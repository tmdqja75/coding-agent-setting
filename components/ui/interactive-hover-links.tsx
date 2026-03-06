"use client";

import {
  useMotionValue,
  motion,
  useSpring,
  useTransform,
} from "motion/react";
import React, { useRef } from "react";
import { ArrowUpRight } from "lucide-react";
import { TbPlugConnected } from "react-icons/tb";
import { FaRobot } from "react-icons/fa";
import { GiFishingHook } from "react-icons/gi";
import { BsStars } from "react-icons/bs";

interface InteractiveHoverLinksProps {
  links?: typeof INTERACTIVE_LINKS;
}

export function InteractiveHoverLinks({
  links = INTERACTIVE_LINKS,
}: InteractiveHoverLinksProps) {
  return (
    <section style={{ width: "100%", padding: "0 2rem 6rem" }}>
      <div style={{ margin: "0 auto", maxWidth: "72rem" }}>
        {links.map((link, i) => (
          <HoverLink key={link.heading} {...link} index={i} />
        ))}
      </div>
    </section>
  );
}

interface LinkProps {
  heading: string;
  icon: React.ElementType;
  subheading: string;
  href: string;
  accentColor: string;
  index: number;
}

function HoverLink({
  heading,
  icon: Icon,
  subheading,
  href,
  accentColor,
  index,
}: LinkProps) {
  const ref = useRef<HTMLAnchorElement | null>(null);

  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseXSpring = useSpring(x, { stiffness: 200, damping: 30 });
  const mouseYSpring = useSpring(y, { stiffness: 200, damping: 30 });

  const top = useTransform(mouseYSpring, [0.5, -0.5], ["40%", "60%"]);
  const left = useTransform(mouseXSpring, [0.5, -0.5], ["60%", "40%"]);

  const handleMouseMove = (
    e: React.MouseEvent<HTMLAnchorElement, MouseEvent>
  ) => {
    const rect = ref.current!.getBoundingClientRect();
    const xPct = (e.clientX - rect.left) / rect.width - 0.5;
    const yPct = (e.clientY - rect.top) / rect.height - 0.5;
    x.set(xPct);
    y.set(yPct);
  };

  return (
    <motion.a
      href={href}
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => {
        x.set(0);
        y.set(0);
      }}
      initial="initial"
      whileHover="whileHover"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid #141414",
        padding: "2.25rem 0",
        position: "relative",
        textDecoration: "none",
      }}
    >
      {/* Index label */}
      <motion.span
        variants={{
          initial: { opacity: 0.25 },
          whileHover: { opacity: 1, color: accentColor },
        }}
        style={{
          fontFamily: "'Courier New', monospace",
          fontSize: "2rem",
          letterSpacing: "0.2em",
          color: "#3a3530",
          marginRight: "2rem",
          flexShrink: 0,
          display: "none",
          paddingTop: "0.3rem",
          transition: "color 0.3s",
        }}
        className="index-label"
      >
        {String(index + 1).padStart(2, "0")}
      </motion.span>

      <style>{`
        @media (min-width: 640px) {
          .index-label { display: block !important; }
        }
      `}</style>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Heading */}
        <motion.span
          variants={{
            initial: { x: 0 },
            whileHover: { x: -16 },
          }}
          transition={{
            type: "spring",
            staggerChildren: 0.04,
            delayChildren: 0.1,
          }}
          style={{
            display: "block",
            fontFamily: "'Georgia', 'Palatino Linotype', Palatino, serif",
            fontSize: "clamp(2.25rem, 5.5vw, 4.5rem)",
            fontWeight: 700,
            lineHeight: 0.95,
            letterSpacing: "-0.025em",
          }}
        >
          {heading.split("").map((l, i) => (
            <motion.span
              variants={{
                initial: { x: 0, color: "#7a7270" },
                whileHover: { x: 16, color: "#f0ebe0" },
              }}
              transition={{ type: "spring", damping: 20 }}
              style={{ display: "inline-block" }}
              key={i}
            >
              {l === " " ? "\u00a0" : l}
            </motion.span>
          ))}
        </motion.span>

        {/* Subheading */}
        <motion.span
          variants={{
            initial: { opacity: 1, x: 0 },
            whileHover: { opacity: 0.65, x: -16 },
          }}
          transition={{ type: "spring", damping: 25 }}
          style={{
            display: "block",
            marginTop: "0.5rem",
            fontSize: "1rem",
            color: "#9a9290",
            letterSpacing: "0.01em",
            fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
          }}
        >
          {subheading}
        </motion.span>
      </div>

      {/* Floating card */}
      <motion.div
        style={{
          top,
          left,
          translateX: "-50%",
          translateY: "-50%",
          position: "absolute",
          zIndex: 50,
          pointerEvents: "none",
        }}
        variants={{
          initial: { scale: 0, rotate: "-12.5deg", opacity: 0 },
          whileHover: { scale: 1, rotate: "12.5deg", opacity: 1 },
        }}
        transition={{ type: "spring", damping: 18, stiffness: 200 }}
      >
        <div
          style={{
            width: "9rem",
            height: "11rem",
            borderRadius: "1.25rem",
            background: "#ffffff",
            border: "1px solid #e8e8e8",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 24px 64px rgba(255,255,255,0.12)",
          }}
        >
          <Icon style={{ fontSize: "3rem", color: "#111" }} />
        </div>
      </motion.div>

      {/* Arrow */}
      <div style={{ overflow: "hidden", flexShrink: 0, marginLeft: "1rem" }}>
        <motion.div
          variants={{
            initial: { x: "110%", opacity: 0 },
            whileHover: { x: "0%", opacity: 1 },
          }}
          transition={{ type: "spring", damping: 22 }}
          style={{ position: "relative", zIndex: 10, padding: "0.5rem" }}
        >
          <ArrowUpRight
            style={{ width: "1.25rem", height: "1.25rem", color: accentColor }}
          />
        </motion.div>
      </div>
    </motion.a>
  );
}

export const INTERACTIVE_LINKS = [
  {
    heading: "MCP",
    subheading: "Claude를 외부 도구 및 데이터 소스에 연결하세요",
    icon: TbPlugConnected,
    href: "/claude-code-components/mcp",
    accentColor: "#22d3ee",
  },
  {
    heading: "Subagents",
    subheading: "복잡한 작업을 전문 에이전트에게 위임하세요",
    icon: FaRobot,
    href: "/claude-code-components/subagents",
    accentColor: "#f97316",
  },
  {
    heading: "Hooks",
    subheading: "툴 이벤트 발생 시 셸 명령어를 자동으로 실행하세요",
    icon: GiFishingHook,
    href: "/claude-code-components/hooks",
    accentColor: "#4ade80",
  },
  {
    heading: "Skills",
    subheading: "재사용 가능한 슬래시 명령어로 Claude Code를 확장하세요",
    icon: BsStars,
    href: "/claude-code-components/skills",
    accentColor: "#a78bfa",
  },
];
