# D'Ai CLI

Pure-chat terminal interface for **D'Ai**.

```
D'Ai CLI  v0.1.2
Type "help", "exit", or ask anything.

>>> What is the capital of France?
The capital of France is Paris.

>>>
```

**No API key. No login. No account.**  
Anyone can install and use it — the CLI talks to the public D-Ai backend (keys stay on the server).

---

## Install

```bash
pip install d-ai-cli
```

Then run:

```bash
d-ai
```

Or pass a question directly:

```bash
d-ai "Explain quantum computing in simple terms"
d-ai --max-tokens 32768
```

### Other ways

```bash
# From GitHub (if not yet on PyPI)
pip install git+https://github.com/Dcode9/d-ai-cli.git

# Isolated install
pipx install d-ai-cli
# or
uv tool install d-ai-cli
```

---

## How to install Python (Windows, if needed)

```powershell
winget install Python.Python.3.12
```

Then open a **new** terminal and run `pip install d-ai-cli`.

Or: Microsoft Store → search "Python 3.12" → Install  
Or: https://www.python.org/downloads/ → check "Add to PATH" → Install

---

## Commands inside the CLI

| Command            | Action                                                |
|--------------------|-------------------------------------------------------|
| `help` / `?`       | Show help                                             |
| `tokens [N]`       | View or set max output tokens (e.g. `tokens 32768`)   |
| `exit` / `q`       | Quit                                                  |
| `clear`            | Clear the screen                                      |
| `reset`            | Clear conversation history                            |

Just type any other text to chat.

---

## How it works

```
Your terminal  →  d-ai CLI  →  https://d-ai-omega.vercel.app/api/chat  →  reply
```

The backend already has the API keys (same ones used by the web app).  
Users never see or set any keys.

---

## Development

```bash
git clone https://github.com/Dcode9/d-ai-cli.git
cd d-ai-cli
pip install -e .
d-ai
```

---

## License

MIT
