"""
Talks to the public D-Ai backend on Vercel.
Supports streaming chat and non-streaming tool-calling completions.
"""

from __future__ import annotations

import json
from typing import Any, Generator, List, Dict, Optional

import httpx

API_URL = "https://d-ai-omega.vercel.app/api/chat"
DEFAULT_MAX_TOKENS = 16384

_client = None  # type: Optional[httpx.Client]


def get_client() -> httpx.Client:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(timeout=120.0)
    return _client


def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "User-Agent": "D-Ai-CLI/0.2.2",
        "Accept": "application/json, text/event-stream",
    }


def chat_completion(
    messages,
    tools=None,
    max_tokens=DEFAULT_MAX_TOKENS,
    temperature=0.3,
    provider="inception",
):
    # type: (List[Dict[str, Any]], Optional[List[Dict[str, Any]]], int, float, Optional[str]) -> Dict[str, Any]
    """
    Non-streaming completion. Returns:
      { "content": str|None, "tool_calls": list|None, "raw": dict }
    """
    client = get_client()
    payload = {
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
    }  # type: Dict[str, Any]
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
        raise RuntimeError("Could not reach D-Ai backend: {0}".format(e))

    if resp.status_code != 200:
        if provider:
            payload.pop("provider", None)
            resp = client.post(API_URL, headers=_headers(), json=payload)
        if resp.status_code != 200:
            raise RuntimeError(
                "D-Ai backend returned HTTP {0}: {1}".format(
                    resp.status_code, resp.text[:400]
                )
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
        return {
            "content": data.get("content"),
            "tool_calls": data.get("tool_calls"),
            "raw": data,
        }
    if isinstance(data, str):
        return {"content": data, "tool_calls": None, "raw": data}
    return {"content": json.dumps(data)[:2000], "tool_calls": None, "raw": data}


def chat_stream(
    messages,
    temperature=0.7,
    max_tokens=DEFAULT_MAX_TOKENS,
    provider="inception",
):
    # type: (List[Dict[str, Any]], float, int, Optional[str]) -> Generator[str, None, None]
    """Stream text tokens (no tools)."""
    client = get_client()
    payload = {
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
        "enable_tools": False,
    }  # type: Dict[str, Any]
    if provider:
        payload["provider"] = provider

    def _do_stream(p):
        # type: (Dict[str, Any]) -> Generator[str, None, None]
        with client.stream("POST", API_URL, headers=_headers(), json=p) as resp:
            if resp.status_code != 200:
                body = resp.read().decode("utf-8", errors="replace")[:300]
                raise RuntimeError(
                    "D-Ai backend returned HTTP {0}: {1}".format(
                        resp.status_code, body
                    )
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

    try:
        for chunk in _do_stream(payload):
            yield chunk
    except Exception:
        if provider:
            payload.pop("provider", None)
            for chunk in _do_stream(payload):
                yield chunk
        else:
            raise
