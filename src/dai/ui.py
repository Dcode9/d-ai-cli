"""Rich UI helpers for tool calls and status."""

from __future__ import annotations

from typing import Any

from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text

console = Console()


def summarize_args(name: str, args: dict[str, Any]) -> str:
    """Human-friendly one-line summary of tool arguments."""
    if name == "list_dir":
        return str(args.get("path") or ".")
    if name == "read_file":
        return str(args.get("path") or "?")
    if name == "write_file":
        path = str(args.get("path") or "?")
        content = args.get("content") or ""
        n = len(content) if isinstance(content, str) else 0
        return f"{path}  ({n:,} chars)"
    if name == "edit_file":
        path = str(args.get("path") or "?")
        old = str(args.get("old_string") or "")
        preview = (old[:40] + "…") if len(old) > 40 else old
        return f"{path}  replace {preview!r}"
    if name == "mkdir":
        return str(args.get("path") or "?")
    if name == "run_shell":
        cmd = str(args.get("command") or "?")
        if len(cmd) > 72:
            cmd = cmd[:69] + "…"
        return cmd
    if name == "web_search":
        q = str(args.get("query") or "?")
        if len(q) > 72:
            q = q[:69] + "…"
        return q
    # fallback
    raw = str(args)
    return raw if len(raw) <= 80 else raw[:77] + "…"


def summarize_result(name: str, output: str) -> tuple[bool, str]:
    """Return (ok, short status line)."""
    low = (output or "").lower()
    failed = low.startswith("error") or "error:" in low[:80]
    if name == "list_dir":
        if failed:
            return False, output.split("\n", 1)[0][:80]
        lines = [l for l in output.splitlines() if l.strip() and l.strip() != "(empty directory)"]
        if output.strip() == "(empty directory)":
            return True, "empty"
        return True, f"{len(lines)} item(s)"
    if name == "read_file":
        if failed:
            return False, output.split("\n", 1)[0][:80]
        return True, f"{len(output):,} chars"
    if name in ("write_file", "edit_file", "mkdir"):
        if failed:
            return False, output.split("\n", 1)[0][:80]
        # Use first line of tool output
        return True, output.split("\n", 1)[0][:100]
    if name == "run_shell":
        if "timed out" in low:
            return False, "timed out"
        code = "?"
        if output.startswith("exit_code="):
            code = output.split("\n", 1)[0].replace("exit_code=", "").strip()
        ok = code in ("0", 0, "0")
        try:
            ok = int(code) == 0
        except Exception:
            ok = code == "0"
        # Detect background servers started then timed out as soft info
        return ok, f"exit {code}"
    if name == "web_search":
        if failed or low.startswith("search error") or low.startswith("search failed"):
            return False, output.split("\n", 1)[0][:80]
        if "no results" in low:
            return True, "no results"
        n = output.count("\n\n")
        return True, f"{max(n, 1)} result block(s)"
    if failed:
        return False, output.split("\n", 1)[0][:80]
    return True, "done"


def print_tool_start(name: str, args: dict[str, Any], index: int) -> None:
    summary = summarize_args(name, args)
    label = Text()
    label.append(f"  {index}. ", style="dim")
    label.append(f"{name}", style="bold cyan")
    label.append("  ")
    label.append(escape(summary), style="dim")
    console.print(label)


def print_tool_end(name: str, output: str) -> None:
    ok, summary = summarize_result(name, output)
    mark = Text("     ")
    if ok:
        mark.append("✓ ", style="bold green")
        mark.append(escape(summary), style="dim")
    else:
        mark.append("✗ ", style="bold red")
        mark.append(escape(summary), style="red")
    console.print(mark)


def print_thinking() -> None:
    console.print("  [dim]Thinking…[/]")


def print_divider() -> None:
    console.print("[dim]  ────────────────────────────────────────[/]")


def print_answer_header() -> None:
    console.print()
    console.print("[bold gold1]  Answer[/]")
    console.print("[dim]  ────────────────────────────────────────[/]")
