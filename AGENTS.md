# AGENTS.md

A minimal LLM-powered coding agent using LangChain.

## Structure

- `agent.py` — agent loop, system prompt, state management
- `tools.py` — LangChain @tool functions (read, create, edit, run, list)
- `commands.py` — slash commands (/new, /model, /help, etc.)
- `setup.py` — package setup

## Conventions

- Keep it minimal. Prefer fewer LOC over abstractions.
- Tools return strings. Errors are returned, not raised.
- Slash commands mutate `state` dict directly.
- System prompt puts dynamic vars at the end for prompt caching.
