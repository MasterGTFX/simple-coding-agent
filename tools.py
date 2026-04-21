import os
import subprocess
from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """Read contents of a file."""
    return open(path).read()


@tool
def create_file(path: str, content: str) -> str:
    """Create a new file with content. Fails if file exists."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        return f"Error: {path} already exists. Use edit_file to modify it."
    open(path, "w").write(content)
    return f"Created {path}"


def _fuzzy_match(text: str, target: str) -> bool:
    """Match ignoring leading/trailing whitespace per line."""
    return "\n".join(l.strip() for l in text.splitlines()) == "\n".join(l.strip() for l in target.splitlines())


def _apply_edit(content: str, old_text: str, new_text: str) -> str:
    if old_text in content:
        return content.replace(old_text, new_text, 1)
    # fuzzy fallback: try whitespace-normalized matching
    for i in range(len(content)):
        for j in range(i + 1, len(content) + 1):
            if _fuzzy_match(content[i:j], old_text):
                return content[:i] + new_text + content[j:]
    raise ValueError(f"old_text not found in file:\n{old_text[:200]}")


@tool
def edit_file(path: str, edits: list[dict]) -> str:
    """Apply search-replace edits to a file.
    edits: list of {"old_text": "exact text to find", "new_text": "replacement text"}
    Each old_text must be unique in the file. Keep old_text minimal but unique."""
    content = open(path).read()
    for edit in edits:
        content = _apply_edit(content, edit["old_text"], edit["new_text"])
    open(path, "w").write(content)
    return f"Applied {len(edits)} edit(s) to {path}"


@tool
def run_command(command: str) -> str:
    """Run a shell command and return stdout+stderr."""
    r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return (r.stdout + r.stderr).strip()


@tool
def list_files(path: str = ".") -> str:
    """List files in a directory recursively, respects .gitignore."""
    path = path.strip()
    try:
        r = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=path, capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except FileNotFoundError:
        pass
    files = []
    for root, dirs, fnames in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", "__pycache__", "node_modules")]
        files.extend(os.path.join(root, f) for f in fnames)
    return "\n".join(sorted(files))


ALL_TOOLS = [read_file, create_file, edit_file, run_command, list_files]
