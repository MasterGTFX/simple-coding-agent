# simple-coding-agent

A minimal LLM-powered coding agent in ~100 LOC using LangChain.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .
```

Set your API key:
```bash
set OPENAI_API_KEY=sk-...
```

## Usage

```bash
# interactive
python agent.py

# one-shot
python agent.py "add tests to app.py"
```

## Slash Commands

| Command         | Description                    |
|-----------------|--------------------------------|
| `/new`          | Clear conversation             |
| `/fork`         | Fork into a new session        |
| `/resume [id]`  | List/resume past sessions      |
| `/model <name>` | Switch model (or show current) |
| `/system`       | Print system prompt            |
| `/help`         | List all commands              |
| `/exit`         | Quit                           |

## Tools

- `read_file` — read a file
- `create_file` — create a new file
- `edit_file` — search-replace edits (with fuzzy fallback)
- `run_command` — run a shell command
- `list_files` — list files (respects `.gitignore`)
