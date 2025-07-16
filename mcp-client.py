import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # self.anthropic = Anthropic()

    async def connect_to_server(self):
        """Connect to an MCP server"""
        server_params = StdioServerParameters(
            command="npx",
            args=["mcp-server-kubernetes"]
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [f'{tool.name}:{tool.description}, inputSchema: {tool.inputSchema}' for tool in tools])


async def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python client.py <path_to_server_script>")
    #     sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server()
        # await client.chat_loop()
    finally:
        # await client.cleanup()
        print("done")

if __name__ == "__main__":
    import sys
    asyncio.run(main())