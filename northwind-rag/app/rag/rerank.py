from sentence_transformers import CrossEncoder

from app.config import settings


class Reranker:
    """Cross-encoder reranker — loaded once at startup, not per request."""

    def __init__(self):
        self.model = CrossEncoder(settings.reranker_model)

    def rerank(self, question: str, hits: list, top_n: int) -> list:
        pairs = [(question, h["text"]) for h in hits]
        scores = self.model.predict(pairs)
        for hit, score in zip(hits, scores):
            hit["rerank_score"] = float(score)
        return sorted(hits, key=lambda h: h["rerank_score"], reverse=True)[:top_n]


reranker: Reranker | None = None  # set at startup by the lifespan handler
