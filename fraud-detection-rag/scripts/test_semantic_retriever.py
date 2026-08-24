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
from app.retrieval import (
    RetrievalConfig,
    SemanticRetriever,
)
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
        treatment dates, provider names, and billed amounts.

        Claims repeatedly submitted by the same provider should be compared
        with previous claim records. Unusual claim frequency may indicate
        provider-level fraud.

        Altered invoices, conflicting treatment dates, modified amounts, and
        suspicious signatures should be escalated for manual investigation.

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

    # ------------------------------------------------------------
    # Step 1: Create chunks
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Step 2: Create embeddings
    # ------------------------------------------------------------

    embedding_config = EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=16,
        normalize_embeddings=True,
        device=None,
    )

    embedder = SentenceTransformerEmbedder(embedding_config)

    embedding_batch = embedder.embed_chunks(chunks)

    # ------------------------------------------------------------
    # Step 3: Store embeddings
    # ------------------------------------------------------------

    vector_store_config = VectorStoreConfig(
        persist_directory="data/chroma",
        collection_name="insurance_fraud_documents",
        distance_metric="cosine",
        expected_dimension=embedder.dimension,
    )

    vector_store = ChromaVectorStore(vector_store_config)

    vector_store.upsert(embedding_batch)

    # ------------------------------------------------------------
    # Step 4: Create retriever
    # ------------------------------------------------------------

    retrieval_config = RetrievalConfig(
        top_k=3,
        fetch_k=8,
        minimum_score=None,
        maximum_context_characters=2_000,
        remove_duplicate_content=True,
        include_metadata=True,
    )

    retriever = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
        config=retrieval_config,
    )

    # ------------------------------------------------------------
    # Step 5: Retrieve relevant chunks
    # ------------------------------------------------------------

    question = "What signs indicate duplicate billing fraud?"

    result = retriever.retrieve(
        question,
        where={
            "tenant_id": "INSURER-001",
        },
    )

    print(f"Question: {result.query}")
    print(f"Candidates considered: {result.candidates_considered}")
    print(f"Chunks selected: {len(result)}")
    print(f"Chunks filtered: {result.filtered_count}")
    print(f"Total context characters: {result.total_context_characters}")
    print("=" * 80)

    for chunk in result.chunks:
        print(f"Rank: {chunk.rank}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Score: {chunk.score:.4f}")
        print(f"Distance: {chunk.distance:.4f}")
        print(f"Source: {chunk.source}")
        print()
        print(chunk.content)
        print("-" * 80)

    print()
    print("FINAL RETRIEVAL CONTEXT")
    print("=" * 80)
    print(result.context)


if __name__ == "__main__":
    main()
