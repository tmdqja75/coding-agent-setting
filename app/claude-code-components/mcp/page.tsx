"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { TbPlugConnected } from "react-icons/tb";

const description =
  "MCP(Model Context Protocol)는 Claude가 외부 도구, API, 데이터 소스에 표준화된 방식으로 연결할 수 있게 해주는 오픈 프로토콜입니다. 프로젝트에 MCP 서버를 설정하면 Claude의 기본 기능을 넘어 파일 시스템, GitHub, 데이터베이스 등 다양한 외부 서비스와 상호작용할 수 있습니다.";

const howToUse = [
  "프로젝트 루트에 .mcp.json 파일을 생성합니다.",
  "연결할 MCP 서버의 command, args, env를 정의합니다.",
  "필요한 인증 토큰과 접근 권한을 안전하게 설정합니다.",
  "Claude에서 MCP 도구를 호출해 연결 상태를 검증합니다.",
];

const example = `// .mcp.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./src"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}`;

export default function McpPage() {
  return (
    <FeatureDetail
      heading="MCP"
      subheading="Claude를 외부 도구 및 데이터 소스에 연결하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      icon={TbPlugConnected}
    />
  );
}
