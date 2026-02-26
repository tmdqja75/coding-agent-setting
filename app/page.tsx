"use client";

import { useRouter } from "next/navigation";
import Hero from "@/components/ui/animated-shader-hero";

export default function Home() {
  const router = useRouter();

  const handlePrimaryClick = () => {
    router.push("/claude-code-components");
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
          line1: "클로드 코드로",
          line2: "더 빠르게 개발하기",
        }}
        subtitle="AI 기반 코드 자동화와 컴포넌트로 다음 세대 개발 워크플로우를 경험하세요."
        buttons={{
          primary: {
            text: "클로드 코드 컴포넌트 설명",
            onClick: handlePrimaryClick,
          },
          secondary: {
            text: "클로드 코드 세팅하기",
            onClick: handleSecondaryClick,
          },
        }}
      />
    </div>
  );
}
