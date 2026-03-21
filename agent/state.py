from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict                            # extracted project facts (includes domain, pain_points, daily_workflows)
    search_results: dict                     # cached API results keyed by query
    pending_queries: list[str]               # queries waiting to be executed
    phase: str                               # "clarify" | "search"
    next_question: str | None                # question to return to frontend
    zip_bytes: str | None                    # generated zip as base64 string
    generated_agents: list[tuple[str, str]]  # (filename, markdown_content) pairs
    settings_json: str | None                # JSON string for .claude/settings.json
    claude_md: str | None                    # Markdown string for CLAUDE.md
