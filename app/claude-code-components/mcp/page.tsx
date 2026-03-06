"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { TbPlugConnected } from "react-icons/tb";

const description = [
  "MCP(Model Context Protocol)는 Anthropic이 설계한 개방형 표준으로, Claude Code가 수백 개의 외부 도구 및 데이터 소스에 연결할 수 있도록 합니다. JIRA에서 기능 구현, Sentry로 오류 분석, PostgreSQL 쿼리, GitHub PR 생성 등 복잡한 크로스 시스템 워크플로우를 단일 대화에서 처리할 수 있습니다.",
  "세 가지 전송 방식을 지원합니다: HTTP(원격 서버 권장), SSE(레거시), stdio(로컬 프로세스). `claude mcp add` 명령 하나로 서버를 연결하며, OAuth 2.0 인증이 필요한 원격 서버는 `/mcp` 명령으로 안전하게 로그인합니다.",
  "세 가지 범위로 서버를 관리합니다: local(기본값, 현재 프로젝트 전용), project(.mcp.json으로 팀 공유, 버전 관리 가능), user(모든 프로젝트에서 사용). 동일한 이름의 서버가 여러 범위에 존재하면 local > project > user 순으로 우선합니다.",
  ".mcp.json의 env 필드에서 `${VAR}` 또는 `${VAR:-default}` 구문으로 환경 변수를 확장할 수 있어, API 키 같은 민감한 값을 코드에 직접 노출하지 않고 팀과 구성을 공유할 수 있습니다.",
  "MCP 서버는 동적으로 도구 목록을 업데이트할 수 있습니다. 서버가 `list_changed` 알림을 보내면 Claude Code가 재연결 없이 자동으로 새로운 도구를 인식합니다.",
];

const howToUse = [
  "HTTP 서버 추가: `claude mcp add --transport http <name> <url>`",
  "로컬 stdio 서버 추가: `claude mcp add --transport stdio <name> -- <command> [args]`",
  "`--scope project` 플래그로 .mcp.json에 저장해 팀 전체와 공유합니다.",
  "OAuth 인증이 필요한 서버는 `/mcp` 명령으로 브라우저 로그인 흐름을 진행합니다.",
  "`claude mcp list`로 연결 상태를 확인하고, Claude Code 내에서 `/mcp`로 서버 상태를 점검합니다.",
];

const diagram = `# 범위별 저장 위치
local   → ~/.claude.json        (현재 프로젝트, 기본값, 비공개)
project → .mcp.json             (팀 공유, 버전 관리 권장)
user    → ~/.claude.json        (모든 프로젝트, 개인 전용)

# 우선순위: local > project > user`;

const example = `# HTTP 서버 추가 (권장)
claude mcp add --transport http notion https://mcp.notion.com/mcp

# OAuth 인증 (Claude Code 내에서)
> /mcp   # "Authenticate" 선택 후 브라우저 로그인

# 팀과 공유할 프로젝트 범위 서버 추가
claude mcp add --transport http github \\
  --scope project https://api.githubcopilot.com/mcp/

# .mcp.json — 환경 변수 확장 활용
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "\${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer \${API_KEY}"
      }
    }
  }
}

# stdio 서버 추가 (로컬 프로세스)
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \\
  --dsn "postgresql://localhost/mydb"

# 서버 관리
claude mcp list              # 연결된 서버 목록
claude mcp get github        # 특정 서버 상세 정보
claude mcp remove github     # 서버 제거`;

export default function McpPage() {
  return (
    <FeatureDetail
      heading="MCP"
      subheading="Claude Code를 수백 개의 외부 도구와 데이터 소스에 연결하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      diagram={diagram}
      icon={TbPlugConnected}
      accentColor="#22d3ee"
      tags={["외부 연동", "OAuth 인증", "팀 공유", "로컬·원격"]}
    />
  );
}
