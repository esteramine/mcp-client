from typing import List, Optional
from .tool import ToolCall

class LLMMessage:
    def __init__(self, role: str, content: Optional[str], tool_calls: List[ToolCall]):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls


class LLMResponse:
    def __init__(self, messages: List[LLMMessage]):
        self.messages = messages