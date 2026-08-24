from pathlib import Path

from app.ingestion.base import BaseLoader
from app.ingestion.loaders.loader import TextLoader
from app.ingestion.loaders.pdf_loader import PdfLoader


class LoaderFactory:
    """
    Creates the correct loader based on file extension.
    """

    _loaders = {
        ".txt": TextLoader,
        ".pdf": PdfLoader,
    }

    @classmethod
    def get_loader(cls, file_path: str) -> BaseLoader:
        suffix = Path(file_path).suffix.lower()

        loader = cls._loaders.get(suffix)

        if loader is None:
            raise ValueError(f"Unsupported file type: {suffix}")

        return loader()
