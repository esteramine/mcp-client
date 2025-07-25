import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    # Load environment variables
    load_dotenv()

    # Create configuration dictionary
    config = {
    "mcpServers": {
      "kubernetes": {
          "command": "npx",
          "args": [
              "mcp-server-kubernetes"
          ],
          "env": {
              "SPAWN_MAX_BUFFER": "5242880"
          }
      }
    }
  }

    # Create MCPClient from configuration dictionary
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"), 
        base_url=os.getenv("LLM_BASE_URL"),
      )

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run the query
    result = await agent.run(
        "list all pods under sre-test namespace",
    )
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())