# D'Ai CLI

Pure-chat terminal interface for **D'Ai** — the same multi-provider engine used by the web app, now in a Python-REPL-style CLI.

```
D'Ai CLI  v0.1.0
Type "help", "exit", or ask anything.

>>> What is the capital of France?
The capital of France is Paris.

>>>
```

No login. No account. Just set an API key and chat.

---

## Quick install (with Python)

```bash
pip install d-ai
```

Then run:

```bash
d-ai
```

---

## Install options (including no Python)

### 1. pip (recommended if you already have Python)

```bash
pip install d-ai
d-ai
```

### 2. pipx / uv (clean, isolated)

```bash
pipx install d-ai
# or
uv tool install d-ai
d-ai
```

### 3. From this GitHub repo (no PyPI needed)

```bash
pip install git+https://github.com/Dcode9/d-ai-cli.git
d-ai
```

### 4. No Python at all — Windows .exe (coming soon)

We will publish a single `D-Ai.exe` on the [Releases](https://github.com/Dcode9/d-ai-cli/releases) page.  
Download → double-click or put in PATH. Zero dependencies.

### 5. winget / scoop / chocolatey (future)

Once the package is stable we can submit it to:

- **winget** (Windows Package Manager)
- **scoop**
- **Chocolatey**

Then users can do:

```powershell
winget install Dcode9.d-ai
```

---

## How to install Python (if you don’t have it)

### Windows (easiest)

1. Open Microsoft Store → search **Python 3.12** (or 3.13) → Install  
   **or**
2. Go to https://www.python.org/downloads/ → Download → run installer  
   - ✅ Check **“Add python.exe to PATH”**  
   - Click Install

Verify:

```powershell
python --version
pip --version
```

### Alternative one-liner (PowerShell)

```powershell
winget install Python.Python.3.12
```

Then open a **new** terminal and run `pip install d-ai`.

---

## API keys (required for most providers)

Set at least one environment variable:

| Variable            | Free tier?          | Get key at                          |
|---------------------|---------------------|-------------------------------------|
| `GROQ_API_KEY`      | Yes (very generous) | https://console.groq.com            |
| `GEMINI_API_KEY`    | Yes                 | https://aistudio.google.com         |
| `CEREBRAS_API_KEY`  | Yes                 | https://cloud.cerebras.ai           |
| `POLLINATIONS_API`  | Optional            | Free tier works without a key       |

**Windows (PowerShell, current session):**

```powershell
$env:GROQ_API_KEY = "gsk_..."
d-ai
```

**Permanent (user environment):**

```powershell
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", "gsk_...", "User")
```

Or create a file `%USERPROFILE%\.dai\.env`:

```
GROQ_API_KEY=gsk_your_key_here
```

---

## Commands inside the CLI

| Command     | Action                          |
|-------------|---------------------------------|
| `help` / `?`| Show help                       |
| `exit` / `q`| Quit                            |
| `clear`     | Clear the screen                |
| `providers` | List configured providers       |
| `reset`     | Clear conversation history      |

Just type any other text to chat.

---

## Will this CLI create files / folders? (agentic coding)

**Current version (0.1.0) = pure chat only.**  
It does **not** write files or create folders.

We can add that later as an optional “agent mode” that is **restricted to the current working directory** (or a folder you choose). That way it can:

- create / edit files
- make folders
- run limited shell commands

…only inside the project you are working on, never outside it.

If you want this next, just say so and we will add a safe, scoped file-system tool.

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
