"use client";

import { useCallback, useRef, useState } from "react";
import {
  getApiErrorCode,
  getApiErrorMessage,
  runAnalysis,
  type AnalysisAnswerResponse,
  type AnalysisClarificationResponse,
} from "@/lib/api";
import { buildClarifiedQuestion } from "@/lib/utils/clarification";

export type AnalysisState =
  | { status: "idle" }
  | { status: "loading"; question: string }
  | { status: "answer"; result: AnalysisAnswerResponse; index: number }
  | {
      status: "clarification";
      result: AnalysisClarificationResponse;
      pendingQuestion: string;
    }
  | {
      status: "error";
      message: string;
      code: string;
      question: string;
    };

const EXAMPLE_QUESTIONS = [
  "Which region generated the most revenue?",
  "Show total revenue by region as a bar chart.",
  "Plot revenue over time.",
  "What is the average revenue per order?",
];

export function useAnalysis(activeDatasetId: string | null) {
  const [question, setQuestion] = useState("");
  const [analysisState, setAnalysisState] = useState<AnalysisState>({
    status: "idle",
  });
  const resultCounterRef = useRef(0);

  const submitQuestion = useCallback(
    async (questionText: string) => {
      const trimmed = questionText.trim();

      if (!trimmed || !activeDatasetId) {
        return;
      }

      setAnalysisState({ status: "loading", question: trimmed });

      try {
        const response = await runAnalysis({
          dataset_id: activeDatasetId,
          question: trimmed,
        });

        if (response.type === "clarification") {
          setAnalysisState({
            status: "clarification",
            result: response,
            pendingQuestion: trimmed,
          });
          return;
        }

        resultCounterRef.current += 1;
        setAnalysisState({
          status: "answer",
          result: response,
          index: resultCounterRef.current,
        });
      } catch (error) {
        setAnalysisState({
          status: "error",
          message: getApiErrorMessage(error),
          code: getApiErrorCode(error),
          question: trimmed,
        });
      }
    },
    [activeDatasetId],
  );

  const submitClarification = useCallback(
    async (clarificationAnswer: string) => {
      if (analysisState.status !== "clarification") {
        return;
      }

      const combined = buildClarifiedQuestion(
        analysisState.pendingQuestion,
        clarificationAnswer,
      );

      setQuestion(combined);
      await submitQuestion(combined);
    },
    [analysisState, submitQuestion],
  );

  const resetAnalysis = useCallback(() => {
    setAnalysisState({ status: "idle" });
    setQuestion("");
    resultCounterRef.current = 0;
  }, []);

  return {
    question,
    setQuestion,
    analysisState,
    exampleQuestions: EXAMPLE_QUESTIONS,
    submitQuestion,
    submitClarification,
    resetAnalysis,
  };
}

export type UseAnalysisReturn = ReturnType<typeof useAnalysis>;
