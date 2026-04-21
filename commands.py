from langchain_core.messages import messages_from_dict
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


PROVIDERS = ["openai", "anthropic", "google", "openrouter", "ollama"]

def fetch_models(provider: str) -> list:
    """Attempt to dynamically fetch models for the provider."""
    models = []
    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI()
            models = sorted([m.id for m in client.models.list().data if m.id.startswith(("gpt-", "o1-", "o3-"))], reverse=True)
        elif provider == "anthropic":
            from anthropic import Anthropic
            client = Anthropic()
            models = sorted([m.id for m in client.models.list().data if "claude" in m.id], reverse=True)
        elif provider == "google":
            import google.generativeai as genai
            if "GOOGLE_API_KEY" in os.environ:
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                models = sorted([m.name.replace("models/", "") for m in genai.list_models() if "generateContent" in m.supported_generation_methods], reverse=True)
            else:
                print("⚠️ GOOGLE_API_KEY not found in environment.")
        elif provider == "openrouter":
            import urllib.request
            req = urllib.request.Request("https://openrouter.ai/api/v1/models")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = [m["id"] for m in data.get("data", [])]
        elif provider == "ollama":
            import urllib.request
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").replace("/v1", "")
            req = urllib.request.Request(f"{base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode())
                models = [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"⚠️ Could not fetch models for {provider}: {e}")
        
    models.append("custom...")
    return models

def cmd_model(state, name=None):
    """Switch model. Usage: /model [provider/]name (or no args for interactive)"""
    if not name:
        if state.get("model"):
            print(f"Current model: {state['model']}\n")
        providers = PROVIDERS
        print("Providers:")
        for i, p in enumerate(providers, 1):
            print(f"  {i}. {p}")
            
        p_idx = input(f"Select provider (1-{len(providers)}, or enter to cancel): ").strip()
        if not p_idx:
            return True
            
        try:
            provider = providers[int(p_idx) - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return True
            
        print(f"Fetching models for {provider}...")
        models = fetch_models(provider)
        print(f"\nModels for {provider}:")
        for i, m in enumerate(models, 1):
            print(f"  {i}. {m}")
            
        m_idx = input(f"Select model (1-{len(models)}, or enter to cancel): ").strip()
        if not m_idx:
            return True
            
        try:
            model_name = models[int(m_idx) - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return True
            
        if model_name == "custom...":
            model_name = input("Enter custom model name: ").strip()
            if not model_name:
                return True
                
        name = f"{provider}/{model_name}"

    from llm import create_llm
    from tools import ALL_TOOLS
    from config import save_config

    try:
        llm = create_llm(name).bind_tools(ALL_TOOLS)
    except Exception as e:
        print(f"Error switching model: {e}")
        return True

    state["model"] = name
    state["llm"] = llm
    save_config("model", name)
    print(f"Switched to {name} (saved to config)")
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
    """Resume a previous session. Usage: /resume [session_id] (or no args for interactive)"""
    if not os.path.exists(".coding-agent"):
        print("No sessions found.")
        return True
        
    if not session_id:
        sessions = sorted(glob.glob(".coding-agent/*.json"))
        sessions = [s for s in sessions if not s.endswith("config.json")]
        if not sessions:
            print("No sessions found.")
            return True
            
        print("Available sessions:")
        sessions = sessions[-10:]
        for i, s in enumerate(sessions, 1):
            name = os.path.basename(s).replace('.json', '')
            snippet = ""
            try:
                with open(s, "r") as f:
                    data = json.load(f)
                    for msg in data:
                        if msg.get("type") == "human":
                            content = msg.get("data", {}).get("content", "")
                            if isinstance(content, str) and content.strip():
                                content = content.strip().replace('\n', ' ')
                                snippet = f" - {(content[:60] + '...') if len(content) > 60 else content}"
                            break
            except Exception:
                pass
            print(f"  {i}. {name}{snippet}")
            
        choice = input(f"\nSelect session (1-{len(sessions)}, or enter to cancel): ").strip()
        if not choice:
            return True
            
        try:
            # If user typed a number
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                session_id = os.path.basename(sessions[idx]).replace('.json', '')
            else:
                print("Invalid selection.")
                return True
        except ValueError:
            # If user typed a session ID string manually
            session_id = choice

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
