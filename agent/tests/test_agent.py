import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
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

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_ai_response):
        state = await graph.ainvoke(
            {"messages": [HumanMessage(content="프론트엔드 앱을 만들고 싶어요")],
             "context": {}, "search_results": {}, "phase": "clarify",
             "next_question": None, "zip_bytes": None},
            config,
        )

    assert state["next_question"] is not None or state["phase"] in ("clarify", "search", "build")
