import time

from openai import OpenAI

from app.config import settings
from app.rag import rerank as rerank_module
from app.rag import store as store_module

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You answer questions using ONLY the numbered context \
chunks provided. Follow these rules strictly:

1. If the answer is not contained in the chunks, reply exactly:
   "I don't know based on the provided documents."
2. Never use outside knowledge, even if you are confident.
3. End every factual sentence with the chunk number it came from, like [2].
4. Keep the answer short and plain."""

REFUSAL = "I don't know based on the provided documents."


def ask(question: str) -> dict:
    started = time.perf_counter()
    store = store_module.store
    reranker = rerank_module.reranker
    if store is None or reranker is None:
        raise RuntimeError("RAG models not initialized")

    hits = store.retrieve(question, settings.retrieve_k)
    gate_distance = hits[0]["distance"] if hits else None

    # GATE 1 — distance threshold, before any token is spent.
    if not hits or hits[0]["distance"] > settings.max_distance:
        return _result(
            REFUSAL, "distance_threshold", hits[:3], None, started, gate_distance,
        )

    hits = reranker.rerank(question, hits, settings.rerank_top_n)

    context = "\n\n".join(
        f"[{i}] (source: {h['source']})\n{h['text']}"
        for i, h in enumerate(hits, 1)
    )

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context chunks:\n\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    answer_text = response.choices[0].message.content

    # GATE 2 — the model declined despite passing the distance gate.
    refused_by = "llm_grounding" if REFUSAL in answer_text else None

    return _result(answer_text, refused_by, hits, response.usage, started, gate_distance)


def _result(answer, refused_by, hits, usage, started, gate_distance=None):
    return {
        "answer": answer,
        "refused": refused_by is not None,
        "refused_by": refused_by,
        "gate_distance": gate_distance,
        "sources": [
            {
                "index": i,
                "source": h["source"],
                "chunk_index": h["chunk_index"],
                "text": h["text"],
                "distance": h["distance"],
                "rerank_score": h.get("rerank_score"),
            }
            for i, h in enumerate(hits, 1)
        ],
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
        }
        if usage
        else None,
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }
