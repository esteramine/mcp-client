import asyncio
import json

from mcp_client.mcp_client import MCPClient
from mcp_agent.mcp_agent import MCPAgent
from llm.factory import get_llm_client
from config.settings import LLM_PROVIDER

CONFIG_PATH = "config/mcp_servers.json"

async def chat_loop(agent: MCPAgent):
        """Run an interactive chat loop"""
        print("\nHost Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await agent.process_query(query)

                if isinstance(response, list):
                    print("\nLLM:".join(str(r) for r in response))
                else:
                    print("\nLLM:" + str(response))

            except Exception as e:
                print(f"\nError: {str(e)}")

async def main():
    try:
      with open(CONFIG_PATH, "r") as f:
        config_dict = json.load(f)
      
      clients = {
          key: await MCPClient.create(cfg)
          for key, cfg in config_dict.items()
      }

      llm = get_llm_client(LLM_PROVIDER)
      agent = MCPAgent(llm, clients)
      await chat_loop(agent)
      
    finally:
      await agent.aclose()


if __name__ == "__main__":
    asyncio.run(main())