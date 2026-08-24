from abc import ABC, abstractmethod

from app.ingestion.schemas import Document


class BaseLoader(ABC):
    """
    Base class for all loaders.
    """

    @abstractmethod
    def load(self, file_path: str) -> Document:
        """
        Loads a document from a given file path.
        """
        pass
