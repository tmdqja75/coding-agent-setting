"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { BsStars } from "react-icons/bs";

const description =
  "Skills는 마크다운 파일로 작성된 재사용 가능한 슬래시 명령어입니다. /skill-name 형식으로 호출하면 해당 파일의 내용이 전체 프롬프트로 확장되어 Claude에게 전달됩니다. 반복적인 작업 패턴을 Skills로 정의해두면 일관된 방식으로 빠르게 실행할 수 있습니다.";

const howToUse = [
  "자주 반복하는 작업을 하나의 스킬 단위로 정의합니다.",
  "~/.claude/skills 디렉터리에 .md 파일을 생성합니다.",
  "작업 절차, 규칙, 예시를 마크다운으로 구체적으로 작성합니다.",
  "터미널에서 /skill-name 명령으로 호출해 실행합니다.",
];

const example = `# ~/.claude/skills/commit.md
# commit

스테이징된 변경사항을 Conventional Commits 형식으로 커밋합니다.

## 단계

1. \`git diff --staged\`로 변경사항 확인
2. 변경의 성격에 맞는 타입 선택:
   - feat: 새로운 기능
   - fix: 버그 수정
   - refactor: 코드 리팩토링
   - docs: 문서 수정
3. 커밋 메시지 작성: \`type(scope): 설명\`
4. \`git commit -m "메시지"\` 실행

---
# 터미널에서 호출
> /commit`;

export default function SkillsPage() {
  return (
    <FeatureDetail
      heading="Skills"
      subheading="재사용 가능한 슬래시 명령어로 Claude Code를 확장하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      icon={BsStars}
    />
  );
}
