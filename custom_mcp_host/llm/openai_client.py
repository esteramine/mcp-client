from .base_client import BaseLLMClient
from openai import OpenAI

from config.settings import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL


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

    async def chat(self, messages, tools: list[dict]=[]) -> str:
        response = self.client.chat.completions.create(
                model=self.model,
                tools=tools,
                messages=messages
            )