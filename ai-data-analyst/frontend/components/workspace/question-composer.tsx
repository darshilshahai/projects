"use client";

import { useCallback } from "react";
import { cn } from "@/lib/utils/cn";

type QuestionComposerProps = {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: (question: string) => void;
  loading?: boolean;
  disabled?: boolean;
  datasetName?: string;
  exampleQuestions?: string[];
  className?: string;
};

export function QuestionComposer({
  question,
  onQuestionChange,
  onSubmit,
  loading = false,
  disabled = false,
  datasetName,
  exampleQuestions = [],
  className,
}: QuestionComposerProps) {
  const handleSubmit = useCallback(() => {
    if (loading || disabled || !question.trim()) {
      return;
    }
    onSubmit(question);
  }, [disabled, loading, onSubmit, question]);

  return (
    <div
      className={cn(
        "shrink-0 border-t border-border-subtle bg-background-panel px-5 py-4 md:px-8",
        className,
      )}
    >
      <label className="block space-y-3">
        <span className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Ask your data
        </span>

        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
              event.preventDefault();
              handleSubmit();
            }
          }}
          disabled={disabled || loading}
          rows={3}
          placeholder={
            datasetName
              ? `Ask something about ${datasetName}...`
              : "Select a dataset to begin..."
          }
          className="w-full resize-none border border-border-subtle bg-background px-3 py-3 text-sm leading-relaxed text-foreground outline-none transition-colors duration-150 placeholder:text-muted focus:border-accent disabled:cursor-not-allowed disabled:opacity-60"
        />
      </label>

      {exampleQuestions.length > 0 && !question ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {exampleQuestions.map((example) => (
            <button
              key={example}
              type="button"
              disabled={disabled || loading}
              onClick={() => onQuestionChange(example)}
              className="border border-border-subtle px-2 py-1 font-mono text-[10px] tracking-[0.08em] text-muted uppercase transition-colors duration-150 hover:border-border hover:text-foreground disabled:opacity-50"
            >
              {example}
            </button>
          ))}
        </div>
      ) : null}

      <div className="mt-4 flex items-center justify-between gap-4">
        <p className="font-mono text-[10px] tracking-widest text-muted uppercase">
          Cmd/Ctrl + Enter
        </p>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || loading || !question.trim()}
          className="landing-cta landing-cta-primary disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "ANALYZING..." : "RUN ANALYSIS ↗"}
        </button>
      </div>
    </div>
  );
}
