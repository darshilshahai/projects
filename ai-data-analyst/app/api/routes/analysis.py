from functools import lru_cache

from fastapi import APIRouter

from app.analysis.chart_builder import PlotlyChartBuilder
from app.analysis.chart_validator import ChartValidator
from app.analysis.service import AnalysisService
from app.analysis.sql_executor import SQLExecutor
from app.analysis.sql_validator import SQLValidator
from app.core.config import get_settings
from app.datasets.profiler import DatasetProfiler
from app.datasets.repository import DatasetRepository
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
)

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


@lru_cache
def get_analysis_service() -> AnalysisService:
    settings = get_settings()

    repository = DatasetRepository(
        settings
    )

    profiler = DatasetProfiler(
        sample_rows=settings.csv_sample_rows,
        preview_rows=settings.csv_preview_rows,
    )

    sql_validator = SQLValidator(
        max_rows=settings.max_query_rows
    )

    sql_executor = SQLExecutor(
        profiler=profiler
    )

    chart_validator = ChartValidator()

    chart_builder = PlotlyChartBuilder(
        validator=chart_validator
    )

    return AnalysisService(
        settings=settings,
        repository=repository,
        sql_validator=sql_validator,
        sql_executor=sql_executor,
        chart_builder=chart_builder,
    )


@router.post(
    "",
    response_model=AnalysisResponse,
)
def analyze_dataset(
    request: AnalysisRequest,
) -> AnalysisResponse:
    return get_analysis_service().analyze(
        dataset_id=request.dataset_id,
        question=request.question,
    )