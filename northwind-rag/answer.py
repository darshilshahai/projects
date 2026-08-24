import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from rerank import rerank

load_dotenv()

# --- Threshold set from OUR measured data, not a guess ---
# Worst in-scope top-1 distance:  0.4136
# Best  out-of-scope top-1 distance: 0.5881
# 0.50 sits in the empty gap between the two groups.
MAX_DISTANCE = 0.65

embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_collection("northwind")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You answer questions using ONLY the numbered context \
chunks provided. Follow these rules strictly:

1. If the answer is not contained in the chunks, reply exactly:
   "I don't know based on the provided documents."
2. Never use outside knowledge, even if you are confident.
3. End every factual sentence with the chunk number it came from, like [2].
4. Keep the answer short and plain."""


def retrieve(question, k=3):
    q_vec = embedder.encode([question]).tolist()

    res = collection.query(query_embeddings=q_vec, n_results=k)
    # print(res)
    return [
        {"text": d, "source": m["source"], "distance": dist}
        for d, m, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]

def answer(question, k=10, top_n=3):
    hits = retrieve(question, k)

    # GATE 1 — refuse before spending a single token on the LLM.
    if not hits or hits[0]["distance"] > MAX_DISTANCE:
        return {
            "answer": "I don't know based on the provided documents.",
            "refused_by": "distance_threshold",
            "hits": hits,
        }

    hits = rerank(question, hits, top_n)

    context = "\n\n".join(
        f"[{i}] (source: {h['source']})\n{h['text']}" for i, h in enumerate(hits, 1)
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context chunks:\n\n{context}\n\nQuestion: {question}",
            },
        ],
    )

    return {
        "answer": response.choices[0].message.content,
        "refused_by": None,
        "hits": hits,
        "usage": response.usage,
    }



if __name__ == "__main__":
    for q in [
        "How many days of paid sick leave do I get?",
        "What is the company's policy on office pets?",
        # "How many days of paid sick leave can I carry forward?",
        # "What is the meal allowance for international travel?"
    ]:
        result = answer(q)
        print("=" * 65)
        print(f"Q: {q}\n")
        print(result["answer"], "\n")
        if result["refused_by"]:
            print(
                f"(refused by: {result['refused_by']}, "
                f"top distance {result['hits'][0]['distance']:.4f})"
            )
        else:
            print("Sources used:")
            for i, h in enumerate(result["hits"], 1):
                print(f"  [{i}] {h['source']} (distance {h['distance']:.4f})")
        print()
