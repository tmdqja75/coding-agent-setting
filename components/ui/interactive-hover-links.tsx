"use client";

import { useMotionValue, motion, useSpring, useTransform } from "motion/react";
import React, { useRef } from "react";
import { ArrowRight } from "lucide-react";
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
    <section className="bg-background p-4 md:px-8 md:py-16 w-full">
      <div className="mx-auto max-w-5xl">
        {links.map((link) => (
          <Link key={link.heading} {...link} />
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
}

function Link({ heading, icon: Icon, subheading, href }: LinkProps) {
  const ref = useRef<HTMLAnchorElement | null>(null);

  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseXSpring = useSpring(x);
  const mouseYSpring = useSpring(y);

  const top = useTransform(mouseYSpring, [0.5, -0.5], ["40%", "60%"]);
  const left = useTransform(mouseXSpring, [0.5, -0.5], ["60%", "40%"]);

  const handleMouseMove = (
    e: React.MouseEvent<HTMLAnchorElement, MouseEvent>
  ) => {
    const rect = ref.current!.getBoundingClientRect();

    const width = rect.width;
    const height = rect.height;

    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const xPct = mouseX / width - 0.5;
    const yPct = mouseY / height - 0.5;

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
      className="group relative flex items-center justify-between border-b-2 border-muted py-4 transition-all duration-500 hover:border-foreground  md:py-8"
    >
      <div>
        <motion.span
          variants={{
            initial: { x: 0 },
            whileHover: { x: -16 },
          }}
          transition={{
            type: "spring",
            staggerChildren: 0.075,
            delayChildren: 0.25,
          }}
          className="relative z-10 block text-4xl font-bold text-muted-foreground transition-colors duration-500 group-hover:text-foreground md:text-6xl"
        >
          {heading.split("").map((l, i) => (
            <motion.span
              variants={{
                initial: { x: 0 },
                whileHover: { x: 16 },
              }}
              transition={{ type: "spring" }}
              className="inline-block"
              key={i}
            >
              {l}
            </motion.span>
          ))}
        </motion.span>
        <span className="relative z-10 mt-2 block text-base text-muted-foreground transition-colors duration-500 group-hover:text-foreground">
          {subheading}
        </span>
      </div>

      <motion.div
        style={{
          top,
          left,
          translateX: "-10%",
          translateY: "-50%",
        }}
        variants={{
          initial: { scale: 0, rotate: "-12.5deg" },
          whileHover: { scale: 1, rotate: "12.5deg" },
        }}
        transition={{ type: "spring" }}
        className="absolute z-0 flex h-24 w-32 items-center justify-center rounded-3xl bg-foreground shadow-lg md:h-48 md:w-64"
      >
        <Icon className="text-background size-12 md:size-20" />
      </motion.div>

      <div className="overflow-hidden">
        <motion.div
          variants={{
            initial: { x: "100%", opacity: 0 },
            whileHover: { x: "0%", opacity: 1 },
          }}
          transition={{ type: "spring" }}
          className="relative z-10 p-4"
        >
          <ArrowRight className="size-8 text-foreground md:size-12" />
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
  },
  {
    heading: "Subagents",
    subheading: "복잡한 작업을 전문 에이전트에게 위임하세요",
    icon: FaRobot,
    href: "/claude-code-components/subagents",
  },
  {
    heading: "Hooks",
    subheading: "툴 이벤트 발생 시 셸 명령어를 자동으로 실행하세요",
    icon: GiFishingHook,
    href: "/claude-code-components/hooks",
  },
  {
    heading: "Skills",
    subheading: "재사용 가능한 슬래시 명령어로 Claude Code를 확장하세요",
    icon: BsStars,
    href: "/claude-code-components/skills",
  },
];
