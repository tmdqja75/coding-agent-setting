import json
import io
import zipfile
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
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


async def decide_node(state: AgentState) -> dict:
    response = await llm.ainvoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    )

    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        parsed = {"action": "ask_question", "question": "프로젝트에 대해 더 알려주세요."}

    action = parsed.get("action", "ask_question")

    if action == "ask_question":
        return {"next_question": parsed.get("question"), "phase": "clarify"}
    elif action == "search_apis":
        return {"phase": "search", "pending_queries": parsed.get("queries", []), "next_question": None}
    elif action == "build_zip":
        return {"phase": "build", "next_question": None}

    return {"next_question": parsed.get("question", "더 알려주세요."), "phase": "clarify"}


async def search_node(state: AgentState) -> dict:
    queries = state.get("pending_queries", [])
    results = dict(state.get("search_results", {}))

    async def run_searches(query: str) -> dict:
        mcp, skills, plugins = await asyncio.gather(
            search_mcp(query),
            search_skills(query),
            search_plugins(query),
        )
        return {"mcp": mcp, "skills": skills, "plugins": plugins}

    for query in queries:
        results[query] = await run_searches(query)

    return {"search_results": results}


async def _curate_results(messages: list, search_results: dict) -> dict:
    """Ask the LLM to select relevant items from raw search results."""
    # Collect unique candidates across all queries
    seen_skill_ids: set[str] = set()
    seen_plugin_ids: set[str] = set()
    seen_mcp_names: set[str] = set()
    all_skills, all_plugins, all_mcp = [], [], []

    for query_results in search_results.values():
        for s in query_results.get("skills", []):
            if s["id"] not in seen_skill_ids:
                seen_skill_ids.add(s["id"])
                all_skills.append({"name": s["name"], "description": s.get("description", ""), "rawFileUrl": s.get("metadata", {}).get("rawFileUrl")})
        for p in query_results.get("plugins", []):
            if p["id"] not in seen_plugin_ids:
                seen_plugin_ids.add(p["id"])
                all_plugins.append({"name": p["name"], "description": p.get("description", "")})
        for m in query_results.get("mcp", []):
            name = m.get("name", "")
            if name not in seen_mcp_names:
                seen_mcp_names.add(name)
                all_mcp.append(m)

    curate_prompt = f"""Based on the user's project requirements from the conversation, select ONLY the relevant items.

Available skills:
{json.dumps([{"name": s["name"], "description": s["description"]} for s in all_skills], ensure_ascii=False, indent=2)}

Available plugins:
{json.dumps([{"name": p["name"], "description": p["description"]} for p in all_plugins], ensure_ascii=False, indent=2)}

Available MCP servers:
{json.dumps([{"name": m.get("name"), "description": m.get("description", "")} for m in all_mcp], ensure_ascii=False, indent=2)}

Reply with JSON only:
{{"selected_skills": ["name1", "name2"], "selected_plugins": ["name1"], "selected_mcp": ["name1"]}}

Select only items genuinely useful for this specific project. Omit frontend/UI tools if the project is not a frontend project."""

    response = await llm.ainvoke([*messages, {"role": "user", "content": curate_prompt}])
    try:
        selected = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback: keep all candidates if curation fails
        selected = {
            "selected_skills": [s["name"] for s in all_skills[:3]],
            "selected_plugins": [p["name"] for p in all_plugins[:2]],
            "selected_mcp": [m.get("name") for m in all_mcp[:3]],
        }

    selected_skill_names = set(selected.get("selected_skills", []))
    selected_plugin_names = set(selected.get("selected_plugins", []))
    selected_mcp_names = set(selected.get("selected_mcp", []))

    return {
        "skills": [s for s in all_skills if s["name"] in selected_skill_names],
        "plugins": [p for p in all_plugins if p["name"] in selected_plugin_names],
        "mcp": [m for m in all_mcp if m.get("name") in selected_mcp_names],
    }


async def build_zip_node(state: AgentState) -> dict:
    search_results = state.get("search_results", {})

    curated = await _curate_results(state["messages"], search_results)

    mcp_servers: list[dict] = curated["mcp"]
    skill_files: list[tuple[str, str]] = []
    agent_files: list[tuple[str, str]] = []

    for skill in curated["skills"]:
        raw_url = skill.get("rawFileUrl")
        if raw_url:
            try:
                content = await download_file(raw_url)
                skill_files.append((skill["name"], content))
            except Exception:
                pass

    for plugin in curated["plugins"]:
        for agent_name in (plugin.get("agents") or "").split(","):
            agent_name = agent_name.strip()
            if agent_name:
                agent_files.append((agent_name, f"# {agent_name} subagent\n"))

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

    return {"zip_bytes": buf.getvalue()}


def route(state: AgentState) -> str:
    phase = state.get("phase", "clarify")
    if phase == "search":
        return "search"
    elif phase == "build":
        return "build_zip"
    return END


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("decide", decide_node)
    builder.add_node("search", search_node)
    builder.add_node("build_zip", build_zip_node)

    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", route, ["search", "build_zip", END])
    builder.add_edge("search", "build_zip")
    builder.add_edge("build_zip", END)

    return builder.compile(checkpointer=InMemorySaver())
