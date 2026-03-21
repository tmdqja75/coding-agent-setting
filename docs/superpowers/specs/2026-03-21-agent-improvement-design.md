# Claude Code Environment Setting Agent — Improvement Design

**Date:** 2026-03-21
**Status:** Approved

---

## Problem Statement

The current LangGraph agent in `agent/` produces Claude Code configuration zips (`.mcp.json`, `CLAUDE.md`, subagent `.md` files) but has three core weaknesses:

1. **Domain blindspot** — assumes coding context; cannot handle marketing research, video production (e.g. Remotion), or other non-coding workflows
2. **Shallow context gathering** — captures only project type, tech stack, and workflows; misses pain points and daily workflow specifics
3. **Weak output quality** — `CLAUDE.md` is boilerplate, no `settings.json` is generated, skills search returns noisy unfiltered results

---

## Goals

- Support multiple task domains beyond coding (marketing, video, research, mixed, others)
- Surface pain points and daily workflows to drive better recommendations
- Generate `settings.json` with domain-appropriate permissions, hooks, and model config
- Generate a rich, project-specific `CLAUDE.md`
- Improve skills and MCP search relevance with query expansion and LLM re-ranking

---

## Section 1: Conversation & State Changes

### Domain Detection

The first question in `decide_node` is always domain detection (before any other clarifying question):

> "어떤 유형의 작업에 Claude Code를 사용하실 예정인가요?"

Domain options: **coding / marketing / video production / research / mixed / others**

If the user selects **others**, the agent asks a free-form follow-up:
> "어떤 작업을 하고 계신지 설명해 주세요."

If the free-form response yields no actionable signal (e.g. one-word answer, out-of-scope), the agent proceeds with an empty permissions list, no hooks, and the default model (`claude-sonnet-4-6`) as safe fallbacks.

### Domain-Specific Follow-up Questions

After domain is detected, the agent asks 1-2 domain-specific questions:

| Domain | Follow-up questions |
|---|---|
| coding | Tech stack + CI/CD and deployment target |
| marketing | Content types and target platforms + research tools used |
| video production | Framework (Remotion/FFmpeg/other) + output format and asset pipeline |
| research | Data sources and output format + collaboration tools |
| mixed | Brief description of each area covered |
| others | Inferred from free-form description; safe defaults applied if no signal |

After domain-specific questions, the agent always asks one pain-points question:
> "가장 시간이 많이 걸리거나 불편한 작업은 무엇인가요?"

### Question Budget

Maximum questions: **4** (up from 3) — domain (1) + domain-specific (1-2) + pain points (1).

### AgentState Changes

`AgentState.context` gains three new fields:

```python
"domain": str          # "coding" | "marketing" | "video" | "research" | "mixed" | "others"
"pain_points": list[str]
"daily_workflows": list[str]
```

Two new top-level fields are added to `AgentState` to carry upstream node outputs into `build_zip_node`:

```python
settings_json: str | None    # JSON string for .claude/settings.json
claude_md: str | None        # Markdown string for CLAUDE.md
```

---

## Section 2: New Graph Nodes & Updated Flow

### New Nodes

**`generate_settings_node`**

- **Input:** `state["context"]` (including `domain`, `pain_points`, `daily_workflows`)
- **Output:** `{"settings_json": "<json string>"}` stored in `AgentState.settings_json`
- Dedicated LLM call producing `.claude/settings.json` with a `permissions.allow` list, 1-2 lifecycle hooks, and a model recommendation — all driven by the domain. Falls back to safe defaults (empty allow list, no hooks, `claude-sonnet-4-6`) if domain yields no signal.

**`generate_claude_md_node`**

- **Input:** `state["context"]`, `state["search_results"]` (for MCP/skill names), `state["generated_agents"]`
- **Output:** `{"claude_md": "<markdown string>"}` stored in `AgentState.claude_md`
- Dedicated LLM call producing a rich, project-specific `CLAUDE.md` using context, pain_points, and daily_workflows.

### Updated Graph Flow

All new nodes use **fixed (unconditional) edges**. The `action == "build_zip"` branch in `decide_node` is **removed** — there is no longer a direct shortcut from `decide` to `build_zip`. Every conversation must flow through the full pipeline. Consequently, `route()` no longer needs the `"build"` / `"build_zip"` case; it only routes to `"search"` or `END`. `build_graph()` is updated to remove `"build_zip"` from the conditional edge targets list.

```
START → decide → search → generate_subagents → generate_settings → generate_claude_md → build_zip → END
```

Fixed edges added:
- `search → generate_subagents` (already exists)
- `generate_subagents → generate_settings` (new)
- `generate_settings → generate_claude_md` (new)
- `generate_claude_md → build_zip` (replaces `generate_subagents → build_zip`)

Removed:
- The `phase = "build"` / `action == "build_zip"` path in `decide_node`
- The `"build_zip"` conditional edge target in `build_graph()`

### `build_zip_node` simplification

`build_zip_node` reads `CLAUDE.md` content from `state["claude_md"]` and `settings.json` content from `state["settings_json"]`. It no longer generates either artifact inline. The old inline `CLAUDE.md` generation (lines 283-303 in `agent.py`) is removed.

**Fallback policy:** if either field is `None` (e.g. upstream node raised an exception), `build_zip_node` uses safe defaults:
- `claude_md` is `None` → write a minimal `CLAUDE.md` with only the heading `# Claude Code Setup`
- `settings_json` is `None` → write `{}` as the settings file content

