"""
Integration tests for the Claude Code setup agent using REAL LLM calls.
Tests are based on example conversations from docs/example-queries.md.
"""
import base64
import io
import json
import zipfile
from pathlib import Path
from typing import Iterator

import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

load_dotenv(Path(__file__).parent.parent / ".env")

from agent.agent import build_graph  # noqa: E402

INITIAL_STATE = {
    "messages": [],
    "context": {},
    "search_results": {},
    "pending_queries": [],
    "phase": "clarify",
    "next_question": None,
    "zip_bytes": None,
    "generated_agents": [],
    "settings_json": None,
    "claude_md": None,
}


async def drive_conversation(
    graph,
    config: dict,
    initial_state: dict,
    answers_iter: Iterator[str],
    max_turns: int = 8,
) -> dict:
    """
    Drive a multi-turn conversation through the graph.

    Starts with the initial_state, then for each interrupt (agent question)
    feeds the next answer from answers_iter. Stops when zip_bytes is set
    or max_turns is reached.

    Returns the final state dict with a '_questions_asked' key added.
    """
    questions_asked = []

    # First invocation
    state = await graph.ainvoke(initial_state, config)

    for turn in range(max_turns):
        interrupts = state.get("__interrupt__", [])
        if not interrupts:
            # No interrupt means graph ran to completion
            break

        # Extract the question the agent asked
        question = interrupts[0].value
        questions_asked.append(question)
        print(f"\n[Turn {turn + 1}] Agent asked: {question}")

        # Get the next prepared answer, or a generic fallback
        try:
            answer = next(answers_iter)
        except StopIteration:
            answer = "네, 계속 진행해 주세요."

        print(f"[Turn {turn + 1}] User answered: {answer}")

        # Resume the graph with the answer
        state = await graph.ainvoke(Command(resume=answer), config)

        if state.get("zip_bytes") is not None:
            break

    state["_questions_asked"] = questions_asked
    return state


# ---------------------------------------------------------------------------
# Test 1: Next.js SaaS Dashboard (coding project)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_nextjs_coding_project():
    """Full conversation for a Next.js 15 SaaS dashboard project."""
    graph = build_graph(MemorySaver())
    config = {"configurable": {"thread_id": "integration-nextjs-001"}}

    first_message = (
        "Next.js 15 App Router로 SaaS 대시보드를 만들고 있어요. "
        "TypeScript, Tailwind CSS, Prisma ORM을 씁니다."
    )

    # Prepared answers in order matching the agent's SYSTEM_PROMPT question sequence:
    # 1. Domain detection question → "코딩입니다"
    # 2. Workflow follow-up → main workflows
    # 3. Test/quality tools follow-up → Vitest, ESLint
    # 4. Pain points → type errors before deploy
    answers = iter([
        "코딩입니다",
        "컴포넌트 작성, Prisma 스키마 변경, Vercel 배포가 주요 작업입니다.",
        "Vitest로 단위 테스트, ESLint + Prettier 씁니다.",
        "배포 전 타입 에러가 자주 발생합니다.",
    ])

    initial = {
        **INITIAL_STATE,
        "messages": [HumanMessage(content=first_message)],
    }

    state = await drive_conversation(graph, config, initial, answers, max_turns=6)

    questions = state.get("_questions_asked", [])
    print(f"\n=== test_nextjs_coding_project ===")
    print(f"Questions asked ({len(questions)}):")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    print(f"\nzip_bytes set: {state.get('zip_bytes') is not None}")
    print(f"context: {state.get('context')}")

    # --- Assertions ---
    assert state.get("zip_bytes") is not None, (
        f"zip_bytes should be set but was None. Questions asked: {questions}"
    )

    # Unpack the zip and inspect contents
    raw_zip = base64.b64decode(state["zip_bytes"])
    buf = io.BytesIO(raw_zip)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        print(f"Zip contents: {names}")

        assert "CLAUDE.md" in names, f"CLAUDE.md missing from zip: {names}"
        assert ".mcp.json" in names, f".mcp.json missing from zip: {names}"
        assert ".claude/settings.json" in names, f".claude/settings.json missing from zip: {names}"

        settings_raw = zf.read(".claude/settings.json").decode()
        claude_md_content = zf.read("CLAUDE.md").decode()

        print(f"\nCLAUDE.md (first 500 chars):\n{claude_md_content[:500]}")
        print(f"\nsettings.json:\n{settings_raw}")

        # settings.json must be valid JSON
        settings = json.loads(settings_raw)
        assert isinstance(settings, dict), "settings.json should be a JSON object"


