"""
Agent harness loop: model ↔ local tools (cwd-scoped).
"""

from __future__ import annotations

import json
from typing import Any, Callable

from rich.console import Console
from rich.markup import escape

from .providers import chat_completion, chat_stream
from .tools import TOOL_SCHEMAS, execute_tool

console = Console()

MAX_TOOL_ROUNDS = 20

AGENT_SYSTEM = """You are D'Ai, an agentic coding intelligence created by Dhairya Shah.

You have local tools that operate ONLY inside the user's current working directory.
Use them to inspect, create, and edit project files and run commands.

HARNESS RULES:
1. Prefer tools over guessing. list_dir / read_file before editing unknown code.
2. write_file for new files; edit_file for precise surgical changes.
3. run_shell for tests, installs, git, builds — keep commands non-interactive.
4. web_search for up-to-date facts, docs, or APIs you are unsure about.
5. Never attempt paths outside the working directory.
6. After finishing tool work, give a clear final answer summarizing what you did.
7. For pure questions with no need for files/commands, answer directly without tools.
8. Generate complete code — no placeholders, no \"// TODO\", no truncated blocks.
"""


def _parse_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return {}
    return {}


def run_agent(
    history: list[dict[str, Any]],
    *,
    max_tokens: int = 16384,
    on_tool: Callable[[str, dict, str], None] | None = None,
) -> str:
    """
    Run the agent loop until a final text answer (no tool_calls).
    Mutates history in place (appends assistant/tool messages).
    Returns the final assistant text.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AGENT_SYSTEM},
        *history,
    ]

    for _round in range(MAX_TOOL_ROUNDS):
        result = chat_completion(
            messages,
            tools=TOOL_SCHEMAS,
            max_tokens=max_tokens,
            temperature=0.3,
        )

        tool_calls = result.get("tool_calls") or []
        content = (result.get("content") or "").strip()

        if not tool_calls:
            if content:
                history.append({"role": "assistant", "content": content})
            return content

        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls,
        }
        history.append(assistant_msg)
        messages.append(assistant_msg)

        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or "unknown"
            args = _parse_args(fn.get("arguments"))
            tool_id = tc.get("id") or f"call_{name}"

            console.print(f"[dim]⚙ {escape(name)}[/] [dim]{escape(json.dumps(args)[:120])}[/]")
            output = execute_tool(name, args)
            if on_tool:
                on_tool(name, args, output)

            if len(output) > 24000:
                output = output[:24000] + "\n…[truncated]"

            tool_msg = {
                "role": "tool",
                "tool_call_id": tool_id,
                "content": output,
            }
            history.append(tool_msg)
            messages.append(tool_msg)

    return "Stopped: reached maximum tool rounds. Ask me to continue if needed."


def run_chat_stream(history: list[dict[str, Any]], *, max_tokens: int = 16384):
    """Simple streaming chat without tools (fallback / pure Q&A path)."""
    messages = [{"role": "system", "content": AGENT_SYSTEM}, *history]
    return chat_stream(messages, max_tokens=max_tokens)
