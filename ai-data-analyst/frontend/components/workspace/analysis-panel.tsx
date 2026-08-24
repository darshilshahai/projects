"use client";

import { useAnalysis } from "@/hooks/use-analysis";
import type { DatasetMetadata } from "@/lib/api";
import { AnalysisEmptyState } from "./analysis-empty-state";
import { AnalysisErrorView } from "./analysis-error-view";
import { AnalysisLoading } from "./analysis-loading";
import { AnswerView } from "./answer-view";
import { ClarificationView } from "./clarification-view";
import { EngineOfflineBanner } from "./engine-offline-banner";
import { QuestionComposer } from "./question-composer";

type AnalysisPanelProps = {
  activeDataset: DatasetMetadata | null;
  engineOnline: boolean;
};

export function AnalysisPanel({
  activeDataset,
  engineOnline,
}: AnalysisPanelProps) {
  const {
    question,
    setQuestion,
    analysisState,
    exampleQuestions,
    submitQuestion,
    submitClarification,
  } = useAnalysis(activeDataset?.dataset_id ?? null);

  const isAnalyzing = analysisState.status === "loading";
  const analysisDisabled = !activeDataset || !engineOnline;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      {!engineOnline ? <EngineOfflineBanner /> : null}

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        <div className="space-y-6 p-5 md:p-8">
          {analysisState.status === "idle" ? (
            <AnalysisEmptyState datasetName={activeDataset?.original_filename} />
          ) : null}

          {analysisState.status === "loading" ? <AnalysisLoading /> : null}

          {analysisState.status === "answer" ? (
            <AnswerView
              result={analysisState.result}
              index={analysisState.index}
            />
          ) : null}

          {analysisState.status === "clarification" ? (
            <ClarificationView
              key={`${analysisState.pendingQuestion}-${analysisState.result.clarification_question}`}
              result={analysisState.result}
              loading={isAnalyzing}
              onSubmit={(answer) => void submitClarification(answer)}
            />
          ) : null}

          {analysisState.status === "error" ? (
            <AnalysisErrorView analysisState={analysisState} />
          ) : null}
        </div>
      </div>

      <QuestionComposer
        question={question}
        onQuestionChange={setQuestion}
        onSubmit={(value) => void submitQuestion(value)}
        loading={isAnalyzing}
        disabled={analysisDisabled}
        datasetName={activeDataset?.original_filename}
        exampleQuestions={engineOnline ? exampleQuestions : []}
      />
    </div>
  );
}
