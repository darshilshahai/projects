import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Threshold set from measured data — see PROJECT_1_NOTES.md Finding 2.
    # Loosened from 0.50 to 0.65 after a valid question at 0.549 was
    # falsely refused. Gate 2 (LLM grounding) catches what passes through.
    max_distance: float = 0.65

    retrieve_k: int = 10  # wide net
    rerank_top_n: int = 3  # then narrow

    embedding_model: str = "all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_model: str = "gpt-4o-mini"

    chroma_path: str = "./chroma_db"
    collection: str = "northwind"
    docs_folder: str = "sample_docs"
    chunk_size: int = 500

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()
