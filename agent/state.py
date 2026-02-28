from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict                  # extracted project facts
    search_results: dict           # cached API results keyed by query
    pending_queries: list[str]     # queries waiting to be executed
    phase: str                     # "clarify" | "search" | "build"
    next_question: str | None      # question to return to frontend
    zip_bytes: bytes | None        # generated zip, stored for /download
