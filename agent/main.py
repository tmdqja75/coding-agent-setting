import base64
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
import redis.asyncio as aioredis

load_dotenv()

# Observability — configure via .env
_langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
_langsmith_key = os.getenv("LANGSMITH_API_KEY")

if _langfuse_secret:
    from langfuse.callback import CallbackHandler as LangfuseCallback
    _obs_callback = LangfuseCallback()
elif _langsmith_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    _obs_callback = None  # LangSmith uses env vars automatically
else:
    _obs_callback = None

from agent.agent import build_graph

_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
ZIP_TTL = 3600  # 1 hour

graph = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, redis_client
    redis_client = aioredis.from_url(_redis_url, decode_responses=False)
    async with AsyncRedisSaver.from_conn_string(
        _redis_url,
        connection_args={
            "health_check_interval": 30,
            "socket_keepalive": True,
            "retry_on_timeout": True,
        },
    ) as checkpointer:
        await checkpointer.asetup()
        graph = build_graph(checkpointer)
        yield
    await redis_client.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    thread_id: str
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    config: dict = {"configurable": {"thread_id": req.thread_id}}
    if _obs_callback:
        config["callbacks"] = [_obs_callback]

    existing = await graph.aget_state(config)
    if existing.values:
        # Continuation: graph is paused at an interrupt — resume with user's answer
        input_state = Command(resume=req.message)
    else:
        # New thread: initialize full state with the first user message
        input_state = {
            "messages": [HumanMessage(content=req.message)],
            "context": {},
            "search_results": {},
            "pending_queries": [],
            "phase": "clarify",
            "next_question": None,
            "zip_bytes": None,
        }

    state = await graph.ainvoke(input_state, config)

    zip_b64 = state.get("zip_bytes")
    if zip_b64:
        zip_bytes = base64.b64decode(zip_b64)
        await redis_client.setex(f"zip:{req.thread_id}", ZIP_TTL, zip_bytes)
        return {"type": "ready", "text": "설정 파일을 생성했습니다."}

    # Graph paused at an interrupt — surface the question to the frontend
    pending = state.get("__interrupt__", [])
    if pending:
        return {"type": "question", "text": pending[0].value}

    return {"type": "ready", "text": "설정을 빌드합니다..."}


@app.get("/download/{thread_id}")
async def download(thread_id: str):
    zip_bytes = await redis_client.get(f"zip:{thread_id}")
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="Zip not found. Try chatting first.")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=claude-code-setup.zip"},
    )
