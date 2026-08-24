from app.embeddings import (
    EmbeddingConfig,
    SentenceTransformerEmbedder,
)
from app.ingestion import (
    ChunkConfig,
    ChunkingPipeline,
    Document,
)
from app.ingestion.chunkers import RecursiveChunker
from app.vectorstores import (
    ChromaVectorStore,
    VectorStoreConfig,
)


def main() -> None:
    document = Document(
        content="""
        Health Insurance Fraud Investigation Guidelines

        Duplicate invoices may indicate that the same medical service was
        billed more than once. Investigators should compare invoice numbers,
        provider names, treatment dates, and billed amounts.

        Repeated claims submitted by the same provider should be checked
        against historical records. Unusual claim frequency may indicate
        provider-level fraud.

        Altered invoices, conflicting dates, modified amounts, and suspicious
        signatures should be escalated for manual investigation.

        Cosmetic procedures are generally excluded unless they are medically
        necessary following an accident or reconstructive treatment.
        """,
        source="data/fraud-guidelines.pdf",
        file_type="pdf",
        metadata={
            "document_id": "DOC-001",
            "tenant_id": "INSURER-001",
            "category": "fraud-guideline",
        },
    )

    chunk_config = ChunkConfig(
        target_size=250,
        overlap=50,
        min_chunk_size=40,
    )

    chunking_pipeline = ChunkingPipeline(
        chunker=RecursiveChunker(chunk_config),
        strategy_name="recursive",
        pipeline_version="1.0.0",
    )

    chunks = chunking_pipeline.process(document)

    embedding_config = EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=16,
        normalize_embeddings=True,
        device=None,
    )

    embedder = SentenceTransformerEmbedder(embedding_config)

    embedding_batch = embedder.embed_chunks(chunks)

    vector_store_config = VectorStoreConfig(
        persist_directory="data/chroma",
        collection_name="insurance_fraud_documents",
        distance_metric="cosine",
        expected_dimension=embedder.dimension,
    )

    vector_store = ChromaVectorStore(vector_store_config)

    inserted_count = vector_store.upsert(embedding_batch)

    print(f"Chunks generated: {len(chunks)}")
    print(f"Vectors stored: {inserted_count}")
    print(f"Collection count: {vector_store.count()}")
    print("=" * 80)

    question = "What signs indicate duplicate billing fraud?"

    query_vector = embedder.embed_query(question)

    search_results = vector_store.search(
        query_vector,
        top_k=3,
        query=question,
        where={
            "tenant_id": "INSURER-001",
        },
    )

    print(f"Question: {question}")
    print(f"Results found: {len(search_results)}")
    print("=" * 80)

    for result in search_results.results:
        print(f"Rank: {result.rank}")
        print(f"Chunk ID: {result.id}")
        print(f"Distance: {result.distance:.4f}")
        print(f"Score: {result.score:.4f}")
        print(f"Source: {result.metadata.get('source')}")
        print(f"Category: {result.metadata.get('category')}")
        print()
        print(result.document)
        print("-" * 80)


if __name__ == "__main__":
    main()
