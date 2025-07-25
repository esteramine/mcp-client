from mcp_client.mcp_client import MCPClient
from shared.llm import LLMResponse
from shared.tool import Tool, ToolCall
from llm.base_client import BaseLLMClient

class MCPAgent:
    def __init__(self, llm: BaseLLMClient, clients: dict[str, MCPClient]):
        """
        MCPAgent that interacts with an LLM and a MCP client.

        :param llm: The language model used for reasoning and generation.
        :param client: The MCPClient instance that manages environment or tool interactions.
        """
        self.llm = llm
        self.clients = clients

    async def aclose(self):
        """Clean up all managed MCP clients."""
        for key, client in self.clients.items():
            await client.cleanup()

    async def _get_available_tools(self) -> list[Tool]:
        tools = []
        for key, client in self.clients.items():
            client_tools = await client.get_tools()
            for tool in client_tools:
                if isinstance(tool, dict):
                    tool_obj = Tool(
                        server=key,
                        name=tool["name"],
                        description=tool["description"],
                        inputSchema=tool["inputSchema"]
                    )
                else:
                    tool_obj = tool
                tools.append(tool_obj)
        return tools

    
    async def process_query(self, query: str) -> str:
        messages = [{"role": "user", "content": query}]
        
        available_tools = await self._get_available_tools()

        response = await self.llm.chat(messages, available_tools)

        final_text = await self._handle_tool_calls(messages, available_tools, response)

        return "\n".join(final_text)

    async def _handle_tool_calls(self, messages, available_tools, response: LLMResponse):
        final_text = []
        
        for message in response.messages:
            for tool_call in message.tool_calls:
                if not await self._confirm_tool_call(tool_call):
                    return ["Tool action is denied."]

                # Call MCP tool 
                # TODO: Should be self.clients[server_name].execute_tool(tool_call.name, tool_call.arguments) when multiple mcp servers are allowed (server_name dynamically changes)
                # NOTES: now only got "kubernetes" MCP server in this code base and chat completion doesn't support server_label, so the server_name value is hardcoded with "kubernetes" first
                result = await self.clients["kubernetes"].execute_tool(tool_call.name, tool_call.args)
                print(result)

                # Update conversation
                messages.extend([
                    {"role": "assistant", "content": message.content or ""},
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result.content}
                ])

                # Next response
                response = await self.llm.chat(messages, available_tools)
                final_text.append(response.messages[0].content or "")

        return final_text

    async def _confirm_tool_call(self, tool_call: ToolCall) -> bool:
        """Ask user for approval"""
        user_input = input(f"\nDo you allow this host to call tool {tool_call.name} with args {tool_call.args}? (yes/no): ").strip()
        return user_input.lower() in ["yes", "y"]
