# Agent Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the LangGraph agent to support non-coding domains (marketing, video, research, etc.), capture pain points in the conversation, and generate richer output artifacts (settings.json, project-specific CLAUDE.md) with improved search relevance via query expansion and LLM re-ranking.

**Architecture:** Domain detection is added as the mandatory first question in `decide_node`; domain + pain_points + daily_workflows are threaded through all generation nodes. Two new nodes (`generate_settings_node`, `generate_claude_md_node`) are inserted between `generate_subagents` and `build_zip` in the graph; `build_zip` is simplified to only package state. A `rerank_results()` helper filters noisy search results inside `search_node`.

**Tech Stack:** Python 3.11+, LangGraph 0.2, LangChain Anthropic, FastAPI, pytest-asyncio, unittest.mock

---

## File Map

| File | What changes |
|---|---|
| `agent/state.py` | Add `settings_json: str \| None` and `claude_md: str \| None` top-level fields |
| `agent/agent.py` | New SYSTEM_PROMPT; remove `build_zip` action from `decide_node`; update `route()`; add `rerank_results()` helper; update `search_node`; update subagent prompts; add `generate_settings_node`, `generate_claude_md_node`; refactor `build_zip_node`; update `build_graph()` |
| `agent/main.py` | Add `settings_json: None`, `claude_md: None` to initial state in `/chat` |
| `agent/tests/test_agent.py` | Update `INITIAL_STATE`; fix base64 handling in zip tests; add tests for all new nodes |

---

## Task 1: Update AgentState schema

**Files:**
- Modify: `agent/state.py`
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

Add to `agent/tests/test_agent.py`:

```python
def test_agent_state_has_new_fields():
    from agent.state import AgentState
    import typing
    hints = typing.get_type_hints(AgentState)
    assert "settings_json" in hints
    assert "claude_md" in hints
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/admin/Documents/one-month-agent-project/2602-claude-code-setup/coding-agent-setting
python -m pytest agent/tests/test_agent.py::test_agent_state_has_new_fields -v
```

Expected: `FAILED` — `AssertionError`

- [ ] **Step 3: Update state.py**

Replace the entire contents of `agent/state.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest agent/tests/test_agent.py::test_agent_state_has_new_fields -v
```

Expected: `PASSED`

- [ ] **Step 5: Update imports and INITIAL_STATE in test_agent.py**

In `agent/tests/test_agent.py`, update the import line at the top of the file to add `AIMessage` and `base64`:

```python
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
```

Then update `INITIAL_STATE` to include the two new fields:

```python
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
```

- [ ] **Step 6: Run all existing tests to make sure nothing is broken**

```bash
python -m pytest agent/tests/test_agent.py -v
```

Expected: `test_agent_state_has_new_fields` passes. `test_graph_builds_without_error` and `test_graph_returns_question_on_first_message` will `ERROR` (they call `build_graph()` without a checkpointer — this is a pre-existing issue fixed in Task 8). All other tests should pass.

- [ ] **Step 7: Commit**

```bash
git add agent/state.py agent/tests/test_agent.py
git commit -m "feat: add settings_json and claude_md fields to AgentState"
```

---

## Task 2: Rewrite SYSTEM_PROMPT and update decide_node

**Files:**
- Modify: `agent/agent.py` (SYSTEM_PROMPT, `decide_node`, `route()`)

The goal: domain-aware 4-question conversation; remove the `action == "build_zip"` shortcut so every run flows through the full pipeline.

- [ ] **Step 1: Write the failing tests**

