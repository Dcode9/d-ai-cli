"""
Talks to the public D-Ai backend on Vercel.
Supports streaming chat and non-streaming tool-calling completions.
"""

from __future__ import annotations

import json
from typing import Any, Generator

import httpx

API_URL = "https://d-ai-omega.vercel.app/api/chat"
DEFAULT_MAX_TOKENS = 16384

_client: httpx.Client | None = None


def get_client() -> httpx.Client:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(timeout=120.0)
    return _client


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "User-Agent": "D-Ai-CLI/0.2.0",
        "Accept": "application/json, text/event-stream",
    }


def chat_completion(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.3,
    provider: str | None = "inception",
) -> dict[str, Any]:
    """
    Non-streaming completion. Returns:
      { "content": str|None, "tool_calls": list|None, "raw": dict }
    """
    client = get_client()
    payload: dict[str, Any] = {
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
        payload["enable_tools"] = True
    else:
        payload["enable_tools"] = False
    if provider:
        payload["provider"] = provider

    try:
        resp = client.post(API_URL, headers=_headers(), json=payload)
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach D-Ai backend: {e}") from e

    if resp.status_code != 200:
        if provider:
            payload.pop("provider", None)
            resp = client.post(API_URL, headers=_headers(), json=payload)
        if resp.status_code != 200:
            raise RuntimeError(
                f"D-Ai backend returned HTTP {resp.status_code}: {resp.text[:400]}"
            )

    data = resp.json()
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    if message:
        return {
            "content": message.get("content"),
            "tool_calls": message.get("tool_calls"),
            "raw": data,
        }
    if "content" in data:
        return {"content": data.get("content"), "tool_calls": data.get("tool_calls"), "raw": data}
    if isinstance(data, str):
        return {"content": data, "tool_calls": None, "raw": data}
    return {"content": json.dumps(data)[:2000], "tool_calls": None, "raw": data}


def chat_stream(
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.7,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    provider: str | None = "inception",
) -> Generator[str, None, None]:
    """Stream text tokens (no tools)."""
    client = get_client()
    payload: dict[str, Any] = {
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
        "enable_tools": False,
    }
    if provider:
        payload["provider"] = provider

    def _do_stream(p: dict[str, Any]) -> Generator[str, None, None]:
        with client.stream("POST", API_URL, headers=_headers(), json=p) as resp:
            if resp.status_code != 200:
                body = resp.read().decode("utf-8", errors="replace")[:300]
                raise RuntimeError(f"D-Ai backend returned HTTP {resp.status_code}: {body}")
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

    try:
        yield from _do_stream(payload)
    except Exception:
        if provider:
            payload.pop("provider", None)
            yield from _do_stream(payload)
        else:
            raise
