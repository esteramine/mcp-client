from .openai_client import OpenAIClient
# from .anthropic_client import AnthropicClient  # when implemented

def get_llm_client(provider: str):
    if provider == "openai":
        return OpenAIClient()
    # elif provider == "anthropic":
    #     return AnthropicClient()
    else:
        raise ValueError(f"Unsupported provider: {provider}")