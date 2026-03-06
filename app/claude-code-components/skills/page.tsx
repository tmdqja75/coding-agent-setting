"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { LuWorkflow } from "react-icons/lu";

const description = [
  "Skills는 자주 반복되는 작업을 SKILL.md 파일로 정의한 재사용 가능한 슬래시 명령어 시스템입니다. ~/.claude/skills/<name>/ 디렉터리에 SKILL.md를 생성하면 /<name> 형식으로 언제든 호출할 수 있습니다.",
  "점진적 컨텍스트 통합(Gradual Context Integration): 스킬의 description은 항상 컨텍스트에 로드되어 Claude가 언제 사용할지 파악하지만, 실제 스킬 내용은 호출 시에만 로드됩니다. 덕분에 많은 스킬을 등록해도 컨텍스트 창을 낭비하지 않습니다.",
  "YAML frontmatter의 description 필드를 통해 Claude가 대화 흐름에 맞는 스킬을 자동으로 호출합니다. disable-model-invocation: true를 설정하면 직접 호출 전용으로 사용할 수 있습니다.",
  "스킬 디렉터리에 template.md(출력 템플릿), examples/(예시 파일), scripts/(검증 스크립트) 등 보조 파일을 함께 배치할 수 있습니다. SKILL.md에서 참조하면 Claude가 필요할 때만 로드해 컨텍스트를 효율적으로 사용합니다.",
  "커밋 작성·코드 리뷰·문서화 등 반복 워크플로우를 스킬로 정의하면, 팀 전체가 동일한 기준으로 작업을 일관되게 수행할 수 있습니다.",
  "적용 범위를 유연하게 설정할 수 있습니다: 개인용(~/.claude/skills/), 프로젝트 전용(.claude/skills/), 조직 전체 배포(managed settings).",
];

const howToUse = [
  "스킬 디렉터리를 생성합니다: mkdir ~/.claude/skills/<skill-name>",
  "SKILL.md 파일을 생성하고 YAML frontmatter에 name과 description을 작성합니다.",
  "마크다운 본문에 작업 절차, 규칙, 예시를 구체적으로 작성합니다.",
  "Claude가 description을 보고 자동 호출하거나, /<skill-name>으로 직접 호출합니다.",
  "프로젝트의 .claude/skills/를 버전 관리에 커밋해 팀과 공유합니다.",
];

const diagram = `commit/
├── SKILL.md          # 메인 지침 (필수)
├── template.md       # 커밋 메시지 템플릿
├── examples/
│   └── sample.md     # 좋은 커밋 메시지 예시
└── scripts/
    └── validate.sh   # 커밋 메시지 형식 검증`;

const example = `# ~/.claude/skills/commit/SKILL.md

---
name: commit
description: 스테이징된 변경사항을 Conventional Commits
  형식으로 커밋합니다. 커밋 메시지 작성 시 사용.
disable-model-invocation: true
---

스테이징된 변경사항을 Conventional Commits 형식으로 커밋합니다.

## 단계

1. \`git diff --staged\`로 변경사항 확인
2. 변경의 성격에 맞는 타입 선택:
   - feat: 새로운 기능 / fix: 버그 수정
   - refactor: 리팩토링 / docs: 문서
   - chore: 빌드·설정 변경
3. 커밋 메시지 작성: \`type(scope): 설명\`
4. scripts/validate.sh로 형식 검증 후 커밋

## 추가 리소스

- 출력 형식은 [template.md](template.md) 참고
- 좋은 예시는 [examples/sample.md](examples/sample.md) 참고

---

# 호출 방법
> /commit

# 다른 스킬 예시
> /review    # PR 코드 리뷰 (Claude 자동 호출)
> /document  # 함수·컴포넌트 문서화`;

export default function SkillsPage() {
  return (
    <FeatureDetail
      heading="Skills"
      subheading="재사용 가능한 슬래시 명령어로 Claude Code를 확장하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      diagram={diagram}
      icon={LuWorkflow}
      accentColor="#a78bfa"
      tags={["슬래시 명령어", "재사용", "표준화", "컨텍스트 통합"]}
    />
  );
}
