import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings


class Store:
    """Holds the embedding model and the Chroma collection.

    These load once at app startup, not per request. The embedding model
    takes a few seconds to load into memory — doing that inside a request
    handler would add seconds of latency to every single query.
    """

    def __init__(self):
        self.embedder = SentenceTransformer(settings.embedding_model)
        client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = client.get_collection(settings.collection)

    def retrieve(self, question: str, k: int):
        q_vec = self.embedder.encode([question]).tolist()
        res = self.collection.query(query_embeddings=q_vec, n_results=k)
        return [
            {
                "text": doc,
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "distance": dist,
            }
            for doc, meta, dist in zip(
                res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]

    def delete_source(self, source: str) -> None:
        existing = self.collection.get(where={"source": source}, include=[])
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])

    def add_chunks(self, source: str, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts).tolist()
        self.collection.add(
            ids=[f"{source}::{c['chunk_index']}" for c in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                {"source": source, "chunk_index": c["chunk_index"]}
                for c in chunks
            ],
        )
        return len(chunks)

    def list_sources(self) -> list[str]:
        result = self.collection.get(include=["metadatas"])
        sources = {
            meta["source"]
            for meta in result["metadatas"]
            if meta and "source" in meta
        }
        return sorted(sources)

    def count(self) -> int:
        return self.collection.count()


store: Store | None = None  # set at startup by the lifespan handler
