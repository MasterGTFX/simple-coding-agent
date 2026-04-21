from langchain_core.messages import SystemMessage, messages_from_dict
import os
import glob
import json
from datetime import datetime

def cmd_new(state, args=None):
    """Clear conversation and start fresh."""
    state["messages"] = [state["messages"][0]]
    state["session_id"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🗑️  Conversation cleared. New session: {state['session_id']}")
    return True


def cmd_model(state, name=None):
    """Switch model. Usage: /model <name>"""
    if not name:
        print(f"Current model: {state['model']}")
        return True
    from langchain_openai import ChatOpenAI
    from tools import ALL_TOOLS
    state["model"] = name
    state["llm"] = ChatOpenAI(model=name).bind_tools(ALL_TOOLS)
    print(f"Switched to {name}")
    return True


def cmd_system(state):
    """Print the current system prompt."""
    print(state["messages"][0].content)
    return True


def cmd_help(state):
    """List available commands."""
    for name, fn in COMMANDS.items():
        print(f"  /{name:10s} {fn.__doc__ or ''}")
    return True


def cmd_exit(state):
    """Exit the agent."""
    raise SystemExit(0)


def cmd_fork(state, args=None):
    """Fork current session into a new one."""
    old_id = state.get("session_id")
    state["session_id"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🍴 Forked session {old_id} into {state['session_id']}")
    return True


def cmd_resume(state, session_id=None):
    """Resume a previous session. Usage: /resume [session_id]"""
    if not os.path.exists(".coding-agent"):
        print("No sessions found.")
        return True
        
    if not session_id:
        sessions = sorted(glob.glob(".coding-agent/*.json"))
        if not sessions:
            print("No sessions found.")
            return True
        print("Available sessions:")
        for s in sessions[-10:]:
            print(f"  {os.path.basename(s).replace('.json', '')}")
        print("Use /resume <session_id> to load one.")
        return True

    path = os.path.join(".coding-agent", f"{session_id}.json")
    if not os.path.exists(path):
        print(f"Session {session_id} not found.")
        return True
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
            state["messages"] = messages_from_dict(data)
            state["session_id"] = session_id
        print(f"✅ Resumed session {session_id} ({len(state['messages'])} messages)")
    except Exception as e:
        print(f"Error loading session: {e}")
    return True


COMMANDS = {
    "new": cmd_new,
    "model": cmd_model,
    "system": cmd_system,
    "help": cmd_help,
    "fork": cmd_fork,
    "resume": cmd_resume,
    "exit": cmd_exit,
}


def handle(user_input: str, state: dict) -> bool:
    """Try to handle as slash command. Returns True if handled."""
    if not user_input.startswith("/"):
        return False
    parts = user_input[1:].split(maxsplit=1)
    cmd, args = parts[0], parts[1] if len(parts) > 1 else None
    if cmd not in COMMANDS:
        print(f"Unknown command: /{cmd}. Type /help for list.")
        return True
    fn = COMMANDS[cmd]
    if args:
        return fn(state, args)
    return fn(state)
