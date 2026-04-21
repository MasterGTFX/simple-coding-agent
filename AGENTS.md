# AGENTS.md

A minimal LLM-powered coding agent using LangChain.

## Structure

- `agent.py` — agent loop, system prompt, session persistence
- `tools.py` — LangChain `@tool` functions (read, create, edit, run, list)
- `commands.py` — slash commands (`/new`, `/model`, `/resume`, etc.)
- `llm.py` — provider/model selection for OpenAI, Anthropic, Google, OpenRouter, Ollama
- `config.py` — persisted config in `.coding-agent/config.json`
- `tests/` — unit tests, generally one test module per source module
- `setup.py` — package setup

## Conventions

- Keep it minimal. Prefer fewer LOC over abstractions.
- Tools return strings. Errors are returned, not raised.
- Slash commands mutate `state` dict directly.
- Persist lightweight user config in `.coding-agent/config.json`.
- Keep tests small and direct; prefer one test file per module when practical.
- System prompt puts dynamic vars at the end for prompt caching.
