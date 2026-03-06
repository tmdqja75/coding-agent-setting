"use client";

import { motion } from "motion/react";
import React from "react";
import { NavHoverButton } from "@/components/ui/nav-hover-button";

function renderCodeWithFrontmatter(code: string, accentColor: string) {
  const match = code.match(/^([\s\S]*?)(---\n[\s\S]*?\n---)([\s\S]*)$/);
  if (!match) {
    return <code style={{ color: `${accentColor}ee` }}>{code}</code>;
  }
  const [, preamble, frontmatter, body] = match;
  return (
    <>
      {preamble && <span style={{ color: "#6a6460" }}>{preamble}</span>}
      <span style={{ color: "#fcd34d" }}>{frontmatter}</span>
      <span style={{ color: `${accentColor}ee` }}>{body}</span>
    </>
  );
}

interface FeatureDetailProps {
  heading: string;
  subheading: string;
  description: string | string[];
  howToUse: string[];
  example: string;
  diagram?: string;
  icon: React.ElementType;
  accentColor?: string;
  tags?: string[];
}

export function FeatureDetail({
  heading,
  subheading,
  description,
  howToUse,
  example,
  diagram,
  icon: Icon,
  accentColor = "#22d3ee",
  tags = [],
}: FeatureDetailProps) {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#080808",
        color: "#f0ebe0",
        fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
      }}
    >
      {/* Accent bar */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        style={{
          height: "2px",
          background: `linear-gradient(to right, ${accentColor}, ${accentColor}00)`,
          transformOrigin: "left",
        }}
      />

      {/* Nav */}
      <div style={{ maxWidth: "72rem", margin: "0 auto", padding: "2rem 2rem 0" }}>
        <NavHoverButton
          href="/claude-code-components"
          label="구성요소"
          accentColor={accentColor}
        />
      </div>

      {/* Hero */}
      <header
        style={{
          maxWidth: "72rem",
          margin: "0 auto",
          padding: "3.5rem 2rem 3rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "3rem",
          }}
        >
          {/* Left: text */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              style={{
                fontFamily: "'Courier New', monospace",
                fontSize: "0.62rem",
                letterSpacing: "0.3em",
                textTransform: "uppercase",
                color: accentColor,
                marginBottom: "1.25rem",
              }}
            >
              Claude Code — 구성요소
            </motion.p>

            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
              style={{
                fontFamily: "'Georgia', 'Palatino Linotype', Palatino, serif",
                fontSize: "clamp(3.5rem, 10vw, 6.5rem)",
                fontWeight: 700,
                lineHeight: 0.88,
                letterSpacing: "-0.025em",
                color: "#f0ebe0",
                margin: 0,
              }}
            >
              {heading}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.6 }}
              style={{
                marginTop: "1.75rem",
                fontSize: "1.2rem",
                color: "#a09890",
                letterSpacing: "0.01em",
                maxWidth: "36rem",
                lineHeight: "1.65",
              }}
            >
              {subheading}
            </motion.p>

            {tags.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.45, duration: 0.5 }}
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.5rem",
                  marginTop: "1.5rem",
                }}
              >
                {tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      fontFamily: "'Courier New', monospace",
                      fontSize: "0.6rem",
                      letterSpacing: "0.15em",
                      textTransform: "uppercase",
                      padding: "0.25rem 0.65rem",
                      border: `1px solid ${accentColor}44`,
                      color: accentColor,
                      borderRadius: "2px",
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </motion.div>
            )}
          </div>

          {/* Right: floating icon */}
          <motion.div
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            style={{ flexShrink: 0, display: "none", perspective: "600px" }}
            className="md-icon-wrapper"
          >
            <div style={{ transform: "rotate(10deg)" }}>
              <motion.div
                animate={{ y: [0, -12, 0], rotateY: [0, 360] }}
                transition={{
                  y: { duration: 3.5, repeat: Infinity, ease: "easeInOut" },
                  rotateY: { duration: 6, repeat: Infinity, ease: "linear" },
                }}
              >
                <div
                  style={{
                    width: "12rem",
                    height: "15rem",
                    borderRadius: "1.25rem",
                    background: `linear-gradient(145deg, ${accentColor}18, ${accentColor}08)`,
                    border: `1px solid ${accentColor}30`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: `0 20px 60px ${accentColor}12`,
                  }}
                >
                  <Icon style={{ fontSize: "4rem", color: accentColor }} />
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* md+ icon shown via class */}
          <style>{`
            @media (min-width: 768px) {
              .md-icon-wrapper { display: block !important; }
            }
          `}</style>
        </div>

        <div style={{ height: "1px", background: "#161616", marginTop: "3rem" }} />
      </header>

      {/* Content */}
      <main
        style={{ maxWidth: "72rem", margin: "0 auto", padding: "0 2rem 6rem" }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: "3rem",
          }}
          className="content-grid"
        >
          <style>{`
            @media (min-width: 1024px) {
              .content-grid { grid-template-columns: 1fr 1fr !important; }
            }
          `}</style>

          {/* Left: description + steps */}
          <div style={{ display: "flex", flexDirection: "column", gap: "3rem", minWidth: 0 }} suppressHydrationWarning>
            {/* Description */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              style={{
                borderLeft: `2px solid ${accentColor}`,
                paddingLeft: "1.5rem",
                margin: 0,
              }}
            >
              {Array.isArray(description) ? (
                <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                  {description.map((point, i) => (
                    <li key={i} style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                      <span style={{ color: accentColor, opacity: 0.7, flexShrink: 0, paddingTop: "0.35rem", fontSize: "0.55rem" }}>▶</span>
                      <span style={{ fontSize: "1.15rem", lineHeight: "1.85", color: "#ddd7cd", fontWeight: 400, letterSpacing: "0.01em" }}>{point}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: "1.3rem", lineHeight: "1.95", color: "#ddd7cd", fontWeight: 400, letterSpacing: "0.01em", margin: 0 }}>
                  {description}
                </p>
              )}
            </motion.div>

            {/* Steps */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
            >
              <p
                style={{
                  fontFamily: "'Courier New', monospace",
                  fontSize: "2rem",
                  letterSpacing: "0.3em",
                  textTransform: "uppercase",
                  color: "#6a6460",
                  marginBottom: "1.25rem",
                  paddingBottom: "0.75rem",
                  borderBottom: "1px solid #222",
                }}
              >
                사용 방법
              </p>

              <ol style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {howToUse.map((step, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + i * 0.08, duration: 0.5 }}
                    style={{
                      display: "flex",
                      gap: "2rem",
                      alignItems: "flex-start",
                      padding: "1rem 0",
                      borderBottom: "1px solid #111",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "'Courier New', monospace",
                        fontSize: "0.62rem",
                        color: accentColor,
                        opacity: 0.7,
                        minWidth: "1.5rem",
                        paddingTop: "0.2rem",
                        flexShrink: 0,
                      }}
                    >
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span
                      style={{
                        fontSize: "1.1rem",
                        color: "#c8c0b8",
                        lineHeight: "1.7",
                        letterSpacing: "0.01em",
                      }}
                    >
                      {step}
                    </span>
                  </motion.li>
                ))}
              </ol>
            </motion.div>
          </div>

          {/* Right: diagram + code */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.55, duration: 0.6 }}
            style={{ display: "flex", flexDirection: "column", gap: "2rem", minWidth: 0 }}
            suppressHydrationWarning
          >
            {/* Directory tree diagram */}
            {diagram && (
              <div>
                <p
                  style={{
                    fontFamily: "'Courier New', monospace",
                    fontSize: "2rem",
                    letterSpacing: "0.3em",
                    textTransform: "uppercase",
                    color: "#6a6460",
                    marginBottom: "1rem",
                    paddingBottom: "0.75rem",
                    borderBottom: "1px solid #222",
                  }}
                >
                  디렉터리 구조
                </p>
                <div
                  style={{
                    borderRadius: "0.625rem",
                    overflow: "hidden",
                    border: `1px solid ${accentColor}22`,
                  }}
                >
                  <div
                    style={{
                      background: "#0f0f0f",
                      padding: "0.6rem 1rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      borderBottom: `1px solid ${accentColor}18`,
                    }}
                  >
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#2a2520" }} />
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#2a2520" }} />
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#2a2520" }} />
                    <span
                      style={{
                        fontFamily: "'Courier New', monospace",
                        fontSize: "0.58rem",
                        color: `${accentColor}66`,
                        marginLeft: "0.75rem",
                        letterSpacing: "0.15em",
                        textTransform: "uppercase",
                      }}
                    >
                      structure
                    </span>
                  </div>
                  <pre
                    style={{
                      background: `${accentColor}06`,
                      padding: "1.25rem 1.5rem",
                      fontSize: "0.875rem",
                      lineHeight: "1.85",
                      color: `${accentColor}cc`,
                      overflowX: "auto",
                      margin: 0,
                      fontFamily: "'Courier New', 'Courier', monospace",
                    }}
                  >
                    <code style={{ color: `${accentColor}cc` }}>{diagram}</code>
                  </pre>
                </div>
              </div>
            )}

            {/* Code example */}
            <div>
              <p
                style={{
                  fontFamily: "'Courier New', monospace",
                  fontSize: "2rem",
                  letterSpacing: "0.3em",
                  textTransform: "uppercase",
                  color: "#6a6460",
                  marginBottom: "1rem",
                  paddingBottom: "0.75rem",
                  borderBottom: "1px solid #222",
                }}
              >
                예시
              </p>

              <div
                style={{
                  borderRadius: "0.625rem",
                  overflow: "hidden",
                  border: "1px solid #1a1a1a",
                }}
              >
                {/* Title bar */}
                <div
                  style={{
                    background: "#0f0f0f",
                    padding: "0.6rem 1rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                    borderBottom: "1px solid #1a1a1a",
                  }}
                >
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#2a2520" }} />
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#2a2520" }} />
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#2a2520" }} />
                  <span
                    style={{
                      fontFamily: "'Courier New', monospace",
                      fontSize: "0.58rem",
                      color: "#3a3530",
                      marginLeft: "0.75rem",
                      letterSpacing: "0.15em",
                      textTransform: "uppercase",
                    }}
                  >
                    config
                  </span>
                </div>

                {/* Code body */}
                <pre
                  style={{
                    background: "#060606",
                    padding: "1.25rem 1.5rem",
                    fontSize: "0.875rem",
                    lineHeight: "1.85",
                    color: `${accentColor}ee`,
                    overflowX: "auto",
                    margin: 0,
                    fontFamily: "'Courier New', 'Courier', monospace",
                    maxHeight: "36rem",
                  }}
                >
                  {renderCodeWithFrontmatter(example, accentColor)}
                </pre>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
