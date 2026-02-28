# Claude Code Setup Agent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a LangGraph agent served via FastAPI that conducts a multi-turn conversation with a user, then generates a downloadable zip containing a Claude Code project setup (skills, subagents, `.mcp.json`, `CLAUDE.md`). A new `/setup` page in the existing Next.js frontend drives the conversation UI.

**Architecture:** The FastAPI backend is stateless per-process — LangGraph uses an in-memory checkpointer keyed by `thread_id` (a UUID the frontend generates and holds in React state). The frontend sends one message at a time; the backend returns either a follow-up question or a "ready" signal, then the frontend triggers a zip download.

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, langchain-anthropic, httpx (async HTTP), Next.js 16, React 19, TypeScript, Tailwind CSS v4, Framer Motion.

---

## Task 1: Bootstrap Python Agent Project

**Files:**
- Create: `agent/requirements.txt`
- Create: `agent/.env.example`
- Create: `agent/state.py`

**Step 1: Create the agent directory and requirements.txt**

```
agent/
```

`agent/requirements.txt`:
```
fastapi==0.115.6
uvicorn[standard]==0.32.1
langgraph==0.2.60
langchain-anthropic==0.3.3
langchain-core==0.3.28
httpx==0.28.1
python-dotenv==1.0.1
```

**Step 2: Create `.env.example`**

`agent/.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-...

# Choose one observability provider (leave the other blank)
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

LANGSMITH_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=claude-code-setup-agent
```

**Step 3: Create `agent/state.py`**

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict                  # extracted project facts
    search_results: dict           # cached API results keyed by query
    phase: str                     # "clarify" | "search" | "build"
    next_question: str | None      # question to return to frontend
    zip_bytes: bytes | None        # generated zip, stored for /download
```

**Step 4: Install dependencies**

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install without errors.

**Step 5: Commit**

```bash
git add agent/
git commit -m "feat: bootstrap Python agent project structure"
```

---

## Task 2: Implement Search & Download Tools

**Files:**
- Create: `agent/tools.py`
- Create: `agent/tests/test_tools.py`

**Step 1: Write failing tests**

`agent/tests/test_tools.py`:
```python
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from tools import search_mcp, search_skills, search_plugins, download_file


