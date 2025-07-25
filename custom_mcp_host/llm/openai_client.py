from .base_client import BaseLLMClient
from openai import OpenAI
import json

from config.settings import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from shared.tool import ToolCall, Tool
from shared.llm import LLMResponse, LLMMessage


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        super().__init__()
        self.base_url = LLM_BASE_URL
        self.api_key = LLM_API_KEY
        self.model = LLM_MODEL

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    @staticmethod
    def _formatTools(tools: list[Tool]=[]) -> list[dict]:
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in tools]
        return available_tools 
    
    @staticmethod
    def _extract_tool_calls(message) -> list[ToolCall]:
        """Normalize OpenAI tool_calls into ToolCall objects."""
        tool_calls = []

        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                # Parse arguments safely
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        args=args
                    )
                )
        return tool_calls
    
    
    async def chat(self, messages: str, tools: list[dict]=[]) -> str:

        # response = await self.session.list_tools()
        available_tools = self._formatTools(tools)
        
        # Initial LLM API call
        raw_response = self.client.chat.completions.create(
                model=self.model,
                tools=available_tools,
                messages=messages
            )

        return LLMResponse([
            LLMMessage(
                role=choice.message.role,
                content=choice.message.content,
                tool_calls=self._extract_tool_calls(choice.message)
            )
            for choice in raw_response.choices
        ])