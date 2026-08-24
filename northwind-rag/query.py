import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("northwind")

def search(question, k=3):
    # Embed the QUESTION with the same model, so its pin lands on the
    # same map as the chunks. Using a different model here would be like
    # plotting the question on a different map — the coordinates wouldn't
    # line up and every match would be nonsense.
    q_embedding = model.encode([question]).tolist()

    return collection.query(query_embeddings=q_embedding, n_results=k)

if __name__ == "__main__":
    question = "How do I file my income tax return?"
    results = search(question)

    print(f"Question: {question}\n")
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
        print(f"[{rank}] source: {meta['source']}  |  distance: {dist:.4f}")
        print(doc[:200].replace("\n", " "), "...")
        print()