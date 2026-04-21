import os
import json
import platform
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, messages_to_dict
from tools import ALL_TOOLS
from commands import handle

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

state = {
    "model": "gpt-5.3-codex",
    "llm": ChatOpenAI(model="gpt-5.3-codex").bind_tools(ALL_TOOLS),
    "messages": [SystemMessage(content=SYSTEM)],
    "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
}
tools_map = {t.name: t for t in ALL_TOOLS}

def save_session():
    os.makedirs(".coding-agent", exist_ok=True)
    path = os.path.join(".coding-agent", f"{state['session_id']}.json")
    with open(path, "w") as f:
        json.dump(messages_to_dict(state["messages"]), f, indent=2)

def run(user_input: str):
    if handle(user_input, state):
        save_session()
        return
    state["messages"].append(HumanMessage(content=user_input))
    save_session()
    while True:
        response = state["llm"].invoke(state["messages"])
        state["messages"].append(response)
        save_session()
        if not response.tool_calls:
            text = response.content if isinstance(response.content, str) else \
                next((b["text"] for b in response.content if b["type"] == "text"), "")
            print(f"\n🤖 {text}")
            break
        for tc in response.tool_calls:
            print(f"🔧 {tc['name']}({tc['args']})")
            result = tools_map[tc["name"]].invoke(tc["args"])
            print(f"   → {result[:200]}{'...' if len(str(result)) > 200 else ''}")
            state["messages"].append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})


def main():
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
