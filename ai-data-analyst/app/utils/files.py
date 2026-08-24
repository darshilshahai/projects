import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


def json_safe(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, float):
        if value != value:  # noqa: PLR0124
            return None
        if value in (float("inf"), float("-inf")):
            return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except (ValueError, TypeError):
            pass

    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]

    return value


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(json_safe(data), file, ensure_ascii=False, indent=2)

    temporary_path.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)