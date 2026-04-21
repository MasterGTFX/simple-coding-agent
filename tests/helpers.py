import sys
import types
from dataclasses import dataclass, field


@dataclass
class _BaseMessage:
    content: object = ""
    type: str = "base"
    additional_kwargs: dict = field(default_factory=dict)
    response_metadata: dict = field(default_factory=dict)
    tool_calls: list = field(default_factory=list)


class HumanMessage(_BaseMessage):
    def __init__(self, content):
        super().__init__(content=content, type="human")


class SystemMessage(_BaseMessage):
    def __init__(self, content):
        super().__init__(content=content, type="system")


class ToolMessage(_BaseMessage):
    def __init__(self, content, tool_call_id):
        super().__init__(content=content, type="tool")
        self.tool_call_id = tool_call_id


class AIMessage(_BaseMessage):
    def __init__(self, content="", tool_calls=None, additional_kwargs=None, response_metadata=None):
        super().__init__(
            content=content,
            type="ai",
            tool_calls=tool_calls or [],
            additional_kwargs=additional_kwargs or {},
            response_metadata=response_metadata or {},
        )


class BaseChatModel:
    pass


class FakeTool:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def invoke(self, args):
        if isinstance(args, dict):
            return self.func(**args)
        return self.func(args)


def tool(func):
    return FakeTool(func)


def messages_to_dict(messages):
    data = []
    for msg in messages:
        if isinstance(msg, dict):
            data.append(msg)
            continue
        item = {"type": getattr(msg, "type", "unknown"), "data": {"content": getattr(msg, "content", "")}}
        if getattr(msg, "type", None) == "tool":
            item["data"]["tool_call_id"] = getattr(msg, "tool_call_id", None)
        data.append(item)
    return data


def messages_from_dict(items):
    result = []
    for item in items:
        msg_type = item.get("type")
        content = item.get("data", {}).get("content", "")
        if msg_type == "system":
            result.append(SystemMessage(content))
        elif msg_type == "human":
            result.append(HumanMessage(content))
        elif msg_type == "tool":
            result.append(ToolMessage(content, item.get("data", {}).get("tool_call_id")))
        else:
            result.append(AIMessage(content))
    return result


def install_fake_dependencies():
    fake_messages = types.ModuleType("langchain_core.messages")
    fake_messages.HumanMessage = HumanMessage
    fake_messages.SystemMessage = SystemMessage
    fake_messages.ToolMessage = ToolMessage
    fake_messages.messages_to_dict = messages_to_dict
    fake_messages.messages_from_dict = messages_from_dict

    fake_tools = types.ModuleType("langchain_core.tools")
    fake_tools.tool = tool

    fake_chat_models = types.ModuleType("langchain_core.language_models.chat_models")
    fake_chat_models.BaseChatModel = BaseChatModel

    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    sys.modules["langchain_core"] = types.ModuleType("langchain_core")
    sys.modules["langchain_core.messages"] = fake_messages
    sys.modules["langchain_core.tools"] = fake_tools
    sys.modules["langchain_core.language_models"] = types.ModuleType("langchain_core.language_models")
    sys.modules["langchain_core.language_models.chat_models"] = fake_chat_models
    sys.modules["dotenv"] = fake_dotenv
