import { InteractiveHoverLinks } from "@/components/ui/interactive-hover-links";
import { NavHoverButton } from "@/components/ui/nav-hover-button";

const steps = [
  { n: "01", text: "원하는 Claude Code 기능을 선택합니다" },
  { n: "02", text: "핵심 개념과 설정 예시를 확인합니다" },
  { n: "03", text: "Example Usage를 프로젝트에 적용합니다" },
  { n: "04", text: "필요하면 다른 기능도 이어서 학습합니다" },
];

export default function ClaudeCodeComponentsPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#080808",
        color: "#f0ebe0",
        fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
      }}
    >
      {/* Top rule */}
      <div style={{ height: "1px", background: "#161616" }} />

      {/* Nav */}
      <div
        style={{
          maxWidth: "72rem",
          margin: "0 auto",
          padding: "2rem 2rem 0",
        }}
      >
        <NavHoverButton href="/" label="홈" />
      </div>

      {/* Hero */}
      <section
        style={{
          maxWidth: "72rem",
          margin: "0 auto",
          padding: "5rem 2rem 4rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: "3rem",
            flexWrap: "wrap",
            paddingBottom: "4rem",
            borderBottom: "1px solid #161616",
          }}
        >
          {/* Left: title */}
          <div>
            <p
              style={{
                fontFamily: "'Courier New', monospace",
                fontSize: "0.62rem",
                letterSpacing: "0.3em",
                textTransform: "uppercase",
                color: "#7a7470",
                marginBottom: "1.5rem",
              }}
            >
              Claude Code // 핵심 구성요소
            </p>
            <h1
              style={{
                fontFamily:
                  "'Helvetica Neue', Helvetica, Arial, sans-serif",
                fontSize: "clamp(2.75rem, 7vw, 5rem)",
                fontWeight: 700,
                lineHeight: 0.92,
                letterSpacing: "-0.025em",
                color: "#f0ebe0",
                maxWidth: "18ch",
                margin: 0,
              }}
            >
              Claude Code 구성요소
              <br />
              
            </h1>
          </div>

          {/* Right: intro */}
          <p
            style={{
              maxWidth: "rem",
              fontSize: "1.5rem",
              lineHeight: "1.75",
              color: "#a09890",
              margin: 0,
            }}
          >
            Claude Code는 네 가지 핵심 구성요소를 통해 확장됩니다.
            각 기능을 통해 Claude Code의 역량을 더욱 강력하게 활용하세요.
          </p>
        </div>
      </section>

      {/* Steps grid */}
      <section
        style={{
          maxWidth: "72rem",
          margin: "0 auto",
          padding: "0 2rem 4rem",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "0",
          }}
          className="steps-grid"
        >
          <style>{`
            @media (min-width: 768px) {
              .steps-grid { grid-template-columns: repeat(4, 1fr) !important; }
            }
          `}</style>
          {steps.map(({ n, text }) => (
            <div
              key={n}
              style={{
                padding: "1.5rem 1.5rem 1.5rem 0",
                borderTop: "1px solid #161616",
              }}
            >
              <span
                style={{
                  fontFamily: "'Courier New', monospace",
                  fontSize: "1rem",
                  color: "#7a7470",
                  letterSpacing: "0.15em",
                  display: "block",
                }}
              >
                {n}
              </span>
              <p
                style={{
                  marginTop: "1rem",
                  fontSize: "0.82rem",
                  color: "#b0a898",
                  lineHeight: "1.55",
                }}
              >
                {text}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Feature links */}
      <InteractiveHoverLinks />
    </div>
  );
}
