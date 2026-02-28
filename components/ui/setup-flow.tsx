"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import Link from "next/link";
import { ArrowLeft, Download, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://localhost:8000";

type Status = "idle" | "loading" | "questioning" | "building" | "done" | "error";

interface QAPair {
  question: string;
  answer: string;
}

export function SetupFlow() {
  const [threadId] = useState(() => crypto.randomUUID());
  const [status, setStatus] = useState<Status>("idle");
  const [pairs, setPairs] = useState<QAPair[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [pairs, currentQuestion, status]);

  // Auto-focus textarea when a question appears
  useEffect(() => {
    if (status === "questioning" || status === "idle") {
      textareaRef.current?.focus();
    }
  }, [status, currentQuestion]);

  const sendMessage = async (message: string) => {
    setStatus("loading");
    setInput("");

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, message }),
      });

      if (!res.ok) throw new Error(`서버 오류: ${res.status}`);
      const data: { type: "question" | "ready"; text: string } = await res.json();

      if (data.type === "question") {
        if (currentQuestion) {
          setPairs((prev) => [...prev, { question: currentQuestion, answer: message }]);
        }
        setCurrentQuestion(data.text);
        setStatus("questioning");
      } else {
        if (currentQuestion) {
          setPairs((prev) => [...prev, { question: currentQuestion, answer: message }]);
        }
        setCurrentQuestion(null);
        setStatus("building");
        await triggerDownload();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "오류가 발생했습니다.");
      setStatus("error");
    }
  };

  const triggerDownload = async () => {
    try {
      const res = await fetch(`${API_BASE}/download/${threadId}`);
      if (!res.ok) throw new Error("다운로드 준비 중 오류가 발생했습니다.");
      const blob = await res.blob();
      setDownloadUrl(URL.createObjectURL(blob));
      setStatus("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "다운로드 오류");
      setStatus("error");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || status === "loading") return;
    sendMessage(input.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Back nav */}
      <div className="mx-auto max-w-2xl px-8 pt-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200 text-sm"
        >
          <ArrowLeft className="size-4" />
          홈으로
        </Link>
      </div>

      <div className="mx-auto max-w-2xl px-8 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-12"
        >
          <h1 className="text-4xl font-bold text-foreground md:text-5xl">
            Claude Code 세팅
          </h1>
          <p className="mt-3 text-base text-muted-foreground">
            프로젝트를 알려주시면 맞춤 설정 파일을 생성해드립니다.
          </p>
        </motion.div>

        {/* Conversation thread */}
        <div className="space-y-8 mb-10">
          <AnimatePresence initial={false}>
            {pairs.map((pair, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-3"
              >
                {/* Question bubble */}
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 shrink-0 size-6 rounded-full bg-foreground flex items-center justify-center">
                    <span className="text-background text-[10px] font-bold">AI</span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed pt-0.5">
                    {pair.question}
                  </p>
                </div>
                {/* Answer bubble */}
                <div className="flex items-start gap-3 pl-9">
                  <p className="text-sm text-foreground leading-relaxed bg-muted rounded-2xl px-4 py-3">
                    {pair.answer}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Active area */}
        <AnimatePresence mode="wait">
          {(status === "idle" || status === "questioning") && (
            <motion.div
              key="input-area"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3 }}
            >
              {/* Current question */}
              <div className="flex items-start gap-3 mb-6">
                <div className="mt-0.5 shrink-0 size-6 rounded-full bg-foreground flex items-center justify-center">
                  <span className="text-background text-[10px] font-bold">AI</span>
                </div>
                <p className="text-base text-foreground leading-relaxed pt-0.5">
                  {currentQuestion ?? "만들고 싶은 프로젝트를 알려주세요."}
                </p>
              </div>

              {/* Input form */}
              <form onSubmit={handleSubmit} className="pl-9">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={3}
                  className="w-full rounded-2xl border border-muted bg-muted/50 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground resize-none transition-colors"
                  placeholder="여기에 입력하세요... (Enter로 전송)"
                />
                <div className="flex items-center justify-between mt-3">
                  <p className="text-xs text-muted-foreground">
                    Shift+Enter로 줄바꿈
                  </p>
                  <button
                    type="submit"
                    disabled={!input.trim()}
                    className="rounded-2xl bg-foreground px-5 py-2 text-sm font-semibold text-background transition-opacity disabled:opacity-30 hover:opacity-80"
                  >
                    {status === "idle" ? "시작하기" : "답변하기"}
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {status === "loading" && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 pl-0"
            >
              <div className="shrink-0 size-6 rounded-full bg-foreground flex items-center justify-center">
                <span className="text-background text-[10px] font-bold">AI</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <Loader2 className="size-4 animate-spin" />
                <span>생각하는 중...</span>
              </div>
            </motion.div>
          )}

          {status === "building" && (
            <motion.div
              key="building"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3"
            >
              <div className="shrink-0 size-6 rounded-full bg-foreground flex items-center justify-center">
                <span className="text-background text-[10px] font-bold">AI</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <Loader2 className="size-4 animate-spin" />
                <span>설정 파일을 생성 중입니다...</span>
              </div>
            </motion.div>
          )}

          {status === "done" && downloadUrl && (
            <motion.div
              key="done"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="space-y-4"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0 size-6 rounded-full bg-foreground flex items-center justify-center">
                  <span className="text-background text-[10px] font-bold">AI</span>
                </div>
                <p className="text-base text-foreground pt-0.5">
                  설정이 완료되었습니다. 아래에서 다운로드하세요.
                </p>
              </div>
              <div className="pl-9">
                <a
                  href={downloadUrl}
                  download="claude-code-setup.zip"
                  className="inline-flex items-center gap-2 rounded-2xl bg-foreground px-6 py-3 text-sm font-semibold text-background hover:opacity-80 transition-opacity"
                >
                  <Download className="size-4" />
                  claude-code-setup.zip 다운로드
                </a>
              </div>
            </motion.div>
          )}

          {status === "error" && (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl bg-muted px-4 py-3 text-sm text-red-500"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
