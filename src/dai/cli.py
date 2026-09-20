"""
D'Ai CLI — pure chat REPL that looks like the Python interpreter.
No API keys required — talks to the public D-Ai backend.
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from . import __version__
from .providers import DEFAULT_MAX_TOKENS, chat_stream

console = Console()

BANNER = f"""[bold gold1]D'Ai CLI[/]  [dim]v{__version__}[/]
Type "help", "exit", or ask anything.
"""

HELP_TEXT = """
[bold]Commands[/]
  help, ?          Show this help
  tokens [N]       View or change max output tokens (e.g. tokens 32768)
  exit, quit, q    Exit the CLI
  clear            Clear the screen
  reset            Clear conversation history

[bold]Usage[/]
  Just type your question and press Enter.
  Conversation history is kept for the current session.

[bold]No API key needed[/]
  This CLI uses the public D-Ai backend.
  You do not need to set any environment variables.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="D'Ai CLI — pure chat terminal interface. No API key required.",
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
        help="Optional prompt to run directly without entering interactive mode",
    )
    args = parser.parse_args()

    max_tokens = args.max_tokens

    # One-shot mode: run prompt directly if provided
    if args.prompt:
        direct_input = " ".join(args.prompt).strip()
        if direct_input:
            try:
                stream = chat_stream([{"role": "user", "content": direct_input}], max_tokens=max_tokens)
                for chunk in stream:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                print()
            except Exception as e:
                console.print(f"[red]Error:[/] {e}")
            return

    console.print(BANNER)

    history: list[dict[str, str]] = []

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

        if lower in ("tokens", "/tokens"):
            console.print(f"[dim]Current max output tokens:[/] [bold]{max_tokens:,}[/]")
            continue

        if lower.startswith("tokens ") or lower.startswith("/tokens ") or lower.startswith("max_tokens "):
            parts = user_input.split()
            if len(parts) >= 2 and parts[1].isdigit():
                val = int(parts[1])
                if 256 <= val <= 65536:
                    max_tokens = val
                    console.print(f"[green]Max output tokens set to:[/] [bold]{max_tokens:,}[/]")
                else:
                    console.print("[yellow]Please choose a token limit between 256 and 65,536.[/]")
            else:
                console.print("[yellow]Usage: tokens <number> (e.g. tokens 32768)[/]")
            continue

        # Normal chat turn
        history.append({"role": "user", "content": user_input})

        try:
            chunks: list[str] = []
            with console.status("[dim]Thinking…[/]", spinner="dots"):
                stream = chat_stream(history, max_tokens=max_tokens)
                first = next(stream, None)

            if first is None:
                console.print("[red]Empty response from D-Ai backend.[/]")
                history.pop()
                continue

            console.print()
            sys.stdout.write(first)
            sys.stdout.flush()
            chunks.append(first)

            for chunk in stream:
                sys.stdout.write(chunk)
                sys.stdout.flush()
                chunks.append(chunk)

            print()
            print()

            full_reply = "".join(chunks)
            history.append({"role": "assistant", "content": full_reply})

        except RuntimeError as e:
            console.print(f"[red]Error:[/] {e}")
            history.pop()
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted.[/]")
            if history and history[-1]["role"] == "user":
                history.pop()
        except Exception as e:
            console.print(f"[red]Unexpected error:[/] {e}")
            if history and history[-1]["role"] == "user":
                history.pop()


if __name__ == "__main__":
    main()
