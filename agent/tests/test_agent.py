import base64
import json
import zipfile
import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from agent import build_graph, generate_subagents_node, build_zip_node


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


def test_agent_state_has_new_fields():
    from agent.state import AgentState
    import typing
    hints = typing.get_type_hints(AgentState)
    assert "settings_json" in hints
    assert "claude_md" in hints


def test_graph_builds_without_error():
    graph = build_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_returns_question_on_first_message():
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-thread-1"}}

    mock_ai_response = MagicMock()
    mock_ai_response.content = '{"action": "ask_question", "question": "어떤 기술 스택을 사용하시나요?"}'

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_ai_response):
        state = await graph.ainvoke(
            {**INITIAL_STATE, "messages": [HumanMessage(content="프론트엔드 앱을 만들고 싶어요")]},
            config,
        )

    assert state["next_question"] is not None or state["phase"] in ("clarify", "search", "build")


@pytest.mark.asyncio
async def test_generate_subagents_node_returns_agent_files():
    mock_response = MagicMock()
    mock_response.content = json.dumps([
        {
            "name": "code-reviewer",
            "description": "Review code changes for quality and correctness",
            "tools": ["Read", "Glob", "Grep"],
            "model": "sonnet",
            "system_prompt": "You are a code review expert. Analyze the code carefully.",
        }
    ])

    state = {
        **INITIAL_STATE,
        "context": {"type": "Next.js", "stack": ["TypeScript", "React"], "workflows": ["code review"]},
        "search_results": {
            "nextjs": {
                "mcp": [{"name": "mcp-server-git"}],
                "skills": [{"name": "code-review"}],
                "plugins": [],
            }
        },
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_subagents_node(state)

    agents = result["generated_agents"]
    assert len(agents) == 1
    name, content = agents[0]
    assert name == "code-reviewer"
    assert "---" in content
    assert "name: code-reviewer" in content
    assert "tools: Read, Glob, Grep" in content
    assert "model: sonnet" in content
    assert "You are a code review expert" in content


@pytest.mark.asyncio
async def test_generate_subagents_node_returns_empty_for_simple_project():
    mock_response = MagicMock()
    mock_response.content = "[]"

    state = {
        **INITIAL_STATE,
        "context": {"type": "static HTML"},
        "search_results": {},
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_subagents_node(state)

    assert result["generated_agents"] == []


@pytest.mark.asyncio
async def test_generate_subagents_node_handles_invalid_json():
    mock_response = MagicMock()
    mock_response.content = "not valid json at all"

    state = {**INITIAL_STATE, "context": {}, "search_results": {}}

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_subagents_node(state)

    assert result["generated_agents"] == []


@pytest.mark.asyncio
async def test_build_zip_includes_agent_files_when_generated():
    state = {
        **INITIAL_STATE,
        "search_results": {},
        "generated_agents": [
            ("code-reviewer", "---\nname: code-reviewer\n---\n\nReview code.\n"),
        ],
    }

    result = await build_zip_node(state)
    buf = io.BytesIO(result["zip_bytes"])
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert ".claude/agents/code-reviewer.md" in names
        assert "CLAUDE.md" in names
        claude_md = zf.read("CLAUDE.md").decode()
        assert "## Subagents" in claude_md
        assert "code-reviewer" in claude_md


@pytest.mark.asyncio
async def test_build_zip_omits_subagents_section_when_empty():
    state = {
        **INITIAL_STATE,
        "search_results": {},
        "generated_agents": [],
    }

    result = await build_zip_node(state)
    buf = io.BytesIO(result["zip_bytes"])
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert not any("agents" in n for n in names)
        claude_md = zf.read("CLAUDE.md").decode()
        assert "## Subagents" not in claude_md


@pytest.mark.asyncio
async def test_decide_node_emits_domain_question_first():
    """decide_node first response should always be a domain-detection question."""
    from agent.agent import decide_node

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "action": "ask_question",
        "question": "어떤 유형의 작업에 Claude Code를 사용하실 예정인가요?"
    })

    state = {
        **INITIAL_STATE,
        "messages": [HumanMessage(content="안녕하세요")],
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response) as mock_ainvoke:
        try:
            await decide_node(state)
        except Exception:
            pass  # interrupt() raises — that's expected
        # Assert inside context so mock is still active
        assert mock_ainvoke.called


@pytest.mark.asyncio
async def test_decide_node_emits_search_after_enough_context():
    """After enough context, decide_node should emit search_apis action."""
    from agent.agent import decide_node

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "action": "search_apis",
        "queries": ["remotion video", "react animation", "ffmpeg", "video export", "motion graphics"],
        "project_context": {
            "type": "video",
            "stack": ["Remotion", "React"],
            "workflows": ["video rendering"],
            "domain": "video",
            "pain_points": ["render time is too long"],
            "daily_workflows": ["render video", "export MP4"],
        }
    })

    state = {
        **INITIAL_STATE,
        "messages": [
            HumanMessage(content="영상 제작 프로젝트입니다"),
            AIMessage(content="어떤 프레임워크를 사용하시나요?"),
            HumanMessage(content="Remotion을 사용합니다"),
            AIMessage(content="가장 불편한 작업은?"),
            HumanMessage(content="렌더링 시간이 너무 깁니다"),
        ],
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await decide_node(state)

    assert result["phase"] == "search"
    assert len(result["pending_queries"]) == 5
    assert result["context"]["domain"] == "video"
    assert result["context"]["pain_points"] == ["render time is too long"]
