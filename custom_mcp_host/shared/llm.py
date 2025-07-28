from typing import List, Optional
from .tool import ToolCall

class LLMMessage:
    def __init__(self, role: str, content: Optional[str], tool_calls: List[ToolCall]):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
    def __str__(self):
        return f"Role: {self.role}, Content: {self.content}, ToolCalls: {self.tool_calls}"


class LLMResponse:
    def __init__(self, messages: List[LLMMessage]):
        self.messages = messages
    def __str__(self):
        return "\n".join(str(m) for m in self.messages)