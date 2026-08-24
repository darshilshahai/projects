import shutil
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import DatasetNotFoundError
from app.schemas.dataset import DatasetMetadata
from app.utils.files import read_json, write_json


class DatasetRepository:
    def __init__(self, settings: Settings) -> None:
        self._root = settings.dataset_storage_path
        self._root.mkdir(parents=True, exist_ok=True)

    def create_directory(self, dataset_id: str) -> Path:
        dataset_directory = self._root / dataset_id
        dataset_directory.mkdir(parents=False, exist_ok=False)
        return dataset_directory

    def get_directory(self, dataset_id: str) -> Path:
        dataset_directory = self._root / dataset_id

        if not dataset_directory.is_dir():
            raise DatasetNotFoundError(dataset_id)

        return dataset_directory

    def get_csv_path(self, dataset_id: str) -> Path:
        dataset_directory = self.get_directory(dataset_id)
        csv_path = dataset_directory / "dataset.csv"

        if not csv_path.is_file():
            raise DatasetNotFoundError(dataset_id)

        return csv_path

    def save_metadata(self, metadata: DatasetMetadata) -> None:
        dataset_directory = self.get_directory(metadata.dataset_id)
        metadata_path = dataset_directory / "metadata.json"
        write_json(metadata_path, metadata.model_dump(mode="json"))

    def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        dataset_directory = self.get_directory(dataset_id)
        metadata_path = dataset_directory / "metadata.json"

        if not metadata_path.is_file():
            raise DatasetNotFoundError(dataset_id)

        return DatasetMetadata.model_validate(read_json(metadata_path))

    def list_metadata(self) -> list[DatasetMetadata]:
        datasets: list[DatasetMetadata] = []

        for dataset_directory in self._root.iterdir():
            if not dataset_directory.is_dir():
                continue

            metadata_path = dataset_directory / "metadata.json"

            if not metadata_path.is_file():
                continue

            try:
                datasets.append(
                    DatasetMetadata.model_validate(read_json(metadata_path))
                )
            except (ValueError, TypeError):
                continue

        return sorted(
            datasets,
            key=lambda dataset: dataset.created_at,
            reverse=True,
        )

    def delete(self, dataset_id: str) -> None:
        dataset_directory = self.get_directory(dataset_id)
        shutil.rmtree(dataset_directory)