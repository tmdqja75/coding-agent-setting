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
{"action": "search_apis", "queries": ["<query1>", "<query2>"], "project_context": {"type": "<project type>", "stack": ["<tech1>"], "workflows": ["<workflow1>"]}}

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
        return {
            "phase": "search",
            "pending_queries": parsed.get("queries", []),
            "context": parsed.get("project_context", {}),
            "next_question": None,
        }
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


GENERATE_SUBAGENTS_PROMPT = """You are a Claude Code configuration expert. Based on the user's
project context and available tools found by search, decide whether custom subagents would be
useful and generate them if so.

Output a JSON array. If no subagents are needed, return an empty array: []

If subagents are useful, return 2-4 definitions:
[
  {
    "name": "kebab-case-name",
    "description": "Specific trigger description for when Claude should delegate here",
    "tools": ["Read", "Grep", "Glob"],
    "model": "haiku",
    "system_prompt": "Focused system prompt for this agent..."
  }
]

Rules:
- Only generate subagents that solve real, recurring tasks for the given project
- Use the minimum tools needed (principle of least privilege)
- model: "haiku" for fast/cheap lookup tasks, "sonnet" for reasoning tasks, "opus" for complex work
- If the project is simple or has no clear recurring workflows, return []
- Available tools: Read, Write, Edit, Bash, Glob, Grep, Agent
- Write the "system_prompt" field in Korean"""


async def generate_subagents_node(state: AgentState) -> dict:
    context = state.get("context", {})
    search_results = state.get("search_results", {})

    found_mcps = []
    found_skills = []
    found_plugins = []
    for q, r in search_results.items():
        found_mcps.extend([s.get("name") for s in r.get("mcp", [])[:3]])
        found_skills.extend([s.get("name") for s in r.get("skills", [])[:2]])
        found_plugins.extend([p.get("name") for p in r.get("plugins", [])[:1]])

    user_message = f"""Project context: {json.dumps(context)}

Available MCP servers: {found_mcps}
Available skills: {found_skills}
Available plugins: {found_plugins}

Generate subagents for this project, or return [] if none are needed."""

    response = await llm.ainvoke(
        [SystemMessage(content=GENERATE_SUBAGENTS_PROMPT), HumanMessage(content=user_message)]
    )

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()
        definitions = json.loads(raw)
        if not isinstance(definitions, list):
            definitions = []
    except (json.JSONDecodeError, ValueError):
        definitions = []

    agent_files: list[tuple[str, str]] = []
    for defn in definitions:
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
            raw_url = skill.get("metadata", {}).get("rawFileUrl") or skill.get("sourceUrl")
            if raw_url:
                try:
                    content = await download_file(raw_url)
                    skill_files.append((skill["name"], content))
                except Exception:
                    pass

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
    builder.add_node("generate_subagents", generate_subagents_node)
    builder.add_node("build_zip", build_zip_node)

    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", route, ["search", "build_zip", END])
    builder.add_edge("search", "generate_subagents")
    builder.add_edge("generate_subagents", "build_zip")
    builder.add_edge("build_zip", END)

    return builder.compile(checkpointer=InMemorySaver())
