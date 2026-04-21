import os
import json
import platform
import sys
import time
import threading
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, messages_to_dict
from tools import ALL_TOOLS
from commands import handle
from llm import create_llm
from config import load_config

_agents_md = ""
try:
    _agents_md = "\n\n# Project Guidelines\n" + open("AGENTS.md").read()
except FileNotFoundError:
    pass

SYSTEM = (
    "You are a coding assistant. Use tools to read, write, and run code.\n"
    "Work step by step: understand the task, explore existing code, make changes, verify.\n"
    f"{_agents_md}\n"
    "\n"
    "# Environment\n"
    f"OS: {platform.system()} {platform.release()}\n"
    f"Shell: {'cmd.exe' if platform.system() == 'Windows' else os.environ.get('SHELL', '/bin/sh')}\n"
    f"CWD: {os.getcwd()}\n"
    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
)

config_data = load_config()
configured_model = config_data.get("model", os.environ.get("AGENT_MODEL"))

state = {
    "model": configured_model,
    "llm": None,
    "messages": [SystemMessage(content=SYSTEM)],
    "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
}

if configured_model:
    state["llm"] = create_llm(configured_model).bind_tools(ALL_TOOLS)
tools_map = {t.name: t for t in ALL_TOOLS}

def save_session():
    os.makedirs(".coding-agent", exist_ok=True)
    path = os.path.join(".coding-agent", f"{state['session_id']}.json")
    with open(path, "w") as f:
        json.dump(messages_to_dict(state["messages"]), f, indent=2)

def invoke_with_spinner(llm, messages):
    result = []
    exception = []
    
    def worker():
        try:
            result.append(llm.invoke(messages))
        except Exception as e:
            exception.append(e)

    t = threading.Thread(target=worker)
    t.start()
    
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while t.is_alive():
        sys.stdout.write(f"\r🤖 Thinking {chars[i % len(chars)]} ")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
        
    sys.stdout.write("\r" + " " * 20 + "\r")
    sys.stdout.flush()
    
    if exception:
        raise exception[0]
    return result[0]

def print_ai_message(msg):
    reasoning = ""
    text = ""
    
    # 1. Extract from additional_kwargs (OpenAI O1/O3, DeepSeek, OpenRouter)
    kwargs = getattr(msg, "additional_kwargs", {})
    reasoning = kwargs.get("reasoning") or kwargs.get("reasoning_content") or ""
        
    # 2. Extract from response_metadata (OpenRouter often puts it here)
    if not reasoning:
        metadata = getattr(msg, "response_metadata", {})
        reasoning = metadata.get("reasoning") or metadata.get("reasoning_content") or ""
        
        # OpenRouter-specific nested check
        if not reasoning and "provider_extra" in metadata:
            reasoning = metadata["provider_extra"].get("reasoning")

    # 3. Extract from content blocks (Anthropic Claude 3.7)
    if isinstance(msg.content, list):
        text_parts = []
        for block in msg.content:
            if isinstance(block, dict):
                if block.get("type") == "thinking":
                    reasoning += block.get("thinking", "") + "\n"
                elif block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
        text = "".join(text_parts)
    elif isinstance(msg.content, str):
        text = msg.content
        
    if reasoning and str(reasoning).strip():
        print(f"\x1b[3m\x1b[90m🤔 Reasoning:\n{str(reasoning).strip()}\x1b[0m\n")
        
    if text and str(text).strip():
        print(str(text).strip())

def run(user_input: str):
    if handle(user_input, state):
        save_session()
        return
    state["messages"].append(HumanMessage(content=user_input))
    save_session()
    while True:
        response = invoke_with_spinner(state["llm"], state["messages"])
        state["messages"].append(response)
        save_session()
        if not response.tool_calls:
            print("\n🤖 AI:")
            print_ai_message(response)
            break
        for tc in response.tool_calls:
            print(f"🔧 {tc['name']}({tc['args']})")
            result = tools_map[tc["name"]].invoke(tc["args"])
            result_text = str(result)
            print(f"   → {result_text[:200]}{'...' if len(result_text) > 200 else ''}")
            state["messages"].append(ToolMessage(content=result_text, tool_call_id=tc["id"]))


def main():
    if not state.get("model"):
        print("👋 Welcome! Please select a model to get started.")
        from commands import cmd_model
        while not state.get("model"):
            cmd_model(state)
            if not state.get("model"):
                print("⚠️ You must select a model to continue.")

    import sys
    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        while True:
            try:
                run(input("\n> "))
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    main()
