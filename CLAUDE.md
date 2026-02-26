# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start development server at http://localhost:3000
npm run build    # Production build
npm run start    # Start production server
npm run lint     # Run ESLint
```

## Architecture

Next.js 16 App Router application — a Korean-language educational site documenting Claude Code features.

**Key directories:**
- `app/` — App Router pages. `app/claude-code-components/` contains feature sub-pages (mcp, subagents, hooks, skills).
- `components/ui/` — Shared UI components used across pages.

**Component patterns:**
- Feature pages (`mcp/page.tsx`, `subagents/page.tsx`, etc.) all render `<FeatureDetail>` from `components/ui/feature-detail.tsx` with Korean content props.
- `components/ui/animated-shader-hero.tsx` — WebGL2-based hero with embedded renderer/pointer handler classes and a `useShaderBackground()` hook. Modify shader effects in the GLSL fragment shader string inside this file.
- `components/ui/interactive-hover-links.tsx` — Framer Motion client component with spring-physics hover animations linking to the four feature sub-pages.

**Stack:** Next.js 16, React 19, TypeScript 5, Tailwind CSS v4, Framer Motion (motion) 12, lucide-react, react-icons.

**Path alias:** `@/*` maps to the project root.

**No backend** — static/client-side only; no API routes or database.

## Claude Code Plugin

`.claude/settings.json` enables the `frontend-design@claude-plugins-official` plugin. UI work should follow high-quality design standards consistent with existing components.