Add to `agent/tests/test_agent.py`:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest agent/tests/test_agent.py::test_decide_node_emits_domain_question_first agent/tests/test_agent.py::test_decide_node_emits_search_after_enough_context -v
```

Expected: `FAILED` (functions don't exist or wrong behavior)

- [ ] **Step 3: Rewrite SYSTEM_PROMPT and update decide_node in agent.py**

Replace `SYSTEM_PROMPT` (lines 19-34) in `agent/agent.py`:

```python
SYSTEM_PROMPT = """You are a Claude Code setup assistant. Configure the best Claude Code components for the user's project.

Conduct a conversation in Korean following this EXACT sequence:

STEP 1 — Domain detection (always the very first question):
Ask: "어떤 유형의 작업에 Claude Code를 사용하실 예정인가요? (코딩 / 마케팅 / 영상 제작 / 리서치 / 혼합 / 기타)"

STEP 2 — Domain-specific follow-up (ask 1-2 questions based on domain):
- coding: (1) tech stack, (2) CI/CD and deployment target
- marketing: (1) content types and target platforms, (2) research tools used
- video production: (1) framework (Remotion/FFmpeg/other) and output format, (2) asset pipeline
- research: (1) data sources and output format, (2) collaboration tools
- mixed: (1) brief description of each area covered
- others: ask "어떤 작업을 하고 계신지 설명해 주세요." then infer from response

STEP 3 — Pain points (always the last question):
Ask: "가장 시간이 많이 걸리거나 불편한 작업은 무엇인가요?"

STEP 4 — After max 4 questions, emit search_apis with 5-6 targeted queries derived from
the full context including domain, pain points, and workflows.

Always respond with valid JSON in one of these formats:

1. To ask a follow-up question:
{"action": "ask_question", "question": "<question in Korean>"}

2. To search (after gathering enough context — always at most 4 questions):
{"action": "search_apis", "queries": ["<specific query 1>", ..., "<specific query 6>"], "project_context": {"type": "<type>", "stack": ["<tech>"], "workflows": ["<workflow>"], "domain": "<domain>", "pain_points": ["<pain>"], "daily_workflows": ["<workflow>"]}}

Keep questions concise and in Korean. Maximum 4 questions total before emitting search_apis."""
```

In `decide_node`, remove the `if action == "build_zip"` block (lines 66-71). The updated `decide_node` should only handle `search_apis` and `ask_question`:

```python
async def decide_node(state: AgentState) -> dict:
    working_messages = list(state["messages"])
    new_messages: list = []

    while True:
        try:
            response = await llm.ainvoke(
                [SystemMessage(content=SYSTEM_PROMPT)] + working_messages
            )
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            parsed = {"action": "ask_question", "question": "프로젝트에 대해 더 알려주세요."}
        except Exception:
            parsed = {"action": "ask_question", "question": "일시적인 오류가 발생했습니다. 다시 시도해 주세요."}

        action = parsed.get("action", "ask_question")

        if action == "search_apis":
            return {
                "messages": new_messages,
                "phase": "search",
                "pending_queries": parsed.get("queries", []),
                "context": parsed.get("project_context", {}),
                "next_question": None,
            }

        # ask_question (or unknown): interrupt and wait for user's answer.
        question = parsed.get("question") or "더 알려주세요."
        ai_msg = AIMessage(content=question)
        working_messages.append(ai_msg)
        new_messages.append(ai_msg)

        user_answer = interrupt(question)

        human_msg = HumanMessage(content=user_answer)
        working_messages.append(human_msg)
        new_messages.append(human_msg)
```

Also update `route()` — remove the `"build"` branch:

```python
def route(state: AgentState) -> str:
    phase = state.get("phase", "clarify")
    if phase == "search":
        return "search"
    return END
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest agent/tests/test_agent.py::test_decide_node_emits_domain_question_first agent/tests/test_agent.py::test_decide_node_emits_search_after_enough_context -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: domain-aware conversation in decide_node, remove build_zip shortcut"
```

---

## Task 3: Add rerank_results() and update search_node

**Files:**
- Modify: `agent/agent.py` (`search_node`, new `rerank_results()`)
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Add to `agent/tests/test_agent.py`:

```python
@pytest.mark.asyncio
async def test_rerank_results_filters_irrelevant():
    from agent.agent import rerank_results

    search_results = {
        "remotion video": {
            "mcp": [
                {"name": "mcp-kubernetes", "description": "Kubernetes cluster manager"},
                {"name": "mcp-ffmpeg", "description": "Video processing with ffmpeg"},
            ],
            "skills": [
                {"name": "video-render", "content": "Render videos"},
                {"name": "sql-pro", "content": "SQL queries"},
            ],
            "plugins": [],
        }
    }
    context = {"domain": "video", "stack": ["Remotion"], "pain_points": ["slow renders"]}

    mock_response = MagicMock()
    mock_response.content = json.dumps(["mcp-ffmpeg", "video-render"])

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        filtered = await rerank_results(search_results, context)

    mcp_names = [s["name"] for s in filtered["remotion video"]["mcp"]]
    skill_names = [s["name"] for s in filtered["remotion video"]["skills"]]
    assert "mcp-ffmpeg" in mcp_names
    assert "mcp-kubernetes" not in mcp_names
    assert "video-render" in skill_names
    assert "sql-pro" not in skill_names


@pytest.mark.asyncio
async def test_rerank_results_empty_input_is_noop():
    from agent.agent import rerank_results

    result = await rerank_results({}, {"domain": "coding"})
    assert result == {}


