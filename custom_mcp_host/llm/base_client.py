from abc import ABC, abstractmethod
from shared.tool import ToolCall

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages, tools: list[dict]=[]) -> str:
        pass

    @staticmethod
    def _formatTools(tools: list[dict]=[]) -> list[dict]:
        return tools
    
    @staticmethod
    def _extract_tool_calls(message) -> list[ToolCall]:
        pass