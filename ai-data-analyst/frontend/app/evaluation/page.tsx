import { Navbar } from "@/components/landing/navbar";
import { GridBackground } from "@/components/shared";
import { EvaluationShell } from "@/components/evaluation";
import { analyzeEvaluationReport } from "@/lib/evaluation/analyze-report";
import {
  getBenchmarkCases,
  getEvaluationReport,
} from "@/lib/evaluation/mock-report";

export default function EvaluationPage() {
  const report = getEvaluationReport();
  const benchmarkCases = getBenchmarkCases();
  const analysis = analyzeEvaluationReport(report, benchmarkCases);

  return (
    <GridBackground fade className="min-h-dvh">
      <Navbar />
      <EvaluationShell report={report} analysis={analysis} />
    </GridBackground>
  );
}
