from pathlib import Path

from app.ingestion.schemas import Document
from app.ingestion.base import BaseLoader


class TextLoader(BaseLoader):
    """
    Loads text files from a given source.
    """

    def load(self, file_path: str) -> Document:
        path = Path(file_path)

        content = path.read_text(encoding="utf-8")

        return Document(
            content=content, source=path.name, file_type="text", metadata={}
        )
