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


def main() -> None:
    document = Document(
        content="""
        Health Insurance Fraud Guidelines

        Duplicate invoices may indicate that the same medical treatment was
        billed more than once. Investigators should compare invoice numbers,
        provider details, treatment dates, and billed amounts.

        Claims repeatedly submitted by the same provider should be checked
        against historical records. Unusual claim frequency may indicate
        provider-level fraud.

        Altered invoices and conflicting medical documents should be escalated
        for manual investigation.
        """,
        source="data/fraud-guidelines.pdf",
        file_type="pdf",
        metadata={
            "document_id": "DOC-001",
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
        show_progress_bar=False,
    )

    embedder = SentenceTransformerEmbedder(embedding_config)

    embedding_batch = embedder.embed_chunks(chunks)

    print(f"Chunks generated: {len(chunks)}")
    print(f"Embeddings generated: {len(embedding_batch)}")
    print(f"Model: {embedding_batch.model_name}")
    print(f"Dimension: {embedding_batch.dimension}")
    print(f"Normalized: {embedding_batch.normalized}")
    print("=" * 80)

    for index, chunk in enumerate(chunks):
        vector = embedding_batch.vectors[index]

        print(f"Chunk ID: {embedding_batch.ids[index]}")
        print(f"Chunk index: {chunk.chunk_index}")
        print(f"Text size: {len(chunk.content)}")
        print(f"Vector dimension: {len(vector)}")
        print(f"First five values: {vector[:5]}")
        print()
        print(chunk.content)
        print("-" * 80)

        assert embedding_batch.ids[index] == chunk.chunk_id
        assert embedding_batch.texts[index] == chunk.content
        assert len(vector) == embedding_batch.dimension


if __name__ == "__main__":
    main()
