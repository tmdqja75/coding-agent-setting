"use client";

import { FeatureDetail } from "@/components/ui/feature-detail";
import { FaRobot } from "react-icons/fa";

const description =
  "Subagents는 Claude Code가 복잡한 작업을 독립적인 하위 에이전트에게 위임할 수 있게 해줍니다. 각 서브에이전트는 자체 컨텍스트 창을 가지며 모든 도구를 사용할 수 있어, 서로 독립적인 작업을 병렬로 처리하는 데 적합합니다. Task 도구를 통해 에이전트 유형과 프롬프트를 지정하여 실행할 수 있습니다.";

const howToUse = [
  "큰 작업을 독립적인 하위 작업 단위로 분리합니다.",
  "각 작업에 맞는 subagent_type과 목적을 정의합니다.",
  "Task 도구로 구체적인 프롬프트를 전달해 실행합니다.",
  "에이전트 결과를 통합하고 필요한 후속 작업을 지정합니다.",
];

const example = `// CLAUDE.md 또는 프롬프트에서 Task 도구 활용
Task({
  subagent_type: "general-purpose",
  description: "API 엔드포인트 문서화",
  prompt: \`
    프로젝트의 모든 API 엔드포인트를 찾아서 문서화하세요.
    각 엔드포인트의 메서드, 경로, 파라미터를 정리해주세요.
  \`,
})

// 여러 서브에이전트를 병렬로 실행
Task({ subagent_type: "Explore", description: "프론트엔드 분석", prompt: "..." })
Task({ subagent_type: "Explore", description: "백엔드 분석",   prompt: "..." })`;

export default function SubagentsPage() {
  return (
    <FeatureDetail
      heading="Subagents"
      subheading="복잡한 작업을 전문 에이전트에게 위임하세요"
      description={description}
      howToUse={howToUse}
      example={example}
      icon={FaRobot}
    />
  );
}
