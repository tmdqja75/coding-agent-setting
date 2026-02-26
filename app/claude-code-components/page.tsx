import Link from "next/link";
import { InteractiveHoverLinks } from "@/components/ui/interactive-hover-links";
import { ArrowLeft } from "lucide-react";

export default function ClaudeCodeComponentsPage() {
  return (
    <div>
      <div className="mx-auto max-w-5xl px-8 pt-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200"
        >
          <ArrowLeft className="size-4" />
          Back to Home
        </Link>
      </div>
      <section className="mx-auto max-w-5xl px-8 pt-10">
        <p className="text-base font-semibold uppercase tracking-widest text-muted-foreground mb-4">
          How to Use
        </p>
        <ol className="list-decimal space-y-2 pl-6 text-base leading-7 text-foreground">
          <li>아래 항목 중 원하는 Claude Code 기능을 선택합니다.</li>
          <li>각 상세 페이지에서 핵심 개념과 설정 예시를 확인합니다.</li>
          <li>Example Usage를 기준으로 프로젝트 설정에 적용합니다.</li>
          <li>필요하면 이전 페이지로 돌아와 다른 기능도 이어서 학습합니다.</li>
        </ol>
      </section>
      <InteractiveHoverLinks />
    </div>
  );
}
