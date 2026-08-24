import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.rag.chunking import chunk_documents, load_documents

docs = load_documents(settings.docs_folder)
chunks = chunk_documents(docs, target_size=settings.chunk_size)
print(f"{len(chunks)} chunks to index")

model = SentenceTransformer(settings.embedding_model)

texts = [c["text"] for c in chunks]
embeddings = model.encode(texts, show_progress_bar=True)

print(f"\nEach embedding is a vector of length {len(embeddings[0])}")
print(f"First 8 numbers of chunk 0's vector:\n{embeddings[0][:8]}\n")

client = chromadb.PersistentClient(path=settings.chroma_path)

# Delete-then-create makes this script safe to re-run (idempotent).
try:
    client.delete_collection(settings.collection)
except Exception as exc:  # noqa: BLE001
    print(exc)

collection = client.create_collection(
    settings.collection,
    metadata={"hnsw:space": "cosine"},
)

collection.add(
    ids=[f"{c['source']}::{c['chunk_index']}" for c in chunks],
    documents=texts,
    embeddings=embeddings.tolist(),
    metadatas=[
        {"source": c["source"], "chunk_index": c["chunk_index"]}
        for c in chunks
    ],
)

print(f"Stored {collection.count()} chunks in chroma.")
