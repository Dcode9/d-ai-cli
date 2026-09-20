"""
D'Ai CLI — pure chat REPL that looks like the Python interpreter.
No API keys required — talks to the public D-Ai backend.
"""

from __future__ import annotations

import sys

from rich.console import Console

from . import __version__
from .providers import chat_stream

console = Console()

BANNER = f"""[bold gold1]D'Ai CLI[/]  [dim]v{__version__}[/]
Type "help", "exit", or ask anything.
"""

HELP_TEXT = """
[bold]Commands[/]
  help, ?          Show this help
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

        # Normal chat turn
        history.append({"role": "user", "content": user_input})

        try:
            chunks: list[str] = []
            with console.status("[dim]Thinking…[/]", spinner="dots"):
                stream = chat_stream(history)
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
