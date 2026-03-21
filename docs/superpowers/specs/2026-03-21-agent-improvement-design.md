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

The free-form response is used to infer relevant tools and skills the same way explicit domains are used.

### Domain-Specific Follow-up Questions

After domain is detected, the agent asks 1-2 domain-specific questions:

| Domain | Follow-up questions |
|---|---|
| coding | Tech stack + CI/CD and deployment target |
| marketing | Content types and target platforms + research tools used |
| video production | Framework (Remotion/FFmpeg/other) + output format and asset pipeline |
| research | Data sources and output format + collaboration tools |
| mixed | Brief description of each area covered |
| others | Inferred from free-form description |

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

---

## Section 2: New Graph Nodes & Updated Flow

### New Nodes

**`generate_settings_node`**
Dedicated LLM call that produces `.claude/settings.json` with:
- `permissions.allow` list based on domain
- 1-2 lifecycle hooks appropriate to the domain
- Model recommendation based on task complexity

**`generate_claude_md_node`**
Dedicated LLM call that produces a rich, project-specific `CLAUDE.md` using `context`, `pain_points`, and `daily_workflows`.

### Updated Graph Flow

```
START → decide → search → generate_subagents → generate_settings → generate_claude_md → build_zip → END
```

`build_zip_node` is simplified: it only packages artifacts produced by upstream nodes, with no generation logic of its own.

### Domain-to-Permissions Mapping

| Domain | `permissions.allow` examples |
|---|---|
| coding | `Bash(git*)`, `Bash(npm*)`, `Bash(python*)` |
| video | `Bash(npx remotion*)`, `Bash(ffmpeg*)`, `Bash(npm*)` |
| marketing | `WebFetch(*)`, `Bash(curl*)` |
| research | `WebFetch(*)`, `Bash(python*)` |
| others | Inferred from free-form description |

### Domain-to-Hooks Mapping

| Domain | Hook example |
|---|---|
| coding | `PostToolUse` → run linter after file edits |
| video | `PostToolUse` → validate render config after edits |
| others | Inferred from free-form description |

### Model Recommendation

| Domain | Recommended model |
|---|---|
| research / complex coding | `claude-opus-4-6` |
| coding / video | `claude-sonnet-4-6` |
| marketing / simple lookups | `claude-haiku-4-5` |

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

After all search results are retrieved, a single lightweight LLM call scores each result (MCP server or skill) against the full project context and drops low-relevance entries before they reach downstream nodes.

This re-ranking applies to both `search_mcp` and `search_skills` results. `search_plugins` remains a stub.

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

Fields are domain-driven. The LLM is given the domain, pain_points, and daily_workflows to produce a tailored JSON.

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
| `agent/state.py` | Add `domain`, `pain_points`, `daily_workflows` to `AgentState.context` schema |
| `agent/agent.py` | Update `SYSTEM_PROMPT` with domain-aware question banks; add `generate_settings_node`, `generate_claude_md_node`; update graph edges; improve query expansion in `search_node`; add re-ranking step |
| `agent/tools.py` | No structural changes; re-ranking logic added as a new function |

---

## Out of Scope

- Fixing `search_plugins` (remains a stub)
- Multi-language support beyond Korean questions
- User accounts or saved configurations
