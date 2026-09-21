"""
Local harness tools for D'Ai CLI — scoped strictly to the current working directory.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import httpx

SEARCH_URL = "https://d-ai-omega.vercel.app/api/search"

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories inside the project working directory. Use to explore the codebase before editing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path inside the working directory. Default: '.'",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full text content of a file inside the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content. Creates parent directories if needed. Path must stay inside the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace an exact string occurrence inside a file. Fails if old_string is not found or is ambiguous when replace_all is false.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file."},
                    "old_string": {
                        "type": "string",
                        "description": "Exact text to find.",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "Replacement text.",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "If true, replace every occurrence. Default false.",
                    },
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mkdir",
            "description": "Create a directory (and parents) inside the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path to create.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command with cwd set to the project working directory. Use for tests, builds, git, package managers, etc. Prefer non-interactive commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 60, max 120).",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information, docs, news, or verification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "High-signal search query.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


def _root() -> Path:
    return Path.cwd().resolve()


def resolve_safe(path: str) -> Path:
    """Resolve path and reject anything that escapes the working directory."""
    root = _root()
    raw = Path(path)
    target = (root / raw).resolve() if not raw.is_absolute() else raw.resolve()
    try:
        target.relative_to(root)
    except ValueError as e:
        raise PermissionError(
            f"Path escapes working directory ({root}): {path}"
        ) from e
    return target


def list_dir(path: str = ".") -> str:
    target = resolve_safe(path or ".")
    if not target.exists():
        return f"Error: path does not exist: {path}"
    if not target.is_dir():
        return f"Error: not a directory: {path}"
    entries = []
    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        kind = "dir" if child.is_dir() else "file"
        size = ""
        if child.is_file():
            try:
                size = f" ({child.stat().st_size} bytes)"
            except OSError:
                size = ""
        rel = child.relative_to(_root()).as_posix()
        entries.append(f"{kind:4}  {rel}{size}")
    if not entries:
        return "(empty directory)"
    return "\n".join(entries)


def read_file(path: str) -> str:
    target = resolve_safe(path)
    if not target.exists():
        return f"Error: file not found: {path}"
    if not target.is_file():
        return f"Error: not a file: {path}"
    try:
        data = target.read_bytes()
        if len(data) > 400_000:
            return f"Error: file too large ({len(data)} bytes). Read a smaller file or a subset."
        return data.decode("utf-8", errors="replace")
    except OSError as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    target = resolve_safe(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {target.relative_to(_root()).as_posix()}"
    except OSError as e:
        return f"Error writing file: {e}"


def edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    target = resolve_safe(path)
    if not target.is_file():
        return f"Error: file not found: {path}"
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as e:
        return f"Error reading file: {e}"
    count = text.count(old_string)
    if count == 0:
        return "Error: old_string not found in file."
    if count > 1 and not replace_all:
        return f"Error: old_string found {count} times. Set replace_all=true or provide a more unique string."
    if replace_all:
        updated = text.replace(old_string, new_string)
    else:
        updated = text.replace(old_string, new_string, 1)
    try:
        target.write_text(updated, encoding="utf-8")
    except OSError as e:
        return f"Error writing file: {e}"
    n = count if replace_all else 1
    return f"Edited {target.relative_to(_root()).as_posix()} ({n} replacement(s))"


def mkdir(path: str) -> str:
    target = resolve_safe(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        return f"Directory ready: {target.relative_to(_root()).as_posix()}"
    except OSError as e:
        return f"Error creating directory: {e}"


def run_shell(command: str, timeout: int = 60) -> str:
    root = _root()
    timeout = max(1, min(int(timeout or 60), 120))
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PWD": str(root)},
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        out = out[-12000:] if len(out) > 12000 else out
        return f"exit_code={proc.returncode}\n{out}".rstrip() or f"exit_code={proc.returncode} (no output)"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"


def web_search(query: str) -> str:
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(SEARCH_URL, json={"query": query})
            if resp.status_code != 200:
                return f"Search failed HTTP {resp.status_code}: {resp.text[:300]}"
            data = resp.json()
            parts: list[str] = []
            if data.get("answer"):
                parts.append(f"Answer: {data['answer']}")
            for i, r in enumerate(data.get("results") or [], 1):
                parts.append(
                    f"{i}. {r.get('title', '')}\n   {r.get('url', '')}\n   {r.get('content', '')[:400]}"
                )
            return "\n\n".join(parts) if parts else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def execute_tool(name: str, arguments: dict[str, Any] | str) -> str:
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments.strip() else {}
        except json.JSONDecodeError:
            return f"Error: invalid JSON arguments for {name}"
    args = arguments or {}
    try:
        if name == "list_dir":
            return list_dir(str(args.get("path") or "."))
        if name == "read_file":
            return read_file(str(args["path"]))
        if name == "write_file":
            return write_file(str(args["path"]), str(args.get("content", "")))
        if name == "edit_file":
            return edit_file(
                str(args["path"]),
                str(args.get("old_string", "")),
                str(args.get("new_string", "")),
                bool(args.get("replace_all", False)),
            )
        if name == "mkdir":
            return mkdir(str(args["path"]))
        if name == "run_shell":
            return run_shell(str(args["command"]), int(args.get("timeout") or 60))
        if name == "web_search":
            return web_search(str(args["query"]))
        return f"Error: unknown tool '{name}'"
    except PermissionError as e:
        return f"Error: {e}"
    except KeyError as e:
        return f"Error: missing argument {e} for tool {name}"
    except Exception as e:
        return f"Error in {name}: {e}"
