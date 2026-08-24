from pathlib import Path
from typing import cast

import fitz  # type: ignore[import-untyped]

from app.ingestion.base import BaseLoader
from app.ingestion.schemas import Document


class PdfLoader(BaseLoader):
    """
    Loads text from PDF documents.
    """

    def load(self, file_path: str) -> Document:
        path = Path(file_path)

        pages: list[str] = []

        with fitz.open(file_path) as pdf:
            pages = [cast(str, page.get_text("text")) for page in pdf]

        content = "\n".join(pages)

        return Document(
            content=content,
            source=path.name,
            file_type="pdf",
            metadata={"pages": len(pages)},
        )