@pytest.mark.asyncio
async def test_search_mcp_returns_list():
    mock_response = {
        "servers": [{"name": "brave-search", "description": "Web search via Brave"}],
        "metadata": {"count": 1}
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = lambda: mock_response
        mock_get.return_value.raise_for_status = lambda: None
        result = await search_mcp("web search")
    assert isinstance(result, list)
    assert result[0]["name"] == "brave-search"


@pytest.mark.asyncio
async def test_search_skills_returns_list():
    mock_response = {
        "skills": [{"name": "frontend-design", "description": "UI component builder"}],
        "total": 1
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = lambda: mock_response
        mock_get.return_value.raise_for_status = lambda: None
        result = await search_skills("frontend")
    assert isinstance(result, list)
    assert result[0]["name"] == "frontend-design"


@pytest.mark.asyncio
async def test_search_plugins_returns_list():
    mock_response = {
        "plugins": [{"name": "superpowers", "description": "Agent workflow skills"}],
        "total": 1
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = lambda: mock_response
        mock_get.return_value.raise_for_status = lambda: None
        result = await search_plugins("agent")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_download_file_returns_text():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = "# Skill content"
        mock_get.return_value.raise_for_status = lambda: None
        result = await download_file("https://raw.githubusercontent.com/example/skill.md")
    assert result == "# Skill content"
```

**Step 2: Run tests to verify they fail**

```bash
cd agent
source .venv/bin/activate
pip install pytest pytest-asyncio
pytest tests/test_tools.py -v
```

Expected: `ModuleNotFoundError: No module named 'tools'`

**Step 3: Implement `agent/tools.py`**

```python
import httpx
from langchain_core.tools import tool

MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
SKILLS_API = "https://claude-plugins.dev/api/skills"
PLUGINS_API = "https://claude-plugins.dev/api/plugins"


async def search_mcp(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(MCP_REGISTRY, params={"search": query, "limit": limit})
        r.raise_for_status()
        data = r.json()
        return data.get("servers", [])


async def search_skills(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(SKILLS_API, params={"search": query, "limit": limit})
        r.raise_for_status()
        data = r.json()
        return data.get("skills", [])


async def search_plugins(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(PLUGINS_API, params={"search": query, "limit": limit})
        r.raise_for_status()
        data = r.json()
        return data.get("plugins", [])


async def download_file(url: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_tools.py -v
```

Expected: 4 tests PASS.

**Step 5: Commit**

```bash
git add agent/tools.py agent/tests/
git commit -m "feat: implement search and download tools with tests"
```

---

## Task 3: Build the LangGraph Agent Graph

**Files:**
- Create: `agent/agent.py`
- Create: `agent/tests/test_agent.py`

**Step 1: Write failing tests**

`agent/tests/test_agent.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from agent import build_graph


def test_graph_builds_without_error():
    graph = build_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_returns_question_on_first_message():
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-thread-1"}}

    mock_ai_response = MagicMock()
    mock_ai_response.content = '{"action": "ask_question", "question": "어떤 기술 스택을 사용하시나요?"}'

    with patch("agent.llm.ainvoke", new_callable=AsyncMock, return_value=mock_ai_response):
        state = await graph.ainvoke(
            {"messages": [HumanMessage(content="프론트엔드 앱을 만들고 싶어요")],
             "context": {}, "search_results": {}, "phase": "clarify",
             "next_question": None, "zip_bytes": None},
            config=config
        )

    assert state["next_question"] is not None or state["phase"] in ("clarify", "search", "build")
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent'`

**Step 3: Implement `agent/agent.py`**

```python
import json
import io
import zipfile
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from tools import search_mcp, search_skills, search_plugins, download_file

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

SYSTEM_PROMPT = """You are a Claude Code setup assistant. Your job is to recommend and configure the best Claude Code components (MCP servers, skills, subagents) for the user's project.

You will conduct a conversation to understand the user's project. Ask targeted follow-up questions one at a time. Once you have enough information (project type, tech stack, main workflows), stop asking and proceed to search and build.

Always respond with valid JSON in one of these formats:

1. To ask a follow-up question:
{"action": "ask_question", "question": "<your question in Korean>"}

2. To search the registries:
{"action": "search_apis", "queries": ["<query1>", "<query2>"]}

3. To build the zip (when you have enough context):
{"action": "build_zip"}

Keep questions concise and in Korean. Maximum 3 follow-up questions before building."""


async def decide_node(state: AgentState) -> AgentState:
    response = await llm.ainvoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    )

    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        parsed = {"action": "ask_question", "question": "프로젝트에 대해 더 알려주세요."}

    action = parsed.get("action", "ask_question")

    if action == "ask_question":
        return {**state, "next_question": parsed.get("question"), "phase": "clarify"}
    elif action == "search_apis":
        queries = parsed.get("queries", [])
        return {**state, "phase": "search", "_pending_queries": queries, "next_question": None}
    elif action == "build_zip":
        return {**state, "phase": "build", "next_question": None}

    return {**state, "next_question": parsed.get("question", "더 알려주세요."), "phase": "clarify"}


async def search_node(state: AgentState) -> AgentState:
    queries = state.get("_pending_queries", [])
    results = dict(state.get("search_results", {}))

    async def run_searches(query):
        mcp, skills, plugins = await asyncio.gather(
            search_mcp(query),
            search_skills(query),
            search_plugins(query),
        )
        return {"mcp": mcp, "skills": skills, "plugins": plugins}

    for query in queries:
        results[query] = await run_searches(query)

    return {**state, "search_results": results}


async def build_zip_node(state: AgentState) -> AgentState:
    search_results = state.get("search_results", {})

    # Collect unique items
    mcp_servers = []
    skill_files = []
    agent_files = []

    for query_results in search_results.values():
        mcp_servers.extend(query_results.get("mcp", [])[:3])
        for skill in query_results.get("skills", [])[:2]:
            raw_url = skill.get("metadata", {}).get("rawFileUrl") or skill.get("sourceUrl")
            if raw_url:
                try:
                    content = await download_file(raw_url)
                    skill_files.append((skill["name"], content))
                except Exception:
                    pass
        for plugin in query_results.get("plugins", [])[:1]:
            for agent_name in (plugin.get("metadata", {}).get("agents") or "").split(","):
                agent_name = agent_name.strip()
                if agent_name:
                    agent_files.append((agent_name, f"# {agent_name} subagent\n"))

    # Build .mcp.json
    mcp_config = {"mcpServers": {}}
    for server in mcp_servers:
        name = server.get("name", "unknown")
        packages = server.get("packages", [])
        if packages:
            pkg = packages[0]
            mcp_config["mcpServers"][name] = {
                "command": "npx",
                "args": ["-y", pkg.get("name", name)],
            }

    # Build CLAUDE.md summary
    claude_md_lines = [
        "# Claude Code Setup",
        "",
        "This project was configured by the Claude Code Setup Agent.",
        "",
        "## MCP Servers",
    ]
    for server in mcp_servers:
        claude_md_lines.append(f"- **{server.get('name')}**: {server.get('description', '')}")
    claude_md_lines += ["", "## Skills"]
    for name, _ in skill_files:
        claude_md_lines.append(f"- {name}")
    claude_md_lines += ["", "## Subagents"]
    for name, _ in agent_files:
        claude_md_lines.append(f"- {name}")

    # Pack zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".mcp.json", json.dumps(mcp_config, indent=2, ensure_ascii=False))
        zf.writestr("CLAUDE.md", "\n".join(claude_md_lines))
        for name, content in skill_files:
            safe_name = name.replace("/", "_")
            zf.writestr(f".claude/skills/{safe_name}.md", content)
        for name, content in agent_files:
            safe_name = name.replace("/", "_")
            zf.writestr(f".claude/agents/{safe_name}.md", content)

    return {**state, "zip_bytes": buf.getvalue()}


def route(state: AgentState) -> str:
    phase = state.get("phase", "clarify")
    if phase == "clarify":
        return END
    elif phase == "search":
        return "search"
    elif phase == "build":
        return "build_zip"
    return END


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("decide", decide_node)
    builder.add_node("search", search_node)
    builder.add_node("build_zip", build_zip_node)

    builder.set_entry_point("decide")
    builder.add_conditional_edges("decide", route, {
        "search": "search",
        "build_zip": "build_zip",
        END: END,
    })
    builder.add_edge("search", "decide")
    builder.add_edge("build_zip", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent.py::test_graph_builds_without_error -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: implement LangGraph agent graph with decide/search/build nodes"
```

---

## Task 4: Implement FastAPI Endpoints

**Files:**
- Create: `agent/main.py`
- Create: `agent/tests/test_main.py`

**Step 1: Write failing tests**

`agent/tests/test_main.py`:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_question():
    mock_state = {
        "messages": [], "context": {}, "search_results": {},
        "phase": "clarify", "next_question": "어떤 기술 스택을 쓰시나요?",
        "zip_bytes": None
    }
    with patch("main.graph.ainvoke", new_callable=AsyncMock, return_value=mock_state):
        response = client.post("/chat", json={
            "thread_id": "test-123",
            "message": "프론트엔드 앱을 만들고 싶어요"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "question"
    assert "text" in data


def test_chat_returns_ready_when_building():
    mock_state = {
        "messages": [], "context": {}, "search_results": {},
        "phase": "build", "next_question": None,
        "zip_bytes": b"PK fake zip"
    }
    with patch("main.graph.ainvoke", new_callable=AsyncMock, return_value=mock_state):
        response = client.post("/chat", json={
            "thread_id": "test-456",
            "message": "React와 TypeScript를 씁니다"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "ready"


def test_download_returns_zip():
    from main import zip_store
    zip_store["dl-thread-1"] = b"PK fake zip bytes"
    response = client.get("/download/dl-thread-1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


def test_download_missing_thread_returns_404():
    response = client.get("/download/nonexistent-thread")
    assert response.status_code == 404
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

**Step 3: Implement `agent/main.py`**

```python
import os
from contextlib import asynccontextmanager
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

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
        {"messages": [HumanMessage(content=req.message)],
         "context": {}, "search_results": {}, "phase": "clarify",
         "next_question": None, "zip_bytes": None},
        config=config,
    )

    zip_bytes = state.get("zip_bytes")
    if zip_bytes:
        zip_store[req.thread_id] = zip_bytes
        return {"type": "ready", "text": "설정 파일을 생성 중입니다..."}

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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_main.py -v
```

Expected: 5 tests PASS.

**Step 5: Start server manually to verify**

```bash
uvicorn main:app --reload --port 8000
# In another terminal:
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

**Step 6: Commit**

```bash
git add agent/main.py agent/tests/test_main.py
git commit -m "feat: implement FastAPI /chat and /download endpoints"
```

---

## Task 5: Add Observability

**Files:**
- Modify: `agent/main.py`

**Step 1: Install observability packages**

```bash
pip install langfuse langsmith
pip freeze | grep -E "langfuse|langsmith" >> requirements.txt
```

**Step 2: Add observability setup to top of `main.py` (after `load_dotenv()`)**

Add these lines right after `load_dotenv()`:

```python
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
```

**Step 3: Pass callback to graph invocations**

In the `chat` endpoint, update the `graph.ainvoke` call:

```python
    invoke_config = {"configurable": {"thread_id": req.thread_id}}
    if _obs_callback:
        invoke_config["callbacks"] = [_obs_callback]

    state = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)],
         "context": {}, "search_results": {}, "phase": "clarify",
         "next_question": None, "zip_bytes": None},
        config=invoke_config,
    )
```

**Step 4: Commit**

```bash
git add agent/main.py agent/requirements.txt
git commit -m "feat: add optional Langfuse/Langsmith observability"
```

---

## Task 6: Build Frontend `/setup` Page Component

**Files:**
- Create: `components/ui/setup-flow.tsx`
- Create: `app/setup/page.tsx`

**Step 1: Create `components/ui/setup-flow.tsx`**

```tsx
"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";

const API_BASE = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://localhost:8000";

type Status = "idle" | "loading" | "questioning" | "building" | "done" | "error";

interface QAPair {
  question: string;
  answer: string;
}

export function SetupFlow() {
  const [threadId] = useState(() => crypto.randomUUID());
  const [status, setStatus] = useState<Status>("idle");
  const [pairs, setPairs] = useState<QAPair[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (message: string) => {
    setStatus("loading");
    setInput("");

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, message }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data: { type: "question" | "ready"; text: string } = await res.json();

      if (data.type === "question") {
        if (currentQuestion) {
          setPairs((prev) => [...prev, { question: currentQuestion, answer: message }]);
        }
        setCurrentQuestion(data.text);
        setStatus("questioning");
      } else {
        if (currentQuestion) {
          setPairs((prev) => [...prev, { question: currentQuestion, answer: message }]);
        }
        setCurrentQuestion(null);
        setStatus("building");
        triggerDownload();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "오류가 발생했습니다.");
      setStatus("error");
    }
  };

  const triggerDownload = async () => {
    try {
      const res = await fetch(`${API_BASE}/download/${threadId}`);
      if (!res.ok) throw new Error("다운로드 준비 중 오류가 발생했습니다.");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
      setStatus("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "다운로드 오류");
      setStatus("error");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || status === "loading") return;
    sendMessage(input.trim());
  };

  return (
    <div className="mx-auto max-w-2xl px-8 py-16 min-h-screen">
      <h1 className="text-3xl font-bold text-foreground mb-12">
        Claude Code 설정 생성기
      </h1>

      {/* Previous Q&A pairs */}
      <div className="space-y-8 mb-10">
        <AnimatePresence>
          {pairs.map((pair, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-2"
            >
              <p className="text-sm text-muted-foreground">{pair.question}</p>
              <p className="text-base text-muted-foreground/60">{pair.answer}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Active input area */}
      <AnimatePresence mode="wait">
        {(status === "idle" || status === "questioning") && (
          <motion.form
            key="input-form"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <p className="text-lg text-foreground">
              {currentQuestion ?? "만들고 싶은 프로젝트를 입력해세요"}
            </p>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={4}
              className="w-full rounded-2xl border border-muted bg-background px-4 py-3 text-base text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground resize-none"
              placeholder="여기에 입력하세요..."
              autoFocus
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!input.trim()}
                className="rounded-2xl bg-foreground px-6 py-3 text-sm font-semibold text-background transition-opacity disabled:opacity-40"
              >
                {status === "idle" ? "시작하기 →" : "답변하기 →"}
              </button>
            </div>
          </motion.form>
        )}

        {status === "loading" && (
          <motion.p
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-muted-foreground"
          >
            ...
          </motion.p>
        )}

        {status === "building" && (
          <motion.p
            key="building"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-foreground"
          >
            ⟳ 설정 파일을 생성 중입니다...
          </motion.p>
        )}

        {status === "done" && downloadUrl && (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <p className="text-foreground font-semibold">✓ 설정이 완료되었습니다!</p>
            <a
              href={downloadUrl}
              download="claude-code-setup.zip"
              className="inline-block rounded-2xl bg-foreground px-6 py-3 text-sm font-semibold text-background"
            >
              claude-code-setup.zip 다운로드 ↓
            </a>
          </motion.div>
        )}

        {status === "error" && (
          <motion.p
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-red-500"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Step 2: Create `app/setup/page.tsx`**

```tsx
import { SetupFlow } from "@/components/ui/setup-flow";

export default function SetupPage() {
  return <SetupFlow />;
}
```

**Step 3: Add `NEXT_PUBLIC_AGENT_API_URL` to `.env.local`**

```
NEXT_PUBLIC_AGENT_API_URL=http://localhost:8000
```

**Step 4: Verify the page renders**

```bash
npm run dev
# Open http://localhost:3000/setup
```

Expected: Page loads showing "만들고 싶은 프로젝트를 입력해세요" with a textarea.

**Step 5: Commit**

```bash
git add components/ui/setup-flow.tsx app/setup/page.tsx .env.local
git commit -m "feat: add /setup page with sequential Q&A UI"
```

---

## Task 7: Wire Landing Page Button to `/setup`

**Files:**
- Modify: `app/page.tsx:13-14`

**Step 1: Update the secondary button handler in `app/page.tsx`**

Change:
```tsx
  const handleSecondaryClick = () => {
    router.push("/claude-code-components");
  };
```

To:
```tsx
  const handleSecondaryClick = () => {
    router.push("/setup");
  };
```

**Step 2: Verify button navigates correctly**

```bash
npm run dev
# Click "클로드 코드 세팅하기" on the landing page
```

Expected: Navigates to `/setup`.

**Step 3: Commit**

```bash
git add app/page.tsx
git commit -m "feat: wire landing page button to /setup page"
```

---

## Task 8: End-to-End Smoke Test

**Step 1: Start both servers**

Terminal 1:
```bash
cd agent && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```

Terminal 2:
```bash
npm run dev
```

**Step 2: Run manual smoke test**

1. Open `http://localhost:3000`
2. Click "클로드 코드 세팅하기"
3. Type "프론트엔드 Next.js 앱을 만들고 싶어요" and click "시작하기 →"
4. Verify a follow-up question appears
5. Answer the question and verify either another question or "설정 파일을 생성 중입니다..." appears
6. Verify the zip download triggers and contains `.mcp.json`, `CLAUDE.md`, `.claude/` directory

**Step 3: Verify zip contents**

```bash
unzip -l claude-code-setup.zip
```

Expected output includes:
```
.mcp.json
CLAUDE.md
.claude/skills/...
.claude/agents/...
```

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete Claude Code setup agent - LangGraph + FastAPI + Next.js UI"
```

---

## Environment Setup Reference

```bash
# Backend
cd agent
cp .env.example .env
# Fill in ANTHROPIC_API_KEY
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend
cp .env.local.example .env.local   # or create manually
npm run dev
```

## File Structure Summary

```
coding-agent-setting/
├── app/
│   ├── page.tsx                  ← modified: secondary button → /setup
│   └── setup/
│       └── page.tsx              ← new
├── components/ui/
│   └── setup-flow.tsx            ← new
├── .env.local                    ← new (NEXT_PUBLIC_AGENT_API_URL)
└── docs/plans/
    ├── 2026-02-28-claude-code-setup-agent-design.md
    └── 2026-02-28-claude-code-setup-agent-implementation.md

agent/                            ← new Python project
├── main.py
├── agent.py
├── tools.py
├── state.py
├── requirements.txt
├── .env.example
└── tests/
    ├── test_tools.py
    ├── test_agent.py
    └── test_main.py
```
