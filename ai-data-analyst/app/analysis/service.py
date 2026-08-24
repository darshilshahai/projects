import json
from pathlib import Path
from time import perf_counter
from typing import Any

from openai import OpenAI

from app.analysis.chart_builder import (
    PlotlyChartBuilder,
)
from app.analysis.prompts import (
    FINAL_ANSWER_PROMPT,
    SYSTEM_PROMPT,
    build_analysis_context,
)
from app.analysis.sql_executor import (
    SQLExecutionResult,
    SQLExecutor,
)
from app.analysis.sql_validator import SQLValidator
from app.analysis.tools import ANALYSIS_TOOLS
from app.core.config import Settings
from app.core.exceptions import (
    AIAnalysisError,
    OpenAIConfigurationError,
)
from app.datasets.repository import DatasetRepository
from app.observability.pricing import (
    PricingCalculator,
)
from app.observability.usage import TokenUsage
from app.schemas.analysis import (
    AnalysisAnswerResponse,
    AnalysisClarificationResponse,
    AnalysisMetrics,
    AnalysisResponse,
    ClarificationOption,
)
from app.schemas.chart import ChartRequest


class AnalysisService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: DatasetRepository,
        sql_validator: SQLValidator,
        sql_executor: SQLExecutor,
        chart_builder: PlotlyChartBuilder,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._sql_validator = sql_validator
        self._sql_executor = sql_executor
        self._chart_builder = chart_builder

        self._pricing = PricingCalculator(
            settings
        )

        if settings.openai_api_key:
            self._client: OpenAI | None = OpenAI(
                api_key=settings.openai_api_key
            )
        else:
            self._client = None

    def analyze(
        self,
        *,
        dataset_id: str,
        question: str,
    ) -> AnalysisResponse:
        started_at = perf_counter()

        usage = TokenUsage()

        client = self._get_client()

        metadata = self._repository.get_metadata(
            dataset_id
        )

        csv_path = self._repository.get_csv_path(
            dataset_id
        )

        context = build_analysis_context(
            metadata,
            question,
        )

        input_items: list[Any] = [
            {
                "role": "user",
                "content": context,
            }
        ]

        try:
            response = client.responses.create(
                model=self._settings.openai_model,
                instructions=SYSTEM_PROMPT,
                input=input_items,
                tools=ANALYSIS_TOOLS,
                tool_choice="required",
                parallel_tool_calls=False,
            )
        except Exception as exc:
            raise AIAnalysisError(
                f"OpenAI analysis request failed: {exc}"
            ) from exc

        usage.add_response(
            response
        )

        input_items.extend(
            response.output
        )

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if len(tool_calls) != 1:
            raise AIAnalysisError(
                "The model did not return exactly one "
                "analysis action."
            )

        tool_call = tool_calls[0]

        arguments = self._parse_arguments(
            tool_call.arguments
        )

        if tool_call.name == "ask_clarification":
            return self._handle_clarification(
                question=question,
                arguments=arguments,
                usage=usage,
                started_at=started_at,
            )

        if tool_call.name == "execute_sql":
            return self._handle_sql(
                client=client,
                question=question,
                csv_path=csv_path,
                input_items=input_items,
                tool_call=tool_call,
                arguments=arguments,
                usage=usage,
                started_at=started_at,
            )

        if tool_call.name == "create_chart":
            return self._handle_chart(
                client=client,
                question=question,
                csv_path=csv_path,
                input_items=input_items,
                tool_call=tool_call,
                arguments=arguments,
                usage=usage,
                started_at=started_at,
            )

        raise AIAnalysisError(
            f"Unsupported tool call: {tool_call.name}"
        )

    def _handle_clarification(
        self,
        *,
        question: str,
        arguments: dict[str, Any],
        usage: TokenUsage,
        started_at: float,
    ) -> AnalysisClarificationResponse:
        clarification_question = str(
            arguments["question"]
        ).strip()

        options = [
            ClarificationOption(
                label=str(
                    option["label"]
                ).strip(),
                value=str(
                    option["value"]
                ).strip(),
            )
            for option in arguments["options"]
        ]

        if not 2 <= len(options) <= 4:
            raise AIAnalysisError(
                "Clarification must contain between "
                "2 and 4 options."
            )

        return AnalysisClarificationResponse(
            question=question,
            clarification_question=(
                clarification_question
            ),
            options=options,
            metrics=self._build_metrics(
                usage=usage,
                started_at=started_at,
            ),
        )

    def _handle_sql(
        self,
        *,
        client: OpenAI,
        question: str,
        csv_path: Path,
        input_items: list[Any],
        tool_call: Any,
        arguments: dict[str, Any],
        usage: TokenUsage,
        started_at: float,
    ) -> AnalysisAnswerResponse:
        execution_result = (
            self._execute_generated_sql(
                csv_path=csv_path,
                sql=str(
                    arguments["query"]
                ),
            )
        )

        tool_output = {
            "action": "execute_sql",
            **execution_result.to_dict(),
        }

        answer = self._generate_final_answer(
            client=client,
            input_items=input_items,
            tool_call=tool_call,
            tool_output=tool_output,
            usage=usage,
        )

        return AnalysisAnswerResponse(
            question=question,
            answer=answer,
            sql=execution_result.sql,
            columns=execution_result.columns,
            rows=execution_result.rows,
            row_count=execution_result.row_count,
            chart=None,
            metrics=self._build_metrics(
                usage=usage,
                started_at=started_at,
            ),
        )

    def _handle_chart(
        self,
        *,
        client: OpenAI,
        question: str,
        csv_path: Path,
        input_items: list[Any],
        tool_call: Any,
        arguments: dict[str, Any],
        usage: TokenUsage,
        started_at: float,
    ) -> AnalysisAnswerResponse:
        execution_result = (
            self._execute_generated_sql(
                csv_path=csv_path,
                sql=str(
                    arguments["query"]
                ),
            )
        )

        chart_request = ChartRequest(
            chart_type=arguments[
                "chart_type"
            ],
            x=arguments["x"],
            y=arguments["y"],
            title=arguments["title"],
            x_label=arguments["x_label"],
            y_label=arguments["y_label"],
        )

        chart = self._chart_builder.build(
            request=chart_request,
            rows=execution_result.rows,
            columns=execution_result.columns,
        )

        tool_output = {
            "action": "create_chart",
            "query_result": (
                execution_result.to_dict()
            ),
            "chart": {
                "chart_type": (
                    chart.chart_type
                ),
                "title": chart.title,
                "x": chart.x,
                "y": chart.y,
            },
        }

        answer = self._generate_final_answer(
            client=client,
            input_items=input_items,
            tool_call=tool_call,
            tool_output=tool_output,
            usage=usage,
        )

        return AnalysisAnswerResponse(
            question=question,
            answer=answer,
            sql=execution_result.sql,
            columns=execution_result.columns,
            rows=execution_result.rows,
            row_count=execution_result.row_count,
            chart=chart,
            metrics=self._build_metrics(
                usage=usage,
                started_at=started_at,
            ),
        )

    def _execute_generated_sql(
        self,
        *,
        csv_path: Path,
        sql: str,
    ) -> SQLExecutionResult:
        validated_sql = (
            self._sql_validator.validate_and_prepare(
                sql.strip()
            )
        )

        return self._sql_executor.execute(
            csv_path=csv_path,
            sql=validated_sql,
        )

    def _generate_final_answer(
        self,
        *,
        client: OpenAI,
        input_items: list[Any],
        tool_call: Any,
        tool_output: dict[str, Any],
        usage: TokenUsage,
    ) -> str:
        final_input = [
            *input_items,
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": json.dumps(
                    tool_output,
                    ensure_ascii=False,
                    default=str,
                ),
            },
        ]

        try:
            response = client.responses.create(
                model=self._settings.openai_model,
                instructions=FINAL_ANSWER_PROMPT,
                input=final_input,
                tools=ANALYSIS_TOOLS,
                tool_choice="none",
                parallel_tool_calls=False,
            )
        except Exception as exc:
            raise AIAnalysisError(
                f"OpenAI final-answer request failed: {exc}"
            ) from exc

        usage.add_response(
            response
        )

        answer = response.output_text.strip()

        if not answer:
            raise AIAnalysisError(
                "The model returned an empty answer."
            )

        return answer

    def _build_metrics(
        self,
        *,
        usage: TokenUsage,
        started_at: float,
    ) -> AnalysisMetrics:
        elapsed_ms = (
            perf_counter()
            - started_at
        ) * 1000

        cost = self._pricing.calculate(
            usage
        )

        return AnalysisMetrics(
            latency_ms=round(
                elapsed_ms,
                2,
            ),
            llm_calls=usage.llm_calls,
            input_tokens=usage.input_tokens,
            cached_input_tokens=(
                usage.cached_input_tokens
            ),
            output_tokens=usage.output_tokens,
            reasoning_tokens=(
                usage.reasoning_tokens
            ),
            total_tokens=usage.total_tokens,
            estimated_cost_usd=(
                cost.total_cost_usd
            ),
        )

    @staticmethod
    def _parse_arguments(
        arguments: str,
    ) -> dict[str, Any]:
        try:
            return json.loads(
                arguments
            )
        except json.JSONDecodeError as exc:
            raise AIAnalysisError(
                "The model returned invalid "
                "tool arguments."
            ) from exc

    def _get_client(
        self,
    ) -> OpenAI:
        if self._client is None:
            raise OpenAIConfigurationError()

        return self._client