@pytest.mark.asyncio
async def test_rerank_results_fallback_on_llm_error():
    from agent.agent import rerank_results

    search_results = {
        "q": {"mcp": [{"name": "mcp-git"}], "skills": [], "plugins": []}
    }
    context = {"domain": "coding"}

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, side_effect=Exception("API error")):
        filtered = await rerank_results(search_results, context)

    # Should return original on error
    assert filtered == search_results
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest agent/tests/test_agent.py::test_rerank_results_filters_irrelevant agent/tests/test_agent.py::test_rerank_results_empty_input_is_noop agent/tests/test_agent.py::test_rerank_results_fallback_on_llm_error -v
```

Expected: `FAILED` — `ImportError: cannot import name 'rerank_results'`

- [ ] **Step 3: Add rerank_results() to agent.py and call it in search_node**

Add this function after `_parse_json_response` in `agent/agent.py`:

```python
async def rerank_results(search_results: dict, context: dict) -> dict:
    """Filter search results to keep only those relevant to the project context."""
    if not search_results:
        return search_results

    all_results = []
    for query, r in search_results.items():
        for item in r.get("mcp", []):
            all_results.append({"name": item.get("name", ""), "desc": item.get("description", "")})
        for item in r.get("skills", []):
            all_results.append({"name": item.get("name", ""), "desc": item.get("content", "")[:120]})

    if not all_results:
        return search_results

    rerank_prompt = (
        f"Project context: {json.dumps(context, ensure_ascii=False)}\n\n"
        f"Evaluate these search results and return a JSON array of names to KEEP "
        f"(only those genuinely useful for this project). Drop anything irrelevant.\n\n"
        f"Results:\n{json.dumps(all_results, ensure_ascii=False)}\n\n"
        f"Return ONLY a JSON array of name strings, e.g. [\"name1\", \"name2\"]"
    )

    try:
        response = await llm.ainvoke([HumanMessage(content=rerank_prompt)])
        keep_names = _parse_json_response(response.content)
        keep_set = set(keep_names)
    except Exception:
        return search_results  # fallback: keep everything

    filtered = {}
    for query, r in search_results.items():
        filtered[query] = {
            "mcp": [i for i in r.get("mcp", []) if i.get("name") in keep_set],
            "skills": [i for i in r.get("skills", []) if i.get("name") in keep_set],
            "plugins": r.get("plugins", []),
        }
    return filtered
```

Update `search_node` to call `rerank_results` at the end:

```python
async def search_node(state: AgentState) -> dict:
    queries = state.get("pending_queries", [])
    results = dict(state.get("search_results", {}))
    context = state.get("context", {})

    async def run_searches(query: str) -> dict:
        mcp, skills, plugins = await asyncio.gather(
            search_mcp(query),
            search_skills(query),
            search_plugins(query),
        )
        return {"mcp": mcp, "skills": skills, "plugins": plugins}

    for query in queries:
        results[query] = await run_searches(query)

    filtered = await rerank_results(results, context)
    return {"search_results": filtered}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest agent/tests/test_agent.py::test_rerank_results_filters_irrelevant agent/tests/test_agent.py::test_rerank_results_empty_input_is_noop agent/tests/test_agent.py::test_rerank_results_fallback_on_llm_error -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: add rerank_results() and update search_node with LLM filtering"
