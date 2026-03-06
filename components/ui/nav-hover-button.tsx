"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

interface NavHoverButtonProps {
  href: string;
  label: string;
  accentColor?: string;
}

export function NavHoverButton({
  href,
  label,
  accentColor = "#f0ebe0",
}: NavHoverButtonProps) {
  return (
    <Link href={href} style={{ textDecoration: "none" }}>
      <div
        className="group"
        style={{
          position: "relative",
          display: "inline-flex",
          alignItems: "center",
          cursor: "pointer",
          padding: "0.75rem 2rem",
          border: "2px solid #f0ebe0",
          borderRadius: "9999px",
          overflow: "hidden",
          fontFamily: "'Courier New', monospace",
          fontSize: "0.85rem",
          letterSpacing: "0.25em",
          textTransform: "uppercase",
        }}
      >
        {/* Normal state */}
        <span
          className="translate-y-0 group-hover:-translate-y-12 group-hover:opacity-0 transition-all duration-300 inline-flex items-center gap-2"
          style={{ color: "#8a8278" }}
        >
          <ArrowLeft style={{ width: "1rem", height: "1rem" }} />
          {label}
        </span>

        {/* Hover overlay */}
        <div
          className="flex gap-2 items-center absolute inset-0 justify-center translate-y-12 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 rounded-full group-hover:rounded-none"
          style={{ background: accentColor, color: "#080808" }}
        >
          <ArrowLeft style={{ width: "1rem", height: "1rem" }} />
          <span>{label}</span>
        </div>
      </div>
    </Link>
  );
}
