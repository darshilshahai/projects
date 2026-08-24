import json
from pathlib import Path

from app.evaluation.schemas import EvaluationCase


class EvaluationLoader:
    @staticmethod
    def load(
        path: Path,
    ) -> list[EvaluationCase]:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return [EvaluationCase.model_validate(item) for item in data]