```

---

## Task 4: Update generate_subagents_node prompts

**Files:**
- Modify: `agent/agent.py` (`SELECT_SUBAGENTS_PROMPT`, `CUSTOM_SUBAGENTS_PROMPT`, `generate_subagents_node`)
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

Add to `agent/tests/test_agent.py`:

```python
@pytest.mark.asyncio
async def test_generate_subagents_node_uses_domain_context():
    """generate_subagents_node should pass domain/pain_points to LLM prompts."""
    from agent.agent import generate_subagents_node

    # Mock both LLM calls: catalog selection returns [], custom also returns []
    mock_response = MagicMock()
    mock_response.content = "[]"

    state = {
        **INITIAL_STATE,
        "context": {
            "type": "video",
            "domain": "video",
            "stack": ["Remotion"],
            "pain_points": ["slow renders"],
            "daily_workflows": ["render video"],
        },
        "search_results": {},
    }

    call_args_list = []

    async def capturing_ainvoke(messages, **kwargs):
        call_args_list.append(messages)
        return mock_response

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, side_effect=capturing_ainvoke):
        await generate_subagents_node(state)

    # At least one LLM call should contain domain info
    all_content = " ".join(
        m.content for call in call_args_list for m in call if hasattr(m, "content")
    )
    assert "video" in all_content
    assert "slow renders" in all_content or "pain_points" in all_content
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest agent/tests/test_agent.py::test_generate_subagents_node_uses_domain_context -v
```

Expected: `FAILED`

- [ ] **Step 3: Update SELECT_SUBAGENTS_PROMPT, CUSTOM_SUBAGENTS_PROMPT, and user messages**

Replace `SELECT_SUBAGENTS_PROMPT` in `agent/agent.py`:

```python
SELECT_SUBAGENTS_PROMPT = """You are a Claude Code configuration expert. You have access to a curated catalog of 120+ community subagents.

Based on the user's project context, select the most relevant subagents from the catalog below.

## Catalog Index
{catalog_index}

## Instructions
- Select 0-4 subagents that best match the project's domain, tech stack, pain points, and workflows
- Only select subagents that would genuinely help this specific project
- For non-coding domains (marketing, video, research): prefer domain-specific agents over generic coding agents
- If the project is very simple, select fewer or none
- Return a JSON array of selected entries: [{{"name": "...", "category": "..."}}]
- If no catalog subagents are relevant, return: []
"""
```

Replace `CUSTOM_SUBAGENTS_PROMPT` in `agent/agent.py`:

```python
CUSTOM_SUBAGENTS_PROMPT = """You are a Claude Code configuration expert. Some subagents have been selected from a curated catalog. Now decide if additional CUSTOM subagents are needed for workflows not covered by the catalog selections.

Already selected from catalog: {selected_names}

Output a JSON array. If no additional custom subagents are needed, return: []

If custom subagents would fill genuine gaps, return 1-2 definitions:
[
  {{
    "name": "kebab-case-name",
    "description": "Specific trigger description for when Claude should delegate here",
    "tools": ["Read", "Grep", "Glob"],
    "model": "haiku",
    "system_prompt": "Focused system prompt for this agent..."
  }}
]

Rules:
- Only generate custom subagents for workflows NOT covered by catalog selections
- Tailor agents to the actual domain (e.g. video rendering agents for video projects, not kubernetes agents)
- Use the minimum tools needed (principle of least privilege)
- model: "haiku" for fast/cheap lookup tasks, "sonnet" for reasoning tasks, "opus" for complex work
- Available tools: Read, Write, Edit, Bash, Glob, Grep, Agent
- Write the "system_prompt" field in Korean
- system_prompt should be detailed and tailored to the user's project
"""
```

Update the user messages in `generate_subagents_node` to include domain context. Replace the `select_user_msg` and `custom_user_msg` strings:

```python
    select_user_msg = f"""Project context: {json.dumps(context)}

Domain: {context.get('domain', 'unknown')}
Pain points: {context.get('pain_points', [])}
Daily workflows: {context.get('daily_workflows', [])}
Available MCP servers: {found_mcps}
Available skills: {found_skills}
Available plugins: {found_plugins}

Select the most relevant subagents from the catalog for this project."""
```

```python
    custom_user_msg = f"""Project context: {json.dumps(context)}

Domain: {context.get('domain', 'unknown')}
Pain points: {context.get('pain_points', [])}
Daily workflows: {context.get('daily_workflows', [])}
Available MCP servers: {found_mcps}
Available skills: {found_skills}

Generate custom subagents only for gaps not covered by the catalog selections, or return [] if no gaps exist."""
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest agent/tests/test_agent.py::test_generate_subagents_node_uses_domain_context -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full existing test suite**

```bash
python -m pytest agent/tests/test_agent.py -v -k "subagent"
```

