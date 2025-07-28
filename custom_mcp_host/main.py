import json
import os
from fastapi import FastAPI, Request, Response, status

from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, ActivityHandler, TurnContext
from botbuilder.schema import Activity

from mcp_client.mcp_client import MCPClient
from mcp_agent.mcp_agent import MCPAgent
from llm.factory import get_llm_client
from config.settings import LLM_PROVIDER
from shared.query import QueryInput
from shared.context_manager import context_var

CONFIG_PATH = "config/mcp_servers.json"

# --- Global MCPAgent (lazy-loaded) ---
agent: MCPAgent = None


async def get_agent() -> MCPAgent:
    """Initialize MCPAgent on first use (lazy)"""
    global agent
    if agent is None:
        print("Initializing MCPAgent...")
        with open(CONFIG_PATH, "r") as f:
            config_dict = json.load(f)
        clients = {key: await MCPClient.create(cfg) for key, cfg in config_dict.items()}
        llm = get_llm_client(LLM_PROVIDER)
        agent = MCPAgent(llm, clients)
        print("MCPAgent ready!")
    return agent


async def handle_query(query: str) -> str:
    """call MCPAgent and format the reply"""
    ag = await get_agent()
    response = await ag.process_query(query)
    return "\n".join(str(r) for r in response) if isinstance(response, list) else str(response)


# --- FastAPI app ---
app = FastAPI(title="MCP Teams Bot")


# --- Bot Adapter (Teams) ---
APP_ID = os.getenv("MicrosoftAppId", "")
APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")
adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)


# --- Bot Logic ---
class MCPBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        token = context_var.set("teams")
        try:
            reply = await handle_query(turn_context.activity.text)
            await turn_context.send_activity(f"{reply}")
        finally:
            context_var.reset(token)


bot = MCPBot()


# --- Endpoints ---
@app.post("/api/messages")
async def messages(req: Request):
    """Teams Bot Framework endpoint"""
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")
    await adapter.process_activity(activity, auth_header, bot.on_turn)
    return Response(status_code=status.HTTP_200_OK)


@app.post("/simulate/query")
async def simulate_query(req: QueryInput):
    """Directly call MCPAgent"""
    token = context_var.set("swagger")
    try:
        reply = await handle_query(req.query)
        return {"query": req.query, "reply": reply}
    finally:
        context_var.reset(token)


@app.get("/")
def health_check():
    return {"status": "ok"}
