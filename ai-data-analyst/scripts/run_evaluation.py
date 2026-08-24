import argparse
import csv
import json
from pathlib import Path

from app.analysis.chart_builder import (
    PlotlyChartBuilder,
)
from app.analysis.chart_validator import (
    ChartValidator,
)
from app.analysis.service import AnalysisService
from app.analysis.sql_executor import SQLExecutor
from app.analysis.sql_validator import SQLValidator
from app.core.config import get_settings
from app.datasets.profiler import DatasetProfiler
from app.datasets.repository import DatasetRepository
from app.evaluation.evaluator import Evaluator
from app.evaluation.loader import EvaluationLoader
from app.evaluation.schemas import EvaluationReport
from app.schemas.dataset import DatasetMetadata


def build_analysis_service() -> AnalysisService:
    settings = get_settings()

    repository = DatasetRepository(settings)

    profiler = DatasetProfiler(
        sample_rows=settings.csv_sample_rows,
        preview_rows=settings.csv_preview_rows,
    )

    sql_validator = SQLValidator(max_rows=settings.max_query_rows)

    sql_executor = SQLExecutor(profiler=profiler)

    chart_validator = ChartValidator()

    chart_builder = PlotlyChartBuilder(validator=chart_validator)

    return AnalysisService(
        settings=settings,
        repository=repository,
        sql_validator=sql_validator,
        sql_executor=sql_executor,
        chart_builder=chart_builder,
    )


def find_dataset(
    repository: DatasetRepository,
    filename: str,
) -> DatasetMetadata:
    datasets = repository.list_metadata()

    matches = [dataset for dataset in datasets if dataset.original_filename == filename]

    if not matches:
        raise RuntimeError(
            f"Dataset '{filename}' is not uploaded. "
            "Upload evaluation/sales_eval.csv first."
        )

    return matches[0]


def write_json_report(
    report: EvaluationReport,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report.model_dump(mode="json"),
            file,
            indent=2,
            ensure_ascii=False,
        )


def write_csv_report(
    report: EvaluationReport,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "id",
        "question",
        "expected_action",
        "actual_action",
        "action_pass",
        "values_pass",
        "chart_pass",
        "passed",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost_usd",
        "sql",
        "failure_reason",
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for case in report.cases:
            writer.writerow(case.model_dump())


def print_summary(
    report: EvaluationReport,
) -> None:
    summary = report.summary

    print()
    print("=" * 64)
    print("QUERYMINT EVALUATION")
    print("=" * 64)

    print(f"Cases              : {summary.total_cases}")

    print(f"Passed             : {summary.passed_cases}")

    print(f"Failed             : {summary.failed_cases}")

    print(f"Pass rate          : {summary.pass_rate:.2f}%")

    print(f"Action accuracy    : {summary.action_accuracy:.2f}%")

    print(f"Value accuracy     : {summary.value_accuracy:.2f}%")

    print(f"Chart accuracy     : {summary.chart_accuracy:.2f}%")

    print(f"Average latency    : {summary.average_latency_ms:.2f} ms")

    print(f"P95 latency        : {summary.p95_latency_ms:.2f} ms")

    print(f"Total tokens       : {summary.total_tokens}")

    print(f"Estimated cost     : ${summary.total_estimated_cost_usd:.6f}")

    print()

    failures = [case for case in report.cases if not case.passed]

    if failures:
        print("FAILURES")
        print("-" * 64)

        for case in failures:
            print(f"{case.id}: {case.question}")

            print(f"  expected: {case.expected_action}")

            print(f"  actual  : {case.actual_action}")

            print(f"  reason  : {case.failure_reason}")

            if case.sql:
                print(f"  sql     : {case.sql}")

            print()

    else:
        print("All benchmark cases passed.")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        default="sales_eval.csv",
    )

    parser.add_argument(
        "--benchmark",
        default="evaluation/benchmark.json",
    )

    parser.add_argument(
        "--json-report",
        default=("reports/evaluation_report.json"),
    )

    parser.add_argument(
        "--csv-report",
        default=("reports/evaluation_report.csv"),
    )

    args = parser.parse_args()

    settings = get_settings()

    repository = DatasetRepository(settings)

    dataset = find_dataset(
        repository,
        args.dataset,
    )

    cases = EvaluationLoader.load(Path(args.benchmark))

    analysis_service = build_analysis_service()

    evaluator = Evaluator(analysis_service)

    report = evaluator.run(
        dataset_id=dataset.dataset_id,
        cases=cases,
    )

    write_json_report(
        report,
        Path(args.json_report),
    )

    write_csv_report(
        report,
        Path(args.csv_report),
    )

    print_summary(report)


if __name__ == "__main__":
    main()