Expected: All subagent tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: inject domain/pain_points into subagent selection prompts"
```

---

## Task 5: Add generate_settings_node

**Files:**
- Modify: `agent/agent.py`
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Add to `agent/tests/test_agent.py`:

```python
@pytest.mark.asyncio
async def test_generate_settings_node_coding_domain():
    from agent.agent import generate_settings_node

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "permissions": {"allow": ["Bash(git*)", "Bash(npm*)", "Bash(python*)"]},
        "hooks": {
            "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "npm run lint"}]}]
        },
        "model": "claude-sonnet-4-6"
    })

    state = {
        **INITIAL_STATE,
        "context": {
            "domain": "coding",
            "type": "Next.js",
            "stack": ["TypeScript", "React"],
            "pain_points": ["slow tests"],
            "daily_workflows": ["code review", "deploy"],
        },
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_settings_node(state)

    assert result["settings_json"] is not None
    parsed = json.loads(result["settings_json"])
    assert "permissions" in parsed
    assert "Bash(git*)" in parsed["permissions"]["allow"]
    assert parsed["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_generate_settings_node_others_domain_fallback():
    from agent.agent import generate_settings_node

    mock_response = MagicMock()
    mock_response.content = "not valid json {{"  # simulate LLM failure

    state = {
        **INITIAL_STATE,
        "context": {"domain": "others", "type": "unknown"},
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_settings_node(state)

    # Should fall back to safe defaults
    assert result["settings_json"] is not None
    parsed = json.loads(result["settings_json"])
    assert parsed["permissions"]["allow"] == []
    assert parsed["model"] == "claude-sonnet-4-6"
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest agent/tests/test_agent.py::test_generate_settings_node_coding_domain agent/tests/test_agent.py::test_generate_settings_node_others_domain_fallback -v
```

Expected: `FAILED` — `ImportError`

- [ ] **Step 3: Add GENERATE_SETTINGS_PROMPT and generate_settings_node to agent.py**

Add after `CUSTOM_SUBAGENTS_PROMPT`:

```python
GENERATE_SETTINGS_PROMPT = """You are a Claude Code configuration expert. Generate a .claude/settings.json file for this project.

Project context:
{context}

Generate a JSON object with this exact structure:
{{
  "permissions": {{
    "allow": ["<permission1>", ...]
  }},
  "hooks": {{
    "PostToolUse": [{{ "matcher": "<matcher>", "hooks": [{{ "type": "command", "command": "<cmd>" }}] }}]
  }},
  "model": "<model-id>"
}}

Permission guidelines by domain:
- coding: Bash(git*), Bash(npm*) or Bash(python*) based on stack; add Bash(docker*) if containerized
- video: Bash(npx remotion*), Bash(ffmpeg*), Bash(npm*)
- marketing: WebFetch(*), Bash(curl*)
- research: WebFetch(*), Bash(python*)
- mixed: union of permissions from all relevant domains described
- others: infer from context description; fallback to empty allow list if unclear

Hook guidelines:
- coding: PostToolUse with matcher "Edit|Write" to run detected linter (e.g. "npm run lint", "ruff check .")
- video: PostToolUse to validate render config if applicable
- marketing, research: omit hooks entirely (use empty object {{}})
- others: omit hooks unless clearly applicable from description

Model guidelines:
- research or complex analysis: "claude-opus-4-6"
- coding or video production: "claude-sonnet-4-6"
- marketing or simple content tasks: "claude-haiku-4-5-20251001"

Return ONLY valid JSON, no markdown fences, no explanation."""


_SETTINGS_FALLBACK = json.dumps({
    "permissions": {"allow": []},
    "hooks": {},
    "model": "claude-sonnet-4-6"
}, indent=2)


async def generate_settings_node(state: AgentState) -> dict:
    context = state.get("context", {})
    prompt = GENERATE_SETTINGS_PROMPT.format(context=json.dumps(context, ensure_ascii=False))
    try:
        response = await llm.ainvoke(
            [SystemMessage(content=prompt), HumanMessage(content="Generate the settings.json now.")]
        )
        # Validate it's parseable JSON
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()
        json.loads(raw)  # validate
        return {"settings_json": raw}
    except Exception:
        return {"settings_json": _SETTINGS_FALLBACK}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest agent/tests/test_agent.py::test_generate_settings_node_coding_domain agent/tests/test_agent.py::test_generate_settings_node_others_domain_fallback -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: add generate_settings_node with domain-aware permissions and hooks"
```

---

## Task 6: Add generate_claude_md_node

**Files:**
- Modify: `agent/agent.py`
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Add to `agent/tests/test_agent.py`:

```python
@pytest.mark.asyncio
async def test_generate_claude_md_node_produces_markdown():
    from agent.agent import generate_claude_md_node

    mock_response = MagicMock()
    mock_response.content = """# My Video Project

## Project Overview
A Remotion-based video renderer for marketing content.

## Key Commands
- `npm run render` — render video

## Workflows
When render times are slow, use incremental rendering.

## Configured Components
- MCP: mcp-ffmpeg
- Subagents: remotion-renderer
"""

    state = {
        **INITIAL_STATE,
        "context": {
            "domain": "video",
            "type": "Remotion",
            "stack": ["React"],
            "pain_points": ["slow renders"],
            "daily_workflows": ["render video"],
        },
        "search_results": {
            "remotion": {"mcp": [{"name": "mcp-ffmpeg"}], "skills": [], "plugins": []}
        },
        "generated_agents": [("remotion-renderer", "---\nname: remotion-renderer\n---\n")],
    }

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_claude_md_node(state)

    assert result["claude_md"] is not None
    assert "## Project Overview" in result["claude_md"]
    assert "## Key Commands" in result["claude_md"]


@pytest.mark.asyncio
async def test_generate_claude_md_node_fallback_on_error():
    from agent.agent import generate_claude_md_node

    state = {**INITIAL_STATE, "context": {}, "search_results": {}, "generated_agents": []}

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, side_effect=Exception("API down")):
        result = await generate_claude_md_node(state)

    assert result["claude_md"] is None  # None signals build_zip to use fallback
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest agent/tests/test_agent.py::test_generate_claude_md_node_produces_markdown agent/tests/test_agent.py::test_generate_claude_md_node_fallback_on_error -v
```

Expected: `FAILED` — `ImportError`

- [ ] **Step 3: Add GENERATE_CLAUDE_MD_PROMPT and generate_claude_md_node to agent.py**

Add after `_SETTINGS_FALLBACK`:

```python
GENERATE_CLAUDE_MD_PROMPT = """You are a Claude Code configuration expert. Generate a rich, project-specific CLAUDE.md file.

CLAUDE.md is loaded by Claude Code at the start of every session to understand how to work on this project.

Project context: {context}
MCP servers configured: {mcp_names}
Skills configured: {skill_names}
Subagents configured: {agent_names}

Write a CLAUDE.md with these sections (include only sections that are relevant):

# [Project Name derived from context, or "Claude Code Setup"]

## Project Overview
[2-3 sentences describing the project]

## Key Commands
[Domain-specific commands: build/dev/test for coding; render/export for video; etc. — only if known]

## Workflows
[Practical workflows that address the user's pain points — specific and actionable]

## Configured Components
[Brief description of what each configured MCP server, skill, and subagent does — omit if empty]

## Conventions
[Any constraints or conventions from the user's responses — omit if none]

Write in English. Be specific and practical, not generic. Omit sections that have nothing meaningful to say."""


async def generate_claude_md_node(state: AgentState) -> dict:
    context = state.get("context", {})
    search_results = state.get("search_results", {})
    agent_files = state.get("generated_agents", [])

    mcp_names = []
    skill_names = []
    for r in search_results.values():
        mcp_names.extend(s.get("name") for s in r.get("mcp", [])[:3])
        skill_names.extend(s.get("name") for s in r.get("skills", [])[:2])
    agent_names = [name for name, _ in agent_files]

    prompt = GENERATE_CLAUDE_MD_PROMPT.format(
        context=json.dumps(context, ensure_ascii=False),
        mcp_names=mcp_names,
        skill_names=skill_names,
        agent_names=agent_names,
    )

    try:
        response = await llm.ainvoke(
            [SystemMessage(content=prompt), HumanMessage(content="Generate the CLAUDE.md now.")]
        )
        return {"claude_md": response.content}
    except Exception:
        return {"claude_md": None}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest agent/tests/test_agent.py::test_generate_claude_md_node_produces_markdown agent/tests/test_agent.py::test_generate_claude_md_node_fallback_on_error -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: add generate_claude_md_node for rich project-specific CLAUDE.md"
```

---

## Task 7: Refactor build_zip_node

**Files:**
- Modify: `agent/agent.py` (`build_zip_node`)
- Test: `agent/tests/test_agent.py`

The old `build_zip_node` generated CLAUDE.md inline. The new version reads from state and packages all artifacts.

- [ ] **Step 1: Write the failing tests**

Note: `base64` was already added to the top-level imports in Task 1 Step 5. Do not add it again.

Add to `agent/tests/test_agent.py`:

```python
@pytest.mark.asyncio
async def test_build_zip_reads_settings_and_claude_md_from_state():
    state = {
        **INITIAL_STATE,
        "search_results": {},
        "generated_agents": [],
        "settings_json": '{"permissions": {"allow": ["Bash(git*)"]}, "hooks": {}, "model": "claude-sonnet-4-6"}',
        "claude_md": "# My Project\n\n## Overview\nA test project.",
    }

    result = await build_zip_node(state)
    buf = io.BytesIO(base64.b64decode(result["zip_bytes"]))
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert ".mcp.json" in names
        assert "CLAUDE.md" in names
        assert ".claude/settings.json" in names
        assert zf.read("CLAUDE.md").decode() == "# My Project\n\n## Overview\nA test project."
        settings = json.loads(zf.read(".claude/settings.json").decode())
        assert "Bash(git*)" in settings["permissions"]["allow"]


@pytest.mark.asyncio
async def test_build_zip_fallback_when_state_fields_are_none():
    state = {
        **INITIAL_STATE,
        "search_results": {},
        "generated_agents": [],
        "settings_json": None,
        "claude_md": None,
    }

    result = await build_zip_node(state)
    buf = io.BytesIO(base64.b64decode(result["zip_bytes"]))
    with zipfile.ZipFile(buf) as zf:
        claude_md = zf.read("CLAUDE.md").decode()
        settings = json.loads(zf.read(".claude/settings.json").decode())
        assert "# Claude Code Setup" in claude_md
        assert settings == {}
```

- [ ] **Step 2: Also fix the two existing zip tests** which use raw bytes instead of base64

In `agent/tests/test_agent.py`, update `test_build_zip_includes_agent_files_when_generated` and `test_build_zip_omits_subagents_section_when_empty` to decode base64:

```python
@pytest.mark.asyncio
async def test_build_zip_includes_agent_files_when_generated():
    state = {
        **INITIAL_STATE,
        "search_results": {},
        "generated_agents": [
            ("code-reviewer", "---\nname: code-reviewer\n---\n\nReview code.\n"),
        ],
        "settings_json": None,
        "claude_md": "# Setup\n\n## Subagents\n- code-reviewer",
    }

    result = await build_zip_node(state)
    buf = io.BytesIO(base64.b64decode(result["zip_bytes"]))
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert ".claude/agents/code-reviewer.md" in names
        assert "CLAUDE.md" in names
        claude_md = zf.read("CLAUDE.md").decode()
        assert "code-reviewer" in claude_md


@pytest.mark.asyncio
async def test_build_zip_omits_subagents_section_when_empty():
    state = {
        **INITIAL_STATE,
        "search_results": {},
        "generated_agents": [],
        "settings_json": None,
        "claude_md": "# Setup\n",
    }

    result = await build_zip_node(state)
    buf = io.BytesIO(base64.b64decode(result["zip_bytes"]))
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert not any("agents" in n for n in names)
        claude_md = zf.read("CLAUDE.md").decode()
        assert "## Subagents" not in claude_md
```

- [ ] **Step 3: Run to verify new tests fail and existing tests now also run correctly**

```bash
python -m pytest agent/tests/test_agent.py::test_build_zip_reads_settings_and_claude_md_from_state agent/tests/test_agent.py::test_build_zip_fallback_when_state_fields_are_none -v
```

Expected: `FAILED` — build_zip_node still uses old inline generation

- [ ] **Step 4: Replace build_zip_node in agent.py**

```python
async def build_zip_node(state: AgentState) -> dict:
    search_results = state.get("search_results", {})
    agent_files = state.get("generated_agents", [])
    settings_json = state.get("settings_json")
    claude_md = state.get("claude_md")

    # Collect MCP servers and skill files from search results
    mcp_servers: list[dict] = []
    skill_files: list[tuple[str, str]] = []
    for query_results in search_results.values():
        mcp_servers.extend(query_results.get("mcp", [])[:3])
        for skill in query_results.get("skills", [])[:2]:
            content = skill.get("content", "")
            if content:
                skill_files.append((skill["name"], content))

    # Build .mcp.json
    mcp_config: dict = {"mcpServers": {}}
    for server in mcp_servers:
        name = server.get("name", "unknown")
        packages = server.get("packages", [])
        if packages:
            pkg = packages[0]
            mcp_config["mcpServers"][name] = {
                "command": "npx",
                "args": ["-y", pkg.get("name", name)],
            }

    # Apply fallbacks for None upstream outputs
    final_claude_md = claude_md if claude_md is not None else "# Claude Code Setup\n"
    final_settings = settings_json if settings_json is not None else "{}"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".mcp.json", json.dumps(mcp_config, indent=2, ensure_ascii=False))
        zf.writestr("CLAUDE.md", final_claude_md)
        zf.writestr(".claude/settings.json", final_settings)
        for name, content in skill_files:
            zf.writestr(f".claude/skills/{name.replace('/', '_')}.md", content)
        for name, content in agent_files:
            zf.writestr(f".claude/agents/{name.replace('/', '_')}.md", content)

    return {"zip_bytes": base64.b64encode(buf.getvalue()).decode("ascii")}
```

- [ ] **Step 5: Run all zip tests**

```bash
python -m pytest agent/tests/test_agent.py -v -k "zip"
```

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add agent/agent.py agent/tests/test_agent.py
git commit -m "feat: refactor build_zip_node to read artifacts from state, add settings.json to zip"
```

---

## Task 8: Update graph wiring and main.py initialization

**Files:**
- Modify: `agent/agent.py` (`build_graph()`)
- Modify: `agent/main.py`
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

Add to `agent/tests/test_agent.py`:

```python
from langgraph.checkpoint.memory import MemorySaver

def test_graph_builds_with_all_new_nodes():
    from agent.agent import build_graph
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer)
    assert graph is not None
    node_names = list(graph.nodes.keys())
    assert "generate_settings" in node_names
    assert "generate_claude_md" in node_names
    assert "generate_subagents" in node_names
    assert "build_zip" in node_names
    assert "decide" in node_names
    assert "search" in node_names
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest agent/tests/test_agent.py::test_graph_builds_with_all_new_nodes -v
```

Expected: `FAILED`

- [ ] **Step 3: Update build_graph() in agent.py**

Replace the `build_graph` function:

```python
def build_graph(checkpointer):
    builder = StateGraph(AgentState)
    builder.add_node("decide", decide_node)
    builder.add_node("search", search_node)
    builder.add_node("generate_subagents", generate_subagents_node)
    builder.add_node("generate_settings", generate_settings_node)
    builder.add_node("generate_claude_md", generate_claude_md_node)
    builder.add_node("build_zip", build_zip_node)

    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", route, ["search", END])
    builder.add_edge("search", "generate_subagents")
    builder.add_edge("generate_subagents", "generate_settings")
    builder.add_edge("generate_settings", "generate_claude_md")
    builder.add_edge("generate_claude_md", "build_zip")
    builder.add_edge("build_zip", END)

    return builder.compile(checkpointer=checkpointer)
```

- [ ] **Step 4: Update main.py initial state**

In `agent/main.py`, in the `/chat` endpoint, add `settings_json` and `claude_md` to the initial state dict:

```python
        input_state = {
            "messages": [HumanMessage(content=req.message)],
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
```

- [ ] **Step 5: Run graph test**

```bash
python -m pytest agent/tests/test_agent.py::test_graph_builds_with_all_new_nodes -v
```

Expected: `PASSED`

- [ ] **Step 6: Also fix the old test_graph_builds_without_error which calls build_graph() with no args**

Update that test:

```python
def test_graph_builds_without_error():
    from agent.agent import build_graph
    from langgraph.checkpoint.memory import MemorySaver
    graph = build_graph(MemorySaver())
    assert graph is not None
```

- [ ] **Step 7: Run full test suite**

```bash
python -m pytest agent/tests/ -v
```

Expected: All tests pass (or pre-existing failures unrelated to this feature).

- [ ] **Step 8: Commit**

```bash
git add agent/agent.py agent/main.py agent/tests/test_agent.py
git commit -m "feat: wire new nodes into graph, update main.py initial state"
```

---

## Task 9: Final integration smoke test

**Files:**
- Test: `agent/tests/test_agent.py`

- [ ] **Step 1: Write an end-to-end integration test**

Add to `agent/tests/test_agent.py`:

```python
@pytest.mark.asyncio
async def test_full_pipeline_video_domain():
    """Smoke test: full pipeline from video domain conversation to zip with settings.json."""
    from agent.agent import build_graph
    from langgraph.checkpoint.memory import MemorySaver

    graph = build_graph(MemorySaver())
    config = {"configurable": {"thread_id": "smoke-video-1"}}

    call_count = 0

    def make_mock_response(content):
        m = MagicMock()
        m.content = content
        return m

    responses = [
        # decide_node: emit search after context gathered
        make_mock_response(json.dumps({
            "action": "search_apis",
            "queries": ["remotion video", "react animation", "ffmpeg video", "video export"],
            "project_context": {
                "type": "video",
                "stack": ["Remotion", "React"],
                "workflows": ["render video"],
                "domain": "video",
                "pain_points": ["slow renders"],
                "daily_workflows": ["render video", "export MP4"],
            }
        })),
        # rerank_results: keep mcp-ffmpeg
        make_mock_response(json.dumps(["mcp-ffmpeg"])),
        # generate_subagents catalog selection: empty
        make_mock_response("[]"),
        # generate_subagents custom: empty
        make_mock_response("[]"),
        # generate_settings
        make_mock_response(json.dumps({
            "permissions": {"allow": ["Bash(npx remotion*)", "Bash(ffmpeg*)"]},
            "hooks": {},
            "model": "claude-sonnet-4-6"
        })),
        # generate_claude_md
        make_mock_response("# Video Project\n\n## Project Overview\nRemotion video renderer.\n\n## Key Commands\n- `npm run render`\n"),
    ]

    response_iter = iter(responses)

    async def mock_ainvoke(messages, **kwargs):
        return next(response_iter)

    with patch.object(ChatAnthropic, "ainvoke", new_callable=AsyncMock, side_effect=mock_ainvoke):
        with patch("agent.agent.search_mcp", new_callable=AsyncMock, return_value=[{"name": "mcp-ffmpeg", "description": "ffmpeg", "packages": [{"name": "@mcp/ffmpeg"}]}]):
            with patch("agent.agent.search_skills", new_callable=AsyncMock, return_value=[]):
                with patch("agent.agent.search_plugins", new_callable=AsyncMock, return_value=[]):
                    state = await graph.ainvoke(
                        {**INITIAL_STATE, "messages": [HumanMessage(content="Remotion 영상 프로젝트입니다")]},
                        config,
                    )

    assert state["zip_bytes"] is not None
    buf = io.BytesIO(base64.b64decode(state["zip_bytes"]))
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert ".mcp.json" in names
        assert "CLAUDE.md" in names
        assert ".claude/settings.json" in names
        claude_md = zf.read("CLAUDE.md").decode()
        assert "Video Project" in claude_md
        settings = json.loads(zf.read(".claude/settings.json"))
        assert "Bash(npx remotion*)" in settings["permissions"]["allow"]
```

- [ ] **Step 2: Run the smoke test**

```bash
python -m pytest agent/tests/test_agent.py::test_full_pipeline_video_domain -v
```

Expected: `PASSED`

- [ ] **Step 3: Run the full test suite one final time**

```bash
python -m pytest agent/tests/ -v
```

Expected: All tests pass.

- [ ] **Step 4: Final commit**

```bash
git add agent/tests/test_agent.py
git commit -m "test: add end-to-end smoke test for video domain pipeline"
```
