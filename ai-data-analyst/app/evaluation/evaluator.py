from math import ceil
from statistics import mean
from typing import Any

from app.analysis.service import AnalysisService
from app.evaluation.schemas import (
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationReport,
    EvaluationSummary,
)
from app.schemas.analysis import (
    AnalysisAnswerResponse,
    AnalysisClarificationResponse,
    AnalysisResponse,
)


class Evaluator:
    def __init__(
        self,
        analysis_service: AnalysisService,
    ) -> None:
        self._analysis_service = analysis_service

    def run(
        self,
        *,
        dataset_id: str,
        cases: list[EvaluationCase],
    ) -> EvaluationReport:
        results: list[EvaluationCaseResult] = []

        for case in cases:
            result = self._run_case(
                dataset_id=dataset_id,
                case=case,
            )

            results.append(result)

        summary = self._build_summary(results)

        return EvaluationReport(
            summary=summary,
            cases=results,
        )

    def _run_case(
        self,
        *,
        dataset_id: str,
        case: EvaluationCase,
    ) -> EvaluationCaseResult:
        try:
            response = self._analysis_service.analyze(
                dataset_id=dataset_id,
                question=case.question,
            )

            actual_action = self._get_actual_action(response)

            action_pass = actual_action == case.expected_action

            values_pass = self._evaluate_values(
                case=case,
                response=response,
            )

            chart_pass = self._evaluate_chart(
                case=case,
                response=response,
            )

            passed = action_pass and values_pass and chart_pass

            sql = None

            if isinstance(
                response,
                AnalysisAnswerResponse,
            ):
                sql = response.sql

            failure_reason = (
                None
                if passed
                else self._describe_failure(
                    action_pass=action_pass,
                    values_pass=values_pass,
                    chart_pass=chart_pass,
                )
            )

            return EvaluationCaseResult(
                id=case.id,
                question=case.question,
                expected_action=(case.expected_action),
                actual_action=actual_action,
                action_pass=action_pass,
                values_pass=values_pass,
                chart_pass=chart_pass,
                passed=passed,
                latency_ms=(response.metrics.latency_ms),
                input_tokens=(response.metrics.input_tokens),
                output_tokens=(response.metrics.output_tokens),
                total_tokens=(response.metrics.total_tokens),
                estimated_cost_usd=(response.metrics.estimated_cost_usd),
                sql=sql,
                failure_reason=failure_reason,
            )

        except Exception as exc:
            return EvaluationCaseResult(
                id=case.id,
                question=case.question,
                expected_action=(case.expected_action),
                actual_action="error",
                action_pass=False,
                values_pass=False,
                chart_pass=False,
                passed=False,
                latency_ms=0,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                estimated_cost_usd=0,
                sql=None,
                failure_reason=str(exc),
            )

    def _evaluate_values(
        self,
        *,
        case: EvaluationCase,
        response: AnalysisResponse,
    ) -> bool:
        if not case.expected_values:
            return True

        if not isinstance(
            response,
            AnalysisAnswerResponse,
        ):
            return False

        for expected in case.expected_values:
            found = self._contains_value(
                rows=response.rows,
                column=expected.column,
                expected=expected.value,
            )

            if not found:
                return False

        return True

    def _evaluate_chart(
        self,
        *,
        case: EvaluationCase,
        response: AnalysisResponse,
    ) -> bool:
        if case.expected_action != "chart":
            return True

        if not isinstance(
            response,
            AnalysisAnswerResponse,
        ):
            return False

        if response.chart is None:
            return False

        if case.expected_chart_type is None:
            return True

        return response.chart.chart_type == case.expected_chart_type

    @staticmethod
    def _contains_value(
        *,
        rows: list[dict[str, Any]],
        column: str,
        expected: Any,
    ) -> bool:
        for row in rows:
            if column not in row:
                continue

            actual = row[column]

            if Evaluator._values_equal(
                actual,
                expected,
            ):
                return True

        return False

    @staticmethod
    def _values_equal(
        actual: Any,
        expected: Any,
    ) -> bool:
        if isinstance(
            actual,
            (int, float),
        ) and isinstance(
            expected,
            (int, float),
        ):
            return abs(float(actual) - float(expected)) < 1e-6

        return str(actual).strip().lower() == str(expected).strip().lower()

    @staticmethod
    def _get_actual_action(
        response: AnalysisResponse,
    ) -> str:
        if isinstance(
            response,
            AnalysisClarificationResponse,
        ):
            return "clarification"

        if response.chart is not None:
            return "chart"

        return "answer"

    @staticmethod
    def _describe_failure(
        *,
        action_pass: bool,
        values_pass: bool,
        chart_pass: bool,
    ) -> str:
        failures: list[str] = []

        if not action_pass:
            failures.append("incorrect action")

        if not values_pass:
            failures.append("incorrect computed value")

        if not chart_pass:
            failures.append("incorrect chart")

        return ", ".join(failures)

    def _build_summary(
        self,
        results: list[EvaluationCaseResult],
    ) -> EvaluationSummary:
        total = len(results)

        if total == 0:
            return EvaluationSummary(
                total_cases=0,
                passed_cases=0,
                failed_cases=0,
                pass_rate=0,
                action_accuracy=0,
                value_accuracy=0,
                chart_accuracy=0,
                average_latency_ms=0,
                p95_latency_ms=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                total_estimated_cost_usd=0,
                average_cost_usd=0,
            )

        passed = sum(result.passed for result in results)

        action_passes = sum(result.action_pass for result in results)

        value_passes = sum(result.values_pass for result in results)

        chart_cases = [
            result for result in results if (result.expected_action == "chart")
        ]

        chart_passes = sum(result.chart_pass for result in chart_cases)

        latencies = sorted(
            result.latency_ms for result in results if result.latency_ms > 0
        )

        average_latency = mean(latencies) if latencies else 0

        p95_latency = (
            self._percentile(
                latencies,
                95,
            )
            if latencies
            else 0
        )

        total_cost = sum(result.estimated_cost_usd for result in results)

        return EvaluationSummary(
            total_cases=total,
            passed_cases=passed,
            failed_cases=(total - passed),
            pass_rate=round(
                passed / total * 100,
                2,
            ),
            action_accuracy=round(
                action_passes / total * 100,
                2,
            ),
            value_accuracy=round(
                value_passes / total * 100,
                2,
            ),
            chart_accuracy=round(
                (chart_passes / len(chart_cases) * 100) if chart_cases else 100,
                2,
            ),
            average_latency_ms=round(
                average_latency,
                2,
            ),
            p95_latency_ms=round(
                p95_latency,
                2,
            ),
            total_input_tokens=sum(result.input_tokens for result in results),
            total_output_tokens=sum(result.output_tokens for result in results),
            total_tokens=sum(result.total_tokens for result in results),
            total_estimated_cost_usd=round(
                total_cost,
                6,
            ),
            average_cost_usd=round(
                total_cost / total,
                6,
            ),
        )

    @staticmethod
    def _percentile(
        values: list[float],
        percentile: int,
    ) -> float:
        if not values:
            return 0

        index = ceil(percentile / 100 * len(values)) - 1

        index = max(
            0,
            min(
                index,
                len(values) - 1,
            ),
        )

        return values[index]
