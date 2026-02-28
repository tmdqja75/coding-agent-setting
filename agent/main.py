import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

load_dotenv()

from agent import build_graph

graph = build_graph()
zip_store: dict[str, bytes] = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    config = {"configurable": {"thread_id": req.thread_id}}

    state = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=req.message)],
            "context": {},
            "search_results": {},
            "phase": "clarify",
            "next_question": None,
            "zip_bytes": None,
        },
        config,
    )

    zip_bytes = state.get("zip_bytes")
    if zip_bytes:
        zip_store[req.thread_id] = zip_bytes
        return {"type": "ready", "text": "설정 파일을 생성했습니다."}

    question = state.get("next_question")
    if question:
        return {"type": "question", "text": question}

    return {"type": "ready", "text": "설정을 빌드합니다..."}


@app.get("/download/{thread_id}")
def download(thread_id: str):
    zip_bytes = zip_store.get(thread_id)
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="Zip not found. Try chatting first.")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=claude-code-setup.zip"},
    )