Both `settings_json` and `claude_md` must be initialized to `None` in the initial state dict passed by `main.py`'s `/chat` endpoint (alongside `zip_bytes: None`).

### Domain-to-Permissions Mapping

| Domain | `permissions.allow` examples |
|---|---|
| coding | `Bash(git*)`, `Bash(npm*)`, `Bash(python*)` |
| video | `Bash(npx remotion*)`, `Bash(ffmpeg*)`, `Bash(npm*)` |
| marketing | `WebFetch(*)`, `Bash(curl*)` |
| research | `WebFetch(*)`, `Bash(python*)` |
| mixed | Union of relevant domain permissions based on described areas |
| others | Inferred from free-form description; fallback: empty list |

### Domain-to-Hooks Mapping

| Domain | Hook example |
|---|---|
| coding | `PostToolUse` → run linter after file edits |
| video | `PostToolUse` → validate render config after edits |
| marketing / research | No hooks |
| mixed | Hooks from the most relevant sub-domain present |
| others | Inferred from free-form description; fallback: no hooks |

### Model Recommendation

Model IDs are illustrative — confirm against Anthropic API before use:

| Domain | Recommended model |
|---|---|
| research / complex coding | `claude-opus-4-6` |
| coding / video | `claude-sonnet-4-6` |
| marketing / simple lookups | `claude-haiku-4-5-20251001` |

---

## Section 3: Improved Skills Search Accuracy

### Problem

Current: 2-3 generic queries (e.g. `["python", "fastapi"]`) → noisy results with no filtering.

### Fix 1: Multi-Query Expansion

The LLM generates **5-6 targeted search queries** from the full context including `domain`, `pain_points`, and `daily_workflows`.

Example — Remotion video project:
```
["remotion video generation", "react animation rendering",
 "video export pipeline", "motion graphics react", "ffmpeg integration"]
```
instead of: `["video", "react"]`

### Fix 2: LLM Re-ranking Pass

After all search results are retrieved, a dedicated `rerank_results()` function in `agent.py` (not `tools.py`) makes a single LLM call to score each result against the full project context.

- **Scoring schema:** binary keep/drop per result (LLM returns a JSON array of names to keep)
- **Threshold:** any result not in the keep list is dropped
- **Output:** filtered `search_results` dict, replacing the unfiltered version in state before downstream nodes read it
- **Call site:** `rerank_results()` is a helper function in `agent.py` called at the **end of `search_node`**, after all HTTP searches complete. `search_node` calls it and returns the filtered dict as `{"search_results": filtered}`. It is not a separate graph node.
- **Zero-results handling:** if all queries return empty results (API down or no matches), re-ranking is skipped and downstream nodes receive empty search_results — this is a valid no-op path that produces a zip with empty `.mcp.json` and no skills/agents

This re-ranking applies to both `search_mcp` and `search_skills` results. `search_plugins` remains a stub.

`tools.py` gains no new LLM logic — HTTP API functions only, consistent with current pattern.

---

## Section 4: Output Artifact Generation

### `generate_settings_node` output: `.claude/settings.json`

```json
{
  "permissions": {
    "allow": ["Bash(git*)", "Bash(npm*)"]
  },
  "hooks": {
    "PostToolUse": [{ "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "npm run lint" }] }]
  },
  "model": "claude-sonnet-4-6"
}
```

Fields are domain-driven. The LLM is given domain, pain_points, and daily_workflows to produce a tailored JSON. If the domain is `others` and no signal is extracted, an empty `permissions.allow`, no hooks, and default model are used.

### `generate_claude_md_node` output: `CLAUDE.md`

Sections in the generated `CLAUDE.md`:
- **Project overview** — derived from conversation context
- **Key commands** — domain-specific (build/dev/test for coding; render/export for video; etc.)
- **Workflows** — derived from `pain_points` (e.g. "When debugging renders, use X approach")
- **Conventions and constraints** — from user responses

### `generate_subagents_node` (improved)

`domain`, `pain_points`, and `daily_workflows` are injected into both the catalog selection prompt and the custom subagent generation prompt. This prevents irrelevant recommendations (e.g. `kubernetes-specialist` for a Remotion video project) and enables domain-specific custom agents (e.g. a `remotion-video-renderer` agent for a video project).

---

## File Changes Summary

| File | Change |
|---|---|
| `agent/state.py` | Add `settings_json: str \| None` and `claude_md: str \| None` as top-level `AgentState` fields; `domain`, `pain_points`, `daily_workflows` added to `context` dict (runtime, not typed) |
| `agent/agent.py` | Update `SYSTEM_PROMPT` with domain-aware question banks (4-question max); remove `action == "build_zip"` branch from `decide_node`; update `route()` to remove `"build"` case; update `build_graph()` to remove `"build_zip"` from conditional edge targets and add fixed edges for new nodes; add `generate_settings_node`, `generate_claude_md_node`, `rerank_results()` helper (called inside `search_node`); update `SELECT_SUBAGENTS_PROMPT`, `CUSTOM_SUBAGENTS_PROMPT`, and their user messages to include `domain`, `pain_points`, `daily_workflows`; remove inline CLAUDE.md generation from `build_zip_node`; update `build_zip_node` to read from `state["settings_json"]` and `state["claude_md"]` with `None` fallbacks |
| `agent/main.py` | Add `settings_json: None` and `claude_md: None` to initial state dict in `/chat` endpoint |
| `agent/tools.py` | No changes |

---

## Out of Scope

- Fixing `search_plugins` (remains a stub)
- Multi-language support beyond Korean questions
- User accounts or saved configurations
