from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.core.config import get_settings
from app.datasets.profiler import DatasetProfiler
from app.datasets.repository import DatasetRepository
from app.datasets.service import DatasetService
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetMetadata,
    DatasetPreviewResponse,
    DatasetUploadResponse,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@lru_cache
def get_dataset_service() -> DatasetService:
    settings = get_settings()

    repository = DatasetRepository(settings)

    profiler = DatasetProfiler(
        sample_rows=settings.csv_sample_rows,
        preview_rows=settings.csv_preview_rows,
    )

    return DatasetService(
        settings=settings,
        repository=repository,
        profiler=profiler,
    )


@router.post(
    "",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: Annotated[UploadFile, File()],
) -> DatasetUploadResponse:
    dataset = await get_dataset_service().upload(file)

    return DatasetUploadResponse(
        message="Dataset uploaded and profiled successfully.",
        dataset=dataset,
    )


@router.get("", response_model=DatasetListResponse)
def list_datasets() -> DatasetListResponse:
    datasets = get_dataset_service().list()

    return DatasetListResponse(
        datasets=datasets,
        count=len(datasets),
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetMetadata,
)
def get_dataset(dataset_id: str) -> DatasetMetadata:
    return get_dataset_service().get(dataset_id)


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
)
def preview_dataset(
    dataset_id: str,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
) -> DatasetPreviewResponse:
    rows = get_dataset_service().preview(
        dataset_id,
        limit=limit,
    )

    return DatasetPreviewResponse(
        dataset_id=dataset_id,
        rows=rows,
        returned_rows=len(rows),
    )


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_dataset(dataset_id: str) -> Response:
    get_dataset_service().delete(dataset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)