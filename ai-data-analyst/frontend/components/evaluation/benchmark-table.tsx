"use client";

import { useMemo, useState } from "react";
import type { CaseAnalysis, EvaluationCaseResult } from "@/lib/evaluation/types";
import {
  BenchmarkFilters,
  type ActionFilter,
  type StatusFilter,
} from "./benchmark-filters";
import { BenchmarkRow, BenchmarkRowMobile } from "./benchmark-row";

type BenchmarkTableProps = {
  cases: EvaluationCaseResult[];
  caseAnalyses: CaseAnalysis[];
};

function filterCases(
  cases: EvaluationCaseResult[],
  statusFilter: StatusFilter,
  actionFilter: ActionFilter,
  search: string,
): EvaluationCaseResult[] {
  return cases.filter((caseResult) => {
    if (statusFilter === "passed" && !caseResult.passed) {
      return false;
    }

    if (statusFilter === "failed" && caseResult.passed) {
      return false;
    }

    if (
      actionFilter !== "all" &&
      caseResult.expected_action !== actionFilter &&
      caseResult.actual_action !== actionFilter
    ) {
      return false;
    }

    if (
      search.trim() &&
      !caseResult.question.toLowerCase().includes(search.trim().toLowerCase()) &&
      !caseResult.id.toLowerCase().includes(search.trim().toLowerCase())
    ) {
      return false;
    }

    return true;
  });
}

export function BenchmarkTable({ cases, caseAnalyses }: BenchmarkTableProps) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [actionFilter, setActionFilter] = useState<ActionFilter>("all");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const analysisMap = useMemo(
    () => new Map(caseAnalyses.map((item) => [item.case.id, item])),
    [caseAnalyses],
  );

  const filteredCases = useMemo(
    () => filterCases(cases, statusFilter, actionFilter, search),
    [cases, statusFilter, actionFilter, search],
  );

  return (
    <section className="space-y-4">
      <BenchmarkFilters
        statusFilter={statusFilter}
        actionFilter={actionFilter}
        search={search}
        totalCount={filteredCases.length}
        onStatusFilterChange={setStatusFilter}
        onActionFilterChange={setActionFilter}
        onSearchChange={setSearch}
      />

      <div className="hidden overflow-x-auto border border-border-subtle md:block">
        <table className="min-w-full border-collapse text-left">
          <thead className="sticky top-0 bg-background">
            <tr className="border-b border-border-subtle">
              {[
                "ID",
                "Question",
                "Expected",
                "Actual",
                "Value",
                "Chart",
                "Latency",
                "Cost",
                "Status",
              ].map((column) => (
                <th
                  key={column}
                  className="px-3 py-3 font-mono text-[10px] tracking-[0.12em] text-muted uppercase"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredCases.map((caseResult) => {
              const analysis = analysisMap.get(caseResult.id);

              if (!analysis) {
                return null;
              }

              return (
                <BenchmarkRow
                  key={caseResult.id}
                  analysis={analysis}
                  expanded={expandedId === caseResult.id}
                  onToggle={() =>
                    setExpandedId((current) =>
                      current === caseResult.id ? null : caseResult.id,
                    )
                  }
                />
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="border border-border-subtle md:hidden">
        {filteredCases.map((caseResult) => {
          const analysis = analysisMap.get(caseResult.id);

          if (!analysis) {
            return null;
          }

          return (
            <BenchmarkRowMobile
              key={caseResult.id}
              analysis={analysis}
              expanded={expandedId === caseResult.id}
              onToggle={() =>
                setExpandedId((current) =>
                  current === caseResult.id ? null : caseResult.id,
                )
              }
            />
          );
        })}
      </div>
    </section>
  );
}
