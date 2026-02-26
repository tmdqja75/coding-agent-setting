"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { GiFishingHook } from "react-icons/gi";

const description =
  "Hooks는 Claude Code가 특정 동작을 수행할 때 자동으로 실행되는 셸 명령어입니다. 파일 편집 후 린트 실행, Bash 명령 실행 전 로깅, 위험한 작업 차단 등 다양한 워크플로우 자동화에 활용할 수 있습니다. PreToolUse, PostToolUse 등 이벤트 시점에 따라 세밀하게 제어할 수 있습니다.";

const howToUse = [
  "~/.claude/settings.json 파일에 hooks 설정을 추가합니다.",
  "실행 시점(PreToolUse, PostToolUse 등)과 matcher를 지정합니다.",
  "자동 실행할 command 훅을 등록합니다.",
  "원하는 툴 동작을 수행해 훅이 정상 동작하는지 확인합니다.",
];

const example = `// ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint --silent 2>&1 | head -20"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date): $CLAUDE_TOOL_INPUT\" >> ~/.claude/bash.log"
          }
        ]
      }
    ]
  }
}`;

export default function HooksPage() {
  return (
    <FeatureDetail
      heading="Hooks"
      subheading="툴 이벤트 발생 시 셸 명령어를 자동으로 실행하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      icon={GiFishingHook}
    />
  );
}
