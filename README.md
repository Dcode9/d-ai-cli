# D'Ai CLI

Agentic coding harness for **D'Ai** — Python-REPL style, no API key required.

```
D'Ai CLI  v0.2.0  · agent harness
Type "help", "exit", or ask anything. Tools work in the current directory.

>>> create a hello.py that prints hi
⚙ write_file {"path": "hello.py", "content": "..."}
Wrote 28 chars to hello.py

Created `hello.py` in the current directory.
```

## Install

```bash
pip install -U d-ai-cli
d-ai
```

## Harness tools (automatic)

| Tool | Purpose |
|------|---------|
| `list_dir` | Explore files |
| `read_file` | Read a file |
| `write_file` | Create / overwrite a file |
| `edit_file` | Surgical string replace |
| `mkdir` | Create directories |
| `run_shell` | Run commands (cwd = project root) |
| `web_search` | Live web search via D-Ai backend |

**All file and shell tools are restricted to the current working directory.**

## Commands

| Command | Action |
|---------|--------|
| `help` | Help |
| `pwd` | Show tool scope (cwd) |
| `tokens [N]` | Max output tokens |
| `reset` | Clear history |
| `clear` | Clear screen |
| `exit` | Quit |

## One-shot

```bash
d-ai "list files and summarize this repo"
```

## How it works

```
You → d-ai CLI → D-Ai backend (reasoning + tool calls)
                      ↓
              local tools on your machine (cwd only)
```

No user API keys. Keys stay on the Vercel backend.

## License

MIT
