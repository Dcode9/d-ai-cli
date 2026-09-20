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


def chat_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Generator[str, None, None]:
    """
    Stream a response from the public D-Ai API.
    Yields text chunks. Raises RuntimeError on failure.
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    payload = {
        "messages": full_messages,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "enable_tools": False,  # pure chat for now
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "D-Ai-CLI/0.1.0",
        "Accept": "text/event-stream",
    }

    try:
        with httpx.Client(timeout=90.0) as client:
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

    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach D-Ai backend: {e}") from e
