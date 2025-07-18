import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from openai import OpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import json

from dotenv import load_dotenv


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm = OpenAI(
            base_url="{{base_url}}",
            api_key="not-needed" 
        )
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
        # print("\nConnected to server with tools:", [f'{tool.name}:{tool.description}, inputSchema: {tool.inputSchema}' for tool in tools])

    async def execute_tool_call(self, tool_name, tool_args):
        result = await self.session.call_tool(tool_name, tool_args)
        print()
        print(result)

    async def process_query(self, query: str) -> str:
        """Process a query using available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]
        
        # Initial LLM API call
        response = self.llm.chat.completions.create(
            model="Llama-3.2-3B-Instruct",
            tools=available_tools,
            messages=messages
        )

        # print(response.choices)

        # Process response and handle tool calls
        final_text = []

        assistant_message_content = []
        
        for choice in response.choices:
            tool_calls = choice.message.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments

                    query = input(f"\nDo you allow this host to use this tool {tool_name}: {tool_args}\n").strip()

                    if query.lower() != 'yes' and query.lower() != 'y':
                        return "Tool action is denied."
                    

                    tool_args_dict = {}
                    
                    if isinstance(tool_args, str):
                        tool_args_dict = json.loads(tool_args)
                    
                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args_dict)
                    text_output = "".join(content.text for content in result.content if hasattr(content, "text"))
                    data = ""
                    try:
                        data = json.loads(text_output)
                        # print(data)  # pretty print
                    except json.JSONDecodeError as e:
                        print("Tool call result output is not valid JSON:", e)

                    
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]\n Execution Result:\n")
                    final_text.append(f"{json.dumps(data, indent=2)}\n")
                    assistant_message_content.append(choice.message.content or "")
                    messages.append({
                        "role": "assistant",
                        "content": "".join(final_text)
                    })
                    # messages.append({
                    #     "role": "user",
                    #     "content": [
                    #         {
                    #             "type": "tool_result",
                    #             "tool_use_id": tool_call.id,
                    #             "content": data
                    #         }
                    #     ]
                    # })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content
                    })
                    # Get next response from LLM
                    response = self.llm.chat.completions.create(
                        model="Llama-3.2-3B-Instruct",
                        messages=messages,
                        tools=available_tools
                    )
                    print(response) # it directly just merge the message??
                    
                    # final_text.append("LLM: "+response.choices[0].message.content)
                    final_text.append("LLM: " + (response.choices[0].message.content or "[No response]"))

        # tools_args = {
        #     "resourceType": "pods",
        #     "namespace": "sre-test"
        # }
        # await self.execute_tool_call("kubectl_get", tools_args)
        return final_text

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                # print("\nLLM: " + response)
                if isinstance(response, list):
                    print("\n" + "\n".join(str(r) for r in response))
                else:
                    print("\n" + str(response))

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python client.py <path_to_server_script>")
    #     sys.exit(1)
    
    client = MCPClient()
    try:
        await client.connect_to_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())