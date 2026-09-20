"""
D'Ai CLI — pure chat REPL that looks like the Python interpreter.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from . import __version__
from .providers import available_providers, chat_stream

console = Console()

BANNER = f"""[bold gold1]D'Ai CLI[/]  [dim]v{__version__}[/]
Type "help", "exit", or ask anything.
"""

HELP_TEXT = """
[bold]Commands[/]
  help, ?          Show this help
  exit, quit, q    Exit the CLI
  clear            Clear the screen
  providers        Show which AI providers are configured
  reset            Clear conversation history

[bold]Usage[/]
  Just type your question and press Enter.
  Conversation history is kept for the current session.

[bold]API keys[/]
  Set one or more environment variables:
    GROQ_API_KEY          (recommended — free tier at console.groq.com)
    GEMINI_API_KEY
    CEREBRAS_API_KEY
    POLLINATIONS_API      (optional; free tier works without a key)

  Or put them in a .env file in the current directory / your home folder.
"""


def load_dotenv() -> None:
    """Simple .env loader (no external dependency)."""
    candidates = [
        Path.cwd() / ".env",
        Path.cwd() / ".env.local",
        Path.home() / ".dai" / ".env",
        Path.home() / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
        except Exception:
            pass


def main() -> None:
    load_dotenv()

    console.print(BANNER)

    providers = available_providers()
    if not providers:
        console.print(
            "[yellow]No API keys found.[/] "
            "Set GROQ_API_KEY (free at console.groq.com) or another supported key.\n"
            "You can still type questions — the CLI will tell you if providers fail.\n"
        )
    else:
        console.print(f"[dim]Providers ready: {', '.join(providers)}[/]\n")

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

        if lower == "providers":
            ready = available_providers()
            if ready:
                console.print(f"[green]Ready:[/] {', '.join(ready)}")
            else:
                console.print("[yellow]No providers configured.[/]")
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
                # Collect first token quickly, then stream the rest
                stream = chat_stream(history)
                first = next(stream, None)

            if first is None:
                console.print("[red]Empty response from provider.[/]")
                history.pop()  # remove the failed user turn
                continue

            # Print streaming response
            console.print()  # blank line before answer
            sys.stdout.write(first)
            sys.stdout.flush()
            chunks.append(first)

            for chunk in stream:
                sys.stdout.write(chunk)
                sys.stdout.flush()
                chunks.append(chunk)

            print()  # final newline
            print()

            full_reply = "".join(chunks)
            history.append({"role": "assistant", "content": full_reply})

        except RuntimeError as e:
            console.print(f"[red]Error:[/] {e}")
            history.pop()  # remove the failed user turn
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
