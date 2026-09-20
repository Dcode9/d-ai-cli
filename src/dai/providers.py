"""
Talks to the public D-Ai backend on Vercel.
Keys stay on the server — users never need an API key.
"""

from __future__ import annotations

import json
from typing import Generator

import httpx

# Your live backend (same one the web app uses)
API_URL = "https://d-ai-omega.vercel.app/api/chat"

SYSTEM_PROMPT = """You are D'Ai, an ornate, profound, and exceptionally rigorous intelligence created by Dhairya Shah.

CORE GUIDELINES:
1. STRICT FACTUAL ACCURACY & ZERO HALLUCINATIONS:
   - When answering questions about current events, live news, real-world facts, benchmarks, technical releases, or products, your response must be 100% truthful and grounded in verified data.
   - Never fabricate model names, version numbers, or unverified claims.

2. VOICE & REGAL PRESENTATION:
   - Eloquent, regal, articulate, and profoundly helpful.
   - Format with elegant Markdown when useful: structured headers, concise bullet points, comparison tables, bold key concepts.

3. BE DIRECT AND USEFUL:
   - Answer the user's question clearly and completely.
   - Prefer clarity over unnecessary flourish.
"""


# Shared persistent client for connection pooling & fast TLS keep-alive
_client: httpx.Client | None = None


def get_client() -> httpx.Client:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(timeout=60.0)
    return _client


def _stream_from_payload(
    client: httpx.Client,
    payload: dict,
    headers: dict[str, str],
) -> Generator[str, None, None]:
    with client.stream(
        "POST",
        API_URL,
        headers=headers,
        json=payload,
    ) as resp:
        if resp.status_code != 200:
            body = resp.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(
                f"D-Ai backend returned HTTP {resp.status_code}: {body}"
            )

        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                data = line[6:].strip()
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if delta:
                        yield delta
                except Exception:
                    if data and not data.startswith("{"):
                        yield data
                    continue


DEFAULT_MAX_TOKENS = 16384


def chat_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    provider: str = "inception",
) -> Generator[str, None, None]:
    """
    Stream a response from the public D-Ai API.
    Routes to Inception (mercury-2.5) first for ultra-fast generation,
    falling back cleanly to the backend's multi-provider cascade if needed.
    """
    client = get_client()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "D-Ai-CLI/0.1.2",
        "Accept": "text/event-stream",
    }

    base_payload = {
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
        "enable_tools": False,  # pure chat for now
    }

    # 1. Attempt ultra-fast Inception primary
    if provider:
        inception_payload = dict(base_payload)
        inception_payload["provider"] = provider
        try:
            yield from _stream_from_payload(client, inception_payload, headers)
            return
        except Exception:
            # Fall back to backend cascade
            pass

    # 2. Seamless fallback to default backend cascade
    try:
        yield from _stream_from_payload(client, base_payload, headers)
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach D-Ai backend: {e}") from e
