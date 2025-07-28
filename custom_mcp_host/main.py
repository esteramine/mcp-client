import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity

from mcp_client.mcp_client import MCPClient
from mcp_agent.mcp_agent import MCPAgent
from llm.factory import get_llm_client
from config.settings import LLM_PROVIDER
from botbuilder.core import ActivityHandler, TurnContext

CONFIG_PATH = "config/mcp_servers.json"

agent: MCPAgent = None


# --- Lifespan handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    # Startup
    with open(CONFIG_PATH, "r") as f:
        config_dict = json.load(f)
    clients = {key: await MCPClient.create(cfg) for key, cfg in config_dict.items()}
    llm = get_llm_client(LLM_PROVIDER)
    agent = MCPAgent(llm, clients)
    print("MCPAgent initialized")

    yield

    # Shutdown
    await agent.aclose()
    print("MCPAgent closed")


# --- FastAPI app ---
app = FastAPI(title="MCP Teams Bot", lifespan=lifespan)


# --- Bot adapter (for Teams) ---
APP_ID = os.getenv("MicrosoftAppId", "")
APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")
adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

async def handle_query(query: str) -> str:
    response = await agent.process_query(query)
    return "\n".join(str(r) for r in response) if isinstance(response, list) else str(response)

# --- Bot logic ---
class MCPBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        query = turn_context.activity.text
        reply = await handle_query(query)
        await turn_context.send_activity(f"{reply}")


bot = MCPBot()


# --- Endpoints ---
@app.post("/api/messages")
async def messages(req: Request):
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")
    await adapter.process_activity(activity, auth_header, bot.on_turn)
    return Response(status_code=status.HTTP_200_OK)

@app.post("/simulate/query")
async def simulate_query(req: Request):
    data = await req.json()
    query = data.get("query")
    reply = await handle_query(query)
    return {"query": query, "reply": reply}

@app.get("/")
def health_check():
    return {"status": "ok"}
