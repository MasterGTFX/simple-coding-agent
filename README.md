# simple-coding-agent

A minimal LLM-powered coding agent using LangChain.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .
```

Set your API keys (you can also use a `.env` file):
```bash
set OPENAI_API_KEY=sk-...
set ANTHROPIC_API_KEY=sk-...
set GOOGLE_API_KEY=...
set OPENROUTER_API_KEY=sk-...
```

On the very first run, you will be interactively prompted to pick your provider and model.

You can also bypass this by setting an environment variable:
```bash
set AGENT_MODEL=anthropic/claude-3-5-sonnet-20240620
```

The selected model is saved in `.coding-agent/config.json` and reused on the next run.

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
| `/model <name>` | Switch model (e.g. `anthropic/claude-3-5-sonnet-20240620`, `openrouter/anthropic/claude-3-opus`) |
| `/system`       | Print system prompt            |
| `/help`         | List all commands              |
| `/exit`         | Quit                           |

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests are split by module under `tests/` and use small fake shims so they can run without LangChain provider packages installed.

## Tools

- `read_file` — read a file
- `create_file` — create a new file
- `edit_file` — search-replace edits (with fuzzy fallback)
- `run_command` — run a shell command
- `list_files` — list files (respects `.gitignore`)