# ---------------------------------------------------------------------------
# Test 2: Market Research Analyst (non-coding)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_market_research_analyst():
    """Full conversation for a market research analyst (non-coding domain)."""
    graph = build_graph(MemorySaver())
    config = {"configurable": {"thread_id": "integration-market-001"}}

    first_message = (
        "시장 조사 업무를 합니다. 경쟁사 분석, 소비자 트렌드 리서치, "
        "보고서 작성이 주요 업무예요."
    )

    # Answers in order:
    # 1. Domain detection → 마케팅/리서치
    # 2. Tool/format follow-up → Notion + PowerPoint
    # 3. Pain points → competitor info gathering
    answers = iter([
        "마케팅/리서치입니다",
        "Notion에 정리하고, PowerPoint로 최종 보고서를 만듭니다.",
        "경쟁사 정보 수집에 시간이 많이 걸립니다.",
    ])

    initial = {
        **INITIAL_STATE,
        "messages": [HumanMessage(content=first_message)],
    }

    state = await drive_conversation(graph, config, initial, answers, max_turns=6)

    questions = state.get("_questions_asked", [])
    print(f"\n=== test_market_research_analyst ===")
    print(f"Questions asked ({len(questions)}):")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    print(f"\nzip_bytes set: {state.get('zip_bytes') is not None}")

    context = state.get("context", {})
    print(f"context: {context}")

    # --- Assertions ---
    assert state.get("zip_bytes") is not None, (
        f"zip_bytes should be set but was None. Questions asked: {questions}"
    )

    raw_zip = base64.b64decode(state["zip_bytes"])
    buf = io.BytesIO(raw_zip)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        print(f"Zip contents: {names}")

        assert ".claude/settings.json" in names, f".claude/settings.json missing: {names}"

        settings_raw = zf.read(".claude/settings.json").decode()
        claude_md_content = zf.read("CLAUDE.md").decode()

        print(f"\nCLAUDE.md (first 500 chars):\n{claude_md_content[:500]}")
        print(f"\nsettings.json:\n{settings_raw}")

        settings = json.loads(settings_raw)
        assert isinstance(settings, dict), "settings.json must be valid JSON"


# ---------------------------------------------------------------------------
# Test 3: Go backend with detailed first message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_go_backend_detailed():
    """
    Highly detailed first message (Go backend).
    The agent may skip some questions since enough context is already provided.
    """
    graph = build_graph(MemorySaver())
    config = {"configurable": {"thread_id": "integration-go-detailed-001"}}

    first_message = (
        "Go 백엔드 API 서버입니다. Gin 프레임워크, PostgreSQL, Redis 캐시를 씁니다. "
        "주요 작업은 API 엔드포인트 작성, DB 스키마 마이그레이션(golang-migrate), "
        "Redis 캐시 전략 구현입니다. 테스트는 testify로 하고, Docker Compose로 로컬 개발, "
        "GitHub Actions + GCP Cloud Run으로 배포합니다."
    )

    # Answers for any remaining questions:
    # 1. Domain detection (if asked) → 코딩
    # 2. Pain points follow-up → fast API + DB migration
    # 3. Generic continue if needed
    answers = iter([
        "코딩입니다",
        "빠른 API 응답과 DB 마이그레이션 실수가 주요 과제입니다.",
        "네, 계속 진행해 주세요.",
    ])

    initial = {
        **INITIAL_STATE,
        "messages": [HumanMessage(content=first_message)],
    }

    state = await drive_conversation(graph, config, initial, answers, max_turns=5)

    questions = state.get("_questions_asked", [])
    print(f"\n=== test_go_backend_detailed ===")
    print(f"Questions asked ({len(questions)}):")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    print(f"\nzip_bytes set: {state.get('zip_bytes') is not None}")
    print(f"context: {state.get('context')}")

    # --- Assertions ---
    assert state.get("zip_bytes") is not None, (
        f"zip_bytes should be set but was None. Questions asked: {questions}"
    )

    raw_zip = base64.b64decode(state["zip_bytes"])
    buf = io.BytesIO(raw_zip)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        print(f"Zip contents: {names}")

        assert ".claude/settings.json" in names, f".claude/settings.json missing: {names}"

        settings_raw = zf.read(".claude/settings.json").decode()
        claude_md_content = zf.read("CLAUDE.md").decode()

        print(f"\nCLAUDE.md (first 500 chars):\n{claude_md_content[:500]}")
        print(f"\nsettings.json:\n{settings_raw}")

        settings = json.loads(settings_raw)
        assert isinstance(settings, dict), "settings.json must be valid JSON"
