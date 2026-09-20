"""
Multi-provider cascade matching D-Ai web (api/chat.js).
Pure chat only — no tools in this version.
"""

from __future__ import annotations

import os
from typing import Any, Generator

import httpx

# Same system prompt philosophy as the web app (simplified for pure chat)
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

# Provider configs (mirrors api/chat.js cascade)
PROVIDERS: list[dict[str, Any]] = [
    {
        "name": "groq",
        "env_keys": ["GROQ_API_KEY", "GROQ_API", "GROK_API_KEY", "GROK_API"],
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
        ],
    },
    {
        "name": "gemini",
        "env_keys": ["GEMINI_API_KEY", "API_KEY"],
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "models": ["gemini-2.0-flash", "gemini-1.5-flash"],
    },
    {
        "name": "cerebras",
        "env_keys": ["CEREBRAS_API_KEY"],
        "endpoint": "https://api.cerebras.ai/v1/chat/completions",
        "models": ["llama-3.3-70b"],
    },
    {
        "name": "pollinations",
        "env_keys": ["POLLINATIONS_API", "NEXT_PUBLIC_POLLINATIONS_API"],
        "endpoint": "https://text.pollinations.ai/openai/chat/completions",
        "models": ["openai", "mistral", "openai-fast"],
        "allow_no_key": True,  # free tier works without key
    },
]


def _get_api_key(provider: dict[str, Any]) -> str | None:
    for key in provider["env_keys"]:
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return None


def available_providers() -> list[str]:
    """Return list of providers that have a key (or allow no key)."""
    result = []
    for p in PROVIDERS:
        if _get_api_key(p) or p.get("allow_no_key"):
            result.append(p["name"])
    return result


def chat_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Generator[str, None, None]:
    """
    Stream a response using the same cascade as D-Ai web.
    Yields text chunks. Raises RuntimeError if all providers fail.
    """
    # Build full message list with system prompt
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    last_error: str | None = None

    for provider in PROVIDERS:
        api_key = _get_api_key(provider)
        if not api_key and not provider.get("allow_no_key"):
            continue

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "D-Ai-CLI/0.1.0",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        for model in provider["models"]:
            payload = {
                "model": model,
                "messages": full_messages,
                "stream": True,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            try:
                with httpx.Client(timeout=60.0) as client:
                    with client.stream(
                        "POST",
                        provider["endpoint"],
                        headers=headers,
                        json=payload,
                    ) as resp:
                        if resp.status_code != 200:
                            body = resp.read().decode("utf-8", errors="replace")[:200]
                            last_error = f"{provider['name']}/{model}: HTTP {resp.status_code} — {body}"
                            continue

                        # Stream SSE-style OpenAI format
                        for line in resp.iter_lines():
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data = line[6:].strip()
                                if data == "[DONE]":
                                    return
                                try:
                                    import json

                                    chunk = json.loads(data)
                                    delta = (
                                        chunk.get("choices", [{}])[0]
                                        .get("delta", {})
                                        .get("content")
                                    )
                                    if delta:
                                        yield delta
                                except Exception:
                                    continue
                        return  # successful stream finished

            except Exception as e:
                last_error = f"{provider['name']}/{model}: {e}"
                continue

    raise RuntimeError(
        "All providers failed. "
        "Set at least one of: GROQ_API_KEY, GEMINI_API_KEY, CEREBRAS_API_KEY, or POLLINATIONS_API. "
        f"Last error: {last_error or 'none'}"
    )
