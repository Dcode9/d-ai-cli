"""
D'Ai CLI — agentic harness in a Python-style REPL.
No API keys required — talks to the public D-Ai backend + local cwd-scoped tools.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from . import __version__
from .agent import run_agent
from .providers import DEFAULT_MAX_TOKENS

console = Console()

BANNER = f"""[bold gold1]D'Ai CLI[/]  [dim]v{__version__}[/]  [dim]· agent harness[/]
Type "help", "exit", or ask anything. Tools work in the current directory.
"""

HELP_TEXT = """
[bold]Commands[/]
  help, ?          Show this help
  tokens [N]       View or change max output tokens
  pwd              Show working directory (tool scope)
  exit, quit, q    Exit the CLI
  clear            Clear the screen
  reset            Clear conversation history

[bold]Harness tools[/] (model can call these automatically)
  list_dir, read_file, write_file, edit_file, mkdir, run_shell, web_search

  All file/shell tools are restricted to the current working directory.

[bold]Usage[/]
  Ask coding questions, request features, or say things like:
    "create a flask app in this folder"
    "fix the failing tests"
    "read main.py and explain it"

[bold]No API key needed[/]
  Uses the public D-Ai backend. Local tools run on your machine.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="D'Ai CLI — agentic coding harness. No API key required.",
        prog="d-ai",
    )
    parser.add_argument(
        "--max-tokens",
        "-m",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum output tokens (default: {DEFAULT_MAX_TOKENS})",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"D'Ai CLI v{__version__}",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Optional prompt to run once (non-interactive)",
    )
    args = parser.parse_args()
    max_tokens = args.max_tokens

    def one_shot(text: str) -> None:
        history: list[dict] = [{"role": "user", "content": text}]
        try:
            with console.status("[dim]Working…[/]", spinner="dots"):
                answer = run_agent(history, max_tokens=max_tokens)
            if answer:
                console.print()
                console.print(Markdown(answer) if "\n" in answer else answer)
                console.print()
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")

    if args.prompt:
        one_shot(" ".join(args.prompt).strip())
        return

    console.print(BANNER)
    history: list[dict] = []

    while True:
        try:
            user_input = console.input("[bold green]>>>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/]")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/]")
            break

        if lower in ("help", "?"):
            console.print(HELP_TEXT)
            continue

        if lower == "clear":
            console.clear()
            console.print(BANNER)
            continue

        if lower == "reset":
            history.clear()
            console.print("[dim]Conversation history cleared.[/]")
            continue

        if lower == "pwd":
            console.print(f"[dim]{Path.cwd().resolve()}[/]")
            continue

        if lower in ("tokens", "/tokens"):
            console.print(f"[dim]Current max output tokens:[/] [bold]{max_tokens:,}[/]")
            continue

        if lower.startswith("tokens ") or lower.startswith("/tokens "):
            parts = user_input.split()
            if len(parts) >= 2 and parts[1].isdigit():
                val = int(parts[1])
                if 256 <= val <= 65536:
                    max_tokens = val
                    console.print(f"[green]Max output tokens set to:[/] [bold]{max_tokens:,}[/]")
                else:
                    console.print("[yellow]Choose between 256 and 65,536.[/]")
            else:
                console.print("[yellow]Usage: tokens <number>[/]")
            continue

        history.append({"role": "user", "content": user_input})

        try:
            with console.status("[dim]Working…[/]", spinner="dots"):
                answer = run_agent(history, max_tokens=max_tokens)

            if not answer:
                console.print("[yellow]Empty response.[/]")
                continue

            console.print()
            if "\n" in answer or any(x in answer for x in ("```", "**", "# ")):
                console.print(Markdown(answer))
            else:
                console.print(answer)
            console.print()

        except RuntimeError as e:
            console.print(f"[red]Error:[/] {e}")
            if history and history[-1].get("role") == "user":
                history.pop()
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted.[/]")
            if history and history[-1].get("role") == "user":
                history.pop()
        except Exception as e:
            console.print(f"[red]Unexpected error:[/] {e}")
            if history and history[-1].get("role") == "user":
                history.pop()


if __name__ == "__main__":
    main()
