"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Loader2,
  SendHorizontal,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { CustomDropdown } from "@/components/ui/custom-dropdown";
import { Textarea } from "@/components/ui/textarea";
import { askQuestionStream, checkHealth } from "@/lib/api";
import {
  CATEGORY_OPTIONS,
  SAMPLE_QUESTIONS,
  TENANT_OPTIONS,
  TOP_K_OPTIONS,
} from "@/lib/constants";
import type { RAGSource } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: RAGSource[];
  streaming?: boolean;
  error?: boolean;
}

export function InvestigationPanel() {
  const { user } = useAuth();
  const [question, setQuestion] = useState("");
  const [tenantId, setTenantId] = useState(user?.organization ?? "INSURER-001");
  const [category, setCategory] = useState("fraud-guideline");
  const [topK, setTopK] = useState("5");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [collectionCount, setCollectionCount] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    checkHealth()
      .then((health) => {
        setApiOnline(true);
        setCollectionCount(health.vector_store?.collection_count ?? null);
      })
      .catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleAsk(selectedQuestion?: string) {
    const prompt = (selectedQuestion ?? question).trim();
    if (!prompt || isLoading) return;

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
    };

    const assistantId = crypto.randomUUID();
    setMessages((current) => [
      ...current,
      userMessage,
      {
        id: assistantId,
        role: "assistant",
        content: "",
        streaming: true,
      },
    ]);
    setQuestion("");
    setIsLoading(true);

    let answer = "";
    let sources: RAGSource[] = [];

    try {
      await askQuestionStream(
        {
          question: prompt,
          tenant_id: tenantId,
          category: category || undefined,
          top_k: Number(topK),
        },
        {
          onToken: (delta) => {
            answer += delta;
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? { ...message, content: answer }
                  : message,
              ),
            );
          },
          onComplete: (data) => {
            sources = (data.sources as RAGSource[]) ?? [];
            if (typeof data.answer === "string" && data.answer) {
              answer = data.answer;
            }
          },
          onError: (message) => {
            throw new Error(message);
          },
        },
        abortRef.current.signal,
      );

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                content:
                  answer ||
                  "I could not find enough relevant information in the available documents.",
                sources,
                streaming: false,
              }
            : message,
        ),
      );
    } catch (error) {
      if ((error as Error).name === "AbortError") return;

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                content:
                  apiOnline === false
                    ? "Unable to reach the API. Start the FastAPI backend on port 8000."
                    : "Something went wrong while generating the answer.",
                streaming: false,
                error: true,
              }
            : message,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-0px)] flex-col">
      <div className="border-b border-border bg-card px-6 py-5 lg:px-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <h1 className="text-xl font-semibold tracking-tight text-foreground">
                Investigation workspace
              </h1>
            </div>
            <p className="mt-1 text-sm text-muted">
              Ask fraud investigation questions with semantic retrieval and
              cited sources.
            </p>
          </div>

          <div
            className={cn(
              "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium",
              apiOnline
                ? "bg-primary-soft text-primary"
                : "bg-danger-soft text-danger",
            )}
          >
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                apiOnline ? "bg-primary" : "bg-danger",
              )}
            />
            {apiOnline
              ? `API online${collectionCount !== null ? ` · ${collectionCount} chunks` : ""}`
              : "API offline"}
          </div>
        </div>

        <div className="mt-5 grid items-start gap-4 overflow-visible md:grid-cols-3">
          <CustomDropdown
            label="Tenant"
            value={tenantId}
            options={TENANT_OPTIONS}
            onChange={setTenantId}
          />
          <CustomDropdown
            label="Category filter"
            value={category}
            options={CATEGORY_OPTIONS}
            onChange={setCategory}
          />
          <CustomDropdown
            label="Retrieval depth"
            value={topK}
            options={TOP_K_OPTIONS}
            onChange={setTopK}
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 lg:px-8">
        {messages.length === 0 ? (
          <div className="flex h-full w-full flex-col justify-center">
            <div className="w-full rounded-[28px] border border-dashed border-border bg-card px-6 py-10 text-center shadow-[var(--shadow)]">
              <h2 className="text-lg font-semibold text-foreground">
                Start an investigation
              </h2>
              <p className="mt-2 text-sm leading-7 text-muted">
                Try one of these sample questions or write your own below.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                {SAMPLE_QUESTIONS.map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => handleAsk(sample)}
                    className="rounded-full border border-border bg-muted-bg px-4 py-2 text-sm text-foreground transition-colors hover:border-primary/40 hover:bg-primary-soft"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full space-y-5">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "rounded-[24px] px-5 py-4",
                  message.role === "user"
                    ? "ml-auto max-w-[85%] bg-primary text-white"
                    : "mr-auto max-w-[90%] border border-border bg-card-elevated shadow-[var(--shadow)]",
                )}
              >
                <p className="text-xs font-medium uppercase tracking-wide opacity-70">
                  {message.role === "user" ? "Investigator" : "Veritas AI"}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-7">
                  {message.content}
                  {message.streaming ? (
                    <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-accent align-middle" />
                  ) : null}
                </p>

                {message.error ? (
                  <div className="mt-3 flex items-center gap-2 text-sm text-danger">
                    <AlertCircle className="h-4 w-4" />
                    Check that the backend is running.
                  </div>
                ) : null}

                {message.sources && message.sources.length > 0 ? (
                  <div className="mt-4 space-y-3 border-t border-border pt-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted">
                      Sources
                    </p>
                    {message.sources.map((source) => (
                      <div
                        key={source.chunk_id}
                        className="rounded-2xl bg-muted-bg px-4 py-3"
                      >
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                          <span className="font-medium text-primary">
                            Source {source.number}
                          </span>
                          <span>·</span>
                          <span>{source.source}</span>
                          <span>·</span>
                          <span>Score {source.score.toFixed(2)}</span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-foreground">
                          {source.content_preview}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-border bg-card px-6 py-4 lg:px-8">
        <div className="flex w-full flex-col gap-3">
          <Textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about duplicate billing, claim patterns, or investigation guidelines..."
            className="min-h-24"
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleAsk();
              }
            }}
          />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-muted">
              Press Enter to send · Shift+Enter for a new line
            </p>
            <Button onClick={() => handleAsk()} disabled={isLoading || !question.trim()}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Investigating
                </>
              ) : (
                <>
                  Ask question
                  <SendHorizontal className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
