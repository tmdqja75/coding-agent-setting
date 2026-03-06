"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { GiFishingHook } from "react-icons/gi";

const description = [
  "Hooks는 Claude Code의 도구 실행 생명주기에 개입할 수 있는 이벤트 기반 자동화 시스템입니다. 셸 명령어를 특정 도구 이벤트에 연결해 코드 품질 검사, 로깅, 보안 제어를 자동화할 수 있습니다.",
  "두 가지 실행 시점을 제공합니다: PreToolUse(도구 실행 전)와 PostToolUse(도구 실행 후). PreToolUse는 사전 검증·차단에, PostToolUse는 린트·테스트·알림 같은 후처리에 적합합니다.",
  "matcher 필드로 대상 도구를 정규식으로 지정합니다. 'Edit|Write'는 파일 수정 도구 모두에 반응하고, 'Bash'는 셸 명령 실행에만 반응합니다. 하나의 이벤트에 여러 매처를 등록할 수 있습니다.",
  "훅의 표준 출력(stdout)은 Claude에게 추가 컨텍스트로 자동 전달됩니다. 린트 결과나 테스트 출력을 Claude가 즉시 인식해 다음 작업에 반영하도록 할 수 있습니다.",
  "비정상 종료 코드(exit 1)를 반환하면 해당 도구 실행을 즉시 차단합니다. 위험한 명령 패턴을 사전에 감지해 실수를 방지하는 안전망으로 활용할 수 있습니다.",
  "훅 설정은 ~/.claude/settings.json(개인) 또는 .claude/settings.json(프로젝트)에 저장됩니다. 개인 규칙과 팀 공유 규칙을 분리해 관리할 수 있습니다.",
];

const howToUse = [
  "~/.claude/settings.json 파일에 hooks 섹션을 추가합니다.",
  "실행 시점을 선택합니다: PreToolUse(도구 실행 전) 또는 PostToolUse(도구 실행 후).",
  "matcher에 감지할 도구 이름을 정규식으로 지정합니다.",
  "type: 'command'와 실행할 셸 명령을 command 필드에 작성합니다.",
  "대상 도구 동작을 수행해 훅이 자동으로 실행되는지 확인합니다.",
];

const diagram = `~/.claude/settings.json (또는 .claude/settings.json)
└── hooks
    ├── PreToolUse[]        # 도구 실행 전 훅
    │   ├── matcher         # 대상 도구 정규식 (예: "Bash")
    │   └── hooks[]
    │       ├── type: "command"
    │       └── command     # exit 1 → 실행 차단
    └── PostToolUse[]       # 도구 실행 후 훅
        ├── matcher         # 대상 도구 정규식 (예: "Edit|Write")
        └── hooks[]
            ├── type: "command"
            └── command     # stdout → Claude 컨텍스트로 전달`;

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
            "command": "echo \\"$(date): $CLAUDE_TOOL_INPUT\\" >> ~/.claude/bash.log"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '$CLAUDE_TOOL_INPUT' | grep -q 'rm -rf' && exit 1 || exit 0"
          }
        ]
      }
    ]
  }
}

# 동작 원리
# PreToolUse: exit 1 반환 → 도구 실행 차단
# PreToolUse: exit 0 반환 → 도구 실행 허용
# PostToolUse: stdout → Claude 컨텍스트에 자동 추가

# 활용 예시
# > 파일 수정 후 린트 오류를 자동으로 Claude에게 전달
# > rm -rf 감지 시 즉시 차단
# > 모든 Bash 명령을 로그 파일에 기록`;

export default function HooksPage() {
  return (
    <FeatureDetail
      heading="Hooks"
      subheading="툴 이벤트 발생 시 셸 명령어를 자동으로 실행하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      diagram={diagram}
      icon={GiFishingHook}
      accentColor="#4ade80"
      tags={["이벤트 훅", "자동화", "보안 제어", "워크플로우"]}
    />
  );
}
