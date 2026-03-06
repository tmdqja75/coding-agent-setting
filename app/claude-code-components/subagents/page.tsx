"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { FaRobot } from "react-icons/fa";

const description = [
  "Subagents는 Claude Code가 복잡한 작업을 독립적인 단위로 분리해 전문 하위 에이전트에게 위임하는 메커니즘입니다. 각 서브에이전트는 독립적인 컨텍스트 창을 가지므로 메인 대화의 컨텍스트를 소모하지 않고 깊이 있는 작업을 수행할 수 있습니다.",
  "컨텍스트 절약이 핵심 이점입니다. 테스트 실행·로그 분석·대규모 코드베이스 탐색처럼 출력이 방대한 작업을 서브에이전트에 위임하면, 상세 결과는 에이전트 내부에 머물고 요약만 메인 대화로 돌아옵니다.",
  "독립적인 작업은 여러 서브에이전트가 동시에 병렬로 처리할 수 있습니다. 프론트엔드·백엔드·DB 모듈을 각각 다른 에이전트가 탐색하면 전체 소요 시간을 크게 단축할 수 있습니다.",
  "기본 내장 에이전트: Explore(읽기 전용·Haiku 모델로 코드베이스 빠른 탐색), Plan(플랜 모드 전용 리서치), General-purpose(탐색과 수정 모두 가능한 범용 에이전트).",
  "커스텀 서브에이전트는 .claude/agents/ 또는 ~/.claude/agents/에 마크다운 파일로 정의합니다. YAML frontmatter로 사용할 도구·모델·권한 모드를 세밀하게 제어할 수 있습니다.",
  "서브에이전트가 적합한 상황: 대량의 출력이 발생하는 작업, 특정 도구만 허용해야 하는 작업, 결과 요약만 필요한 독립적인 자기완결 작업. 잦은 수정이 필요하거나 단순한 변경은 메인 대화가 더 효율적입니다.",
];

const howToUse = [
  "/agents 명령으로 서브에이전트 관리 인터페이스를 엽니다.",
  "Create new agent를 선택하고 범위를 결정합니다: 프로젝트 전용(.claude/agents/) 또는 전체 프로젝트 공용(~/.claude/agents/).",
  ".claude/agents/<name>.md 파일을 생성하고 YAML frontmatter에 name·description·tools·model을 작성합니다.",
  "마크다운 본문에 에이전트가 따를 시스템 프롬프트를 구체적으로 작성합니다.",
  "대화에서 'code-reviewer 서브에이전트로 변경사항을 검토해줘'처럼 명시적으로 호출하거나, Claude가 description을 보고 자동으로 위임합니다.",
  "독립적인 작업은 여러 서브에이전트를 동시에 실행하도록 요청해 처리 시간을 단축합니다.",
];

const diagram = `.claude/agents/
├── code-reviewer.md   # 프로젝트 전용 (버전 관리 가능)
└── debugger.md

~/.claude/agents/
└── data-analyst.md    # 모든 프로젝트에서 사용 가능`;

const example = `# .claude/agents/code-reviewer.md

---
name: code-reviewer
description: 코드 품질·보안·모범 사례를 검토하는 전문
  리뷰어. 코드 변경 후 즉시 사용.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a senior code reviewer ensuring high standards.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files and begin review

Review checklist:
- Readability and naming conventions
- No duplicated code or exposed secrets
- Proper error handling and input validation
- Test coverage and performance

---

# 호출 방법
> code-reviewer 서브에이전트로 최근 변경사항 검토해줘

# 병렬 실행 예시
> 프론트엔드와 백엔드 모듈을 각각 별도
  서브에이전트로 동시에 분석해줘`;

export default function SubagentsPage() {
  return (
    <FeatureDetail
      heading="Subagents"
      subheading="컨텍스트를 절약하고 작업을 병렬로 위임하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      diagram={diagram}
      icon={FaRobot}
      accentColor="#f97316"
      tags={["병렬 처리", "컨텍스트 절약", "커스텀 에이전트", "자동 위임"]}
    />
  );
}
