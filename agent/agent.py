import base64
import json
import io
import zipfile
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
import os
from langgraph.types import interrupt
from agent.state import AgentState
from agent.tools import (
    search_mcp, search_skills, search_plugins,
    fetch_subagent_content, get_catalog_index_text,
)

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

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


def _parse_json_response(raw: str) -> list:
    """Parse a JSON array from an LLM response, handling markdown code fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()
    result = json.loads(raw)
    return result if isinstance(result, list) else []


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


async def generate_subagents_node(state: AgentState) -> dict:
    context = state.get("context", {})
    search_results = state.get("search_results", {})

    found_mcps = []
    found_skills = []
    found_plugins = []
    for _, r in search_results.items():
        found_mcps.extend([s.get("name") for s in r.get("mcp", [])[:3]])
        found_skills.extend([s.get("name") for s in r.get("skills", [])[:2]])
        found_plugins.extend([p.get("name") for p in r.get("plugins", [])[:1]])

    # ── Phase A: Select from catalog ──
    catalog_index = get_catalog_index_text()
    select_prompt = SELECT_SUBAGENTS_PROMPT.format(catalog_index=catalog_index)

    select_user_msg = f"""Project context: {json.dumps(context)}

Domain: {context.get('domain', 'unknown')}
Pain points: {context.get('pain_points', [])}
Daily workflows: {context.get('daily_workflows', [])}
Available MCP servers: {found_mcps}
Available skills: {found_skills}
Available plugins: {found_plugins}

Select the most relevant subagents from the catalog for this project."""

    catalog_selections: list[dict] = []
    try:
        response = await llm.ainvoke(
            [SystemMessage(content=select_prompt), HumanMessage(content=select_user_msg)]
        )
        catalog_selections = _parse_json_response(response.content)
    except Exception:
        catalog_selections = []

    # Fetch full .md content for each selected catalog subagent
    agent_files: list[tuple[str, str]] = []
    selected_names: list[str] = []

    async def fetch_catalog_entry(entry: dict) -> tuple[str, str] | None:
        name = entry.get("name", "").strip()
        category = entry.get("category", "").strip()
        if not name or not category:
            return None
        content = await fetch_subagent_content(name, category)
        if content:
            return (name, content)
        return None

    fetch_tasks = [fetch_catalog_entry(e) for e in catalog_selections[:4]]
    fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    for result in fetch_results:
        if isinstance(result, tuple):
            agent_files.append(result)
            selected_names.append(result[0])

    # ── Phase B: Generate custom subagents for gaps ──
    custom_prompt = CUSTOM_SUBAGENTS_PROMPT.format(
        selected_names=", ".join(selected_names) if selected_names else "(none)"
    )

    custom_user_msg = f"""Project context: {json.dumps(context)}

Domain: {context.get('domain', 'unknown')}
Pain points: {context.get('pain_points', [])}
Daily workflows: {context.get('daily_workflows', [])}
Available MCP servers: {found_mcps}
Available skills: {found_skills}

Generate custom subagents only for gaps not covered by the catalog selections, or return [] if no gaps exist."""

    try:
        response = await llm.ainvoke(
            [SystemMessage(content=custom_prompt), HumanMessage(content=custom_user_msg)]
        )
        custom_definitions = _parse_json_response(response.content)
    except Exception:
        custom_definitions = []

    for defn in custom_definitions[:2]:
        name = defn.get("name", "").strip()
        if not name:
            continue
        tools_list = ", ".join(defn.get("tools", []))
        model = defn.get("model", "inherit")
        description = defn.get("description", "")
        system_prompt = defn.get("system_prompt", "")
        content = (
            f"---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            f"tools: {tools_list}\n"
            f"model: {model}\n"
            f"---\n\n"
            f"{system_prompt}\n"
        )
        agent_files.append((name, content))

    return {"generated_agents": agent_files}


async def build_zip_node(state: AgentState) -> dict:
    search_results = state.get("search_results", {})
    agent_files = state.get("generated_agents", [])

    mcp_servers: list[dict] = []
    skill_files: list[tuple[str, str]] = []

    for query_results in search_results.values():
        mcp_servers.extend(query_results.get("mcp", [])[:3])
        for skill in query_results.get("skills", [])[:2]:
            content = skill.get("content", "")
            if content:
                skill_files.append((skill["name"], content))

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
    if agent_files:
        claude_md_lines += ["", "## Subagents"]
        for name, _ in agent_files:
            claude_md_lines.append(f"- {name}")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".mcp.json", json.dumps(mcp_config, indent=2, ensure_ascii=False))
        zf.writestr("CLAUDE.md", "\n".join(claude_md_lines))
        for name, content in skill_files:
            zf.writestr(f".claude/skills/{name.replace('/', '_')}.md", content)
        for name, content in agent_files:
            zf.writestr(f".claude/agents/{name.replace('/', '_')}.md", content)

    return {"zip_bytes": base64.b64encode(buf.getvalue()).decode("ascii")}


def route(state: AgentState) -> str:
    phase = state.get("phase", "clarify")
    if phase == "search":
        return "search"
    return END


def build_graph(checkpointer):
    builder = StateGraph(AgentState)
    builder.add_node("decide", decide_node)
    builder.add_node("search", search_node)
    builder.add_node("generate_subagents", generate_subagents_node)
    builder.add_node("build_zip", build_zip_node)

    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", route, ["search", END])
    builder.add_edge("search", "generate_subagents")
    builder.add_edge("generate_subagents", "build_zip")
    builder.add_edge("build_zip", END)

    return builder.compile(checkpointer=checkpointer)
