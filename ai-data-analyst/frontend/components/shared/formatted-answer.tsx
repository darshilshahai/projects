import {
  parseAnswerSegments,
  stripAnswerMarkdown,
  type AnswerSegment,
} from "@/lib/utils/answer-format";
import { cn } from "@/lib/utils/cn";

function renderAnswerSegments(segments: AnswerSegment[]) {
  return segments.map((segment, index) =>
    segment.type === "emphasis" ? (
      <span
        key={`emphasis-${index}`}
        className="font-mono text-accent tracking-[-0.02em]"
      >
        {segment.content}
      </span>
    ) : (
      <span key={`text-${index}`}>{segment.content}</span>
    ),
  );
}

type FormattedAnswerProps = {
  answer: string;
  className?: string;
  size?: "default" | "large";
};

export function FormattedAnswer({
  answer,
  className,
  size = "large",
}: FormattedAnswerProps) {
  const lines = answer.split("\n").filter(Boolean);
  const sizeClassName =
    size === "large"
      ? "text-display text-2xl text-foreground md:text-3xl lg:text-4xl"
      : "text-base leading-relaxed text-foreground";

  if (lines.length <= 1) {
    const segments = parseAnswerSegments(answer);

    return (
      <p className={cn(sizeClassName, className)}>
        {segments.some((segment) => segment.type === "emphasis")
          ? renderAnswerSegments(segments)
          : stripAnswerMarkdown(answer)}
      </p>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {lines.map((line) => {
        const segments = parseAnswerSegments(line);

        return (
          <p key={line} className={sizeClassName}>
            {segments.some((segment) => segment.type === "emphasis")
              ? renderAnswerSegments(segments)
              : stripAnswerMarkdown(line)}
          </p>
        );
      })}
    </div>
  );
}
