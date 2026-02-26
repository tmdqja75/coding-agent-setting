"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { motion } from "motion/react";
import React from "react";

interface FeatureDetailProps {
  heading: string;
  subheading: string;
  description: string;
  howToUse: string[];
  example: string;
  icon: React.ElementType;
}

export function FeatureDetail({
  heading,
  subheading,
  description,
  howToUse,
  example,
  icon: Icon,
}: FeatureDetailProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-5xl px-8 pt-8">
        <Link
          href="/claude-code-components"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200"
        >
          <ArrowLeft className="size-4" />
          Back
        </Link>
      </div>

      <div className="mx-auto max-w-5xl px-8 py-16 flex items-start gap-16">
        <div className="flex-1">
          <h1 className="text-4xl font-bold text-foreground md:text-6xl">
            {heading}
          </h1>
          <p className="mt-2 text-base text-muted-foreground">{subheading}</p>

          <p className="mt-10 text-lg leading-8 text-foreground">{description}</p>

          <div className="mt-10">
            <p className="text-base font-semibold uppercase tracking-widest text-muted-foreground mb-4">
              How to Use
            </p>
            <ol className="list-decimal space-y-2 pl-6 text-base leading-7 text-foreground">
              {howToUse.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="mt-10">
            <p className="text-base font-semibold uppercase tracking-widest text-muted-foreground mb-4">
              Example Usage
            </p>
            <pre className="rounded-3xl bg-muted p-6 text-sm leading-6 overflow-x-auto">
              <code>{example}</code>
            </pre>
          </div>
        </div>

        <div className="hidden md:flex shrink-0 items-start justify-center pt-4">
          <motion.div
            animate={{ y: [0, -14, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            style={{ rotate: 12.5 }}
            className="flex h-48 w-40 items-center justify-center rounded-3xl bg-foreground shadow-lg"
          >
            <Icon className="size-20 text-background" />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
