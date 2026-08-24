from app.ingestion.builders import ChunkBuilder
from app.ingestion.chunk_config import ChunkConfig
from app.ingestion.chunkers import RecursiveChunker
from app.ingestion.overlap import OverlapProcessor
from app.ingestion.processors import TextNormalizer
from app.ingestion.schemas import Document


def main() -> None:
    document = Document(
        content="""
        Health Insurance Fraud Guidelines

        Duplicate invoices may indicate that a medical service has been
        billed more than once. Investigators should compare invoice numbers,
        provider details, treatment dates, and billed amounts.

        Claims submitted repeatedly by the same provider should be compared
        against previous patient records. Unusual claim frequency may indicate
        provider-level fraud.

        Altered documents should be escalated for manual investigation.
        Original source files must be preserved for forensic analysis.
        """,
        source="data/fraud-guidelines.pdf",
        file_type="pdf",
        metadata={
            "document_id": "DOC-2026-001",
            "category": "fraud-guideline",
            "provider": "Example Insurance",
        },
    )

    config = ChunkConfig(
        target_size=260,
        overlap=70,
        min_chunk_size=50,
    )

    normalizer = TextNormalizer()
    chunker = RecursiveChunker(config)
    overlap_processor = OverlapProcessor(config)
    builder = ChunkBuilder()

    normalized_text = normalizer.normalize(document.content)

    segments = chunker.split(normalized_text)

    overlapped_segments = overlap_processor.apply(segments)

    chunks = builder.build_many(
        document=document,
        segments=overlapped_segments,
        strategy="recursive",
        additional_metadata={
            "pipeline_version": "1.0.0",
            "overlap_enabled": config.overlap > 0,
            "requested_overlap": config.overlap,
        },
    )

    print(f"Generated chunks: {len(chunks)}")
    print("=" * 80)

    for chunk in chunks:
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Chunk index: {chunk.chunk_index}")
        print(f"Source: {chunk.source}")
        print(f"Size: {len(chunk.content)}")
        print(f"Metadata: {chunk.metadata}")
        print()
        print(chunk.content)
        print("-" * 80)

        assert len(chunk.chunk_id) == 64
        assert chunk.content.strip()
        assert chunk.metadata["chunk_size"] == len(chunk.content)
        assert chunk.metadata["chunk_index"] == chunk.chunk_index


if __name__ == "__main__":
    main()
