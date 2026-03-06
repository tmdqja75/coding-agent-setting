"use client";

import { useRouter } from "next/navigation";
import Hero from "@/components/ui/animated-shader-hero";

export default function Home() {
  const router = useRouter();

  const handlePrimaryClick = () => {
    router.push("/setup");
  };

  const handleSecondaryClick = () => {
    router.push("/claude-code-components");
  };

  return (
    <div className="w-full">
      <Hero
        trustBadge={{
          text: "Claude Code로 만든 컴포넌트 모음",
          icons: ["✨"],
        }}
        headline={{
          line1: "Anything You Want",
          line2: "in Claude Code",
        }}
        subtitle={"Claude Code로 만들고 싶은걸 알려주면, 맞춤 MCP 서버·스킬·서브에이전트를 찾아\nClaude Code를 세팅해 줄게요."}
        buttons={{
          primary: {
            text: "Claude Code 설정 시작하기",
            onClick: handlePrimaryClick,
          },
          secondary: {
            text: "컴포넌트 둘러보기",
            onClick: handleSecondaryClick,
          },
        }}
      />
    </div>
  );
}
