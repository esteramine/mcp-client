
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self, config):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    @classmethod
    async def create(cls, config) -> "MCPClient":
        self = cls(config)
        await self.connect_to_server()
        return self

    async def connect_to_server(self):
        """Connect to an MCP server"""
        # TODO: Add servers which use HTTP Transport
        server_params = StdioServerParameters(
            command=self.config["command"],
            args=self.config["args"]
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        # response = await self.session.list_tools()
        # tools = response.tools
        # print("\nConnected to server with tools:", [f'{tool.name}:{tool.description}, inputSchema: {tool.inputSchema}' for tool in tools])

    async def get_tools(self):
        response = await self.session.list_tools()
        return  response.tools
    
    async def execute_tool(self, tool_name, tool_args):
        result = await self.session.call_tool(tool_name, tool_args)
        return result

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()