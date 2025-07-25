from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages, tools: list[dict]=[]) -> str:
        pass