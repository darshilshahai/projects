from app.ingestion import (
    ChunkConfig,
    ChunkingPipeline,
    Document,
)
from app.ingestion.chunkers import RecursiveChunker


def main() -> None:
    document = Document(
        content="""
        Health Insurance Fraud Investigation Guidelines

        Duplicate invoices may indicate that the same medical service was
        billed multiple times. Investigators should compare invoice numbers,
        provider details, treatment dates, diagnosis codes, and billed amounts.

        Claims repeatedly submitted by the same provider should be compared
        against historical patient and provider records. Unusual claim
        frequency may indicate provider-level fraud or coordinated activity.

        Documents containing visible alterations, conflicting dates, replaced
        values, inconsistent fonts, or suspicious signatures should be
        escalated for forensic review. Original source files must be preserved.
        """,
        source="data/fraud-investigation-guidelines.pdf",
        file_type="pdf",
        metadata={
            "document_id": "DOC-2026-001",
            "category": "fraud-guideline",
            "tenant_id": "INSURER-001",
        },
    )

    config = ChunkConfig(
        target_size=260,
        overlap=70,
        min_chunk_size=50,
    )

    chunker = RecursiveChunker(config)

    pipeline = ChunkingPipeline(
        chunker=chunker,
        strategy_name="recursive",
        pipeline_version="1.0.0",
    )

    chunks = pipeline.process(
        document,
        additional_metadata={
            "ingestion_job_id": "JOB-2026-0001",
            "environment": "development",
        },
    )

    print(f"Generated chunks: {len(chunks)}")
    print("=" * 80)

    for chunk in chunks:
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Chunk index: {chunk.chunk_index}")
        print(f"Source: {chunk.source}")
        print(f"Content size: {len(chunk.content)}")
        print(f"Strategy: {chunk.metadata['chunking_strategy']}")
        print(f"Pipeline version: {chunk.metadata['pipeline_version']}")
        print(f"Overlap enabled: {chunk.metadata['overlap_enabled']}")
        print()
        print(chunk.content)
        print("-" * 80)

        assert chunk.content.strip()
        assert len(chunk.content) <= config.target_size
        assert len(chunk.chunk_id) == 64
        assert chunk.metadata["chunk_index"] == chunk.chunk_index
        assert chunk.metadata["chunk_size"] == len(chunk.content)


if __name__ == "__main__":
    main()
