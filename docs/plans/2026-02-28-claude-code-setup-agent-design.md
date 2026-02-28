# Claude Code Setup Agent — Design Doc

**Date:** 2026-02-28

## Overview

A LangGraph-powered agent that takes a user's project description through a multi-turn conversation, then generates a downloadable zip containing a ready-to-use Claude Code project setup (skills, subagents, MCP config).

---

## Architecture

### Communication Flow

```
[Next.js /setup page]
  ├── threadId: UUID (React state, generated once on page load)
  ├── POST /chat   { thread_id, message }  →  { type: "question" | "ready", text }
  └── GET  /download/{thread_id}           →  zip file (binary)

[FastAPI Backend — Python, port 8000]
  ├── POST /chat         → invokes LangGraph, returns next question or "ready"
  └── GET /download/{thread_id} → returns generated zip from in-memory store

[LangGraph — in-memory checkpointer keyed by thread_id]
  └── Stateful per thread across multiple /chat calls
      (no DB — thread lives for the server process lifetime)

[Observability]
  └── Langfuse or Langsmith (configured via env var)
```

### External APIs (no auth required)

| API | Endpoint | Covers |
|---|---|---|
| Official MCP Registry | `registry.modelcontextprotocol.io/v0/servers?search=` | MCP servers (~2,000) |
| claude-plugins.dev Skills | `claude-plugins.dev/api/skills?search=` | Claude Code skills (~52,978) |
| claude-plugins.dev Plugins | `claude-plugins.dev/api/plugins?search=` | Plugins bundling skills/subagents/MCPs |

---

## Backend: LangGraph Agent

### State

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]   # full conversation history
    context: dict                 # extracted project info
    search_results: dict          # cached API results
    phase: str                    # "clarify" | "search" | "build"
    zip_bytes: bytes | None       # generated zip (stored for /download)
```

### Graph

```
[START]
   │
   ▼
decide  ← LLM reads messages + context, chooses:
   │       "ask_question" | "search_apis" | "build_zip"
   │
   ├──► ask_question  → returns { type: "question", text } to API (graph pauses)
   │         └── resumes on next /chat call with user's answer
   │
   ├──► search_apis   → 3 tools run in parallel:
   │         │           search_mcp(keywords)
   │         │           search_skills(keywords)
   │         │           search_plugins(keywords)
   │         └──► decide (loops back)
   │
   └──► build_zip     → download_files → pack_zip
             │           returns { type: "ready", text: "설정 파일을 생성 중입니다..." }
             └──► [END]
```

### Tools

- `search_mcp(query)` — GET `registry.modelcontextprotocol.io/v0/servers?search={query}&limit=10`
- `search_skills(query)` — GET `claude-plugins.dev/api/skills?search={query}&limit=10`
- `search_plugins(query)` — GET `claude-plugins.dev/api/plugins?search={query}&limit=10`
- `download_file(url)` — fetches raw file content (skill SKILL.md, subagent .md)

### Zip Output Structure

```
claude-code-setup.zip
├── .claude/
│   ├── agents/        ← downloaded subagent .md files
│   └── skills/        ← downloaded SKILL.md files
├── .mcp.json          ← generated from MCP search results
└── CLAUDE.md          ← generated summary: what was set up and why
```

### LLM

Model: `claude-sonnet-4-6` via Anthropic SDK (LangChain-Anthropic).

---

## Frontend: `/setup` Page

New page added to existing Next.js site. Accessed via a "시작하기" button on the main landing page (`/`).

### UI Flow

```
1. Initial state
   - Prompt: "만들고 싶은 프로젝트를 입력해세요"
   - Textarea + "시작하기 →" button

2. Questioning state (repeats per agent question)
   - Previous answers shown greyed out above
   - Current agent question shown as plain text
   - Active textarea + "답변하기 →" button

3. Building state
   - "⟳ 설정 파일을 생성 중입니다..."
   - GET /download/{thread_id} called automatically

4. Done state
   - "✓ 설정이 완료되었습니다!"
   - Download button: "claude-code-setup.zip 다운로드 ↓"
```

### UI Rules

- No chat bubbles — sequential plain text layout
- Only one active input at a time
- Previous Q&A pairs greyed out, non-editable
- threadId stored in React state (not persisted, not sent to any auth system)

---

## File Structure

```
coding-agent-setting/          ← existing Next.js repo
├── app/
│   └── setup/
│       └── page.tsx           ← new /setup page
├── components/ui/
│   └── setup-flow.tsx         ← sequential Q&A UI component

agent/                         ← new Python project (sibling or subfolder)
├── main.py                    ← FastAPI app
├── agent.py                   ← LangGraph graph definition
├── tools.py                   ← search + download tools
├── state.py                   ← AgentState TypedDict
├── requirements.txt
└── .env.example               ← ANTHROPIC_API_KEY, LANGFUSE_* or LANGSMITH_*
```

---

## Key Decisions

- **Stateless backend per request is not used** — LangGraph checkpointer holds state per thread_id across `/chat` calls, avoiding resending full history each time.
- **No user auth** — thread_id is a temporary UUID in React state only.
- **Observability** — Langfuse or Langsmith configured via env var, not hardcoded.
- **No auth APIs only** — Official MCP Registry and claude-plugins.dev are both free and require no API key.
