from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.llm.llm_config import LLMConfig
from app.llm.llm_schema import (
    LLMRequest,
    LLMResponse,
    LLMStreamEvent,
)


class BaseLLM(ABC):
    """
    Common interface for language model providers.

    Implementations support:

    - complete non-streamed generation
    - incremental streamed generation
    """

    def __init__(
        self,
        config: LLMConfig,
    ) -> None:
        if not isinstance(config, LLMConfig):
            raise TypeError(
                "config must be an LLMConfig instance."
            )

        self._config = config

    @property
    def config(self) -> LLMConfig:
        """
        Return immutable LLM configuration.
        """

        return self._config

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate and return one complete response.
        """

        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[LLMStreamEvent]:
        """
        Generate a response incrementally.

        The iterator emits text_delta events followed by one completed event.
        """

        raise NotImplementedError