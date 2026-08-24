from app.ingestion.chunk_config import ChunkConfig
from app.ingestion.chunkers import RecursiveChunker
from app.ingestion.overlap import OverlapProcessor
from app.ingestion.processors import TextNormalizer


def main() -> None:
    raw_text = """
    Duplicate invoices may indicate that the same medical service has been
    billed more than once. Investigators should compare invoice numbers,
    treatment dates, provider details, and billed amounts.

    Repeated claims from the same provider should be compared against previous
    patient records. Unusual claim frequency may indicate provider-level fraud.

    Claims containing altered documents should be escalated for manual review.
    Investigators must preserve the original files for forensic analysis.
    """

    config = ChunkConfig(
        target_size=260,
        overlap=70,
        min_chunk_size=50,
    )

    normalizer = TextNormalizer()
    normalized_text = normalizer.normalize(raw_text)

    chunker = RecursiveChunker(config)
    original_segments = chunker.split(normalized_text)

    overlap_processor = OverlapProcessor(config)
    overlapped_segments = overlap_processor.apply(original_segments)

    print("ORIGINAL SEGMENTS")
    print("=" * 80)

    for index, segment in enumerate(original_segments):
        print(f"Segment {index}")
        print(f"Size: {len(segment)}")
        print(segment)
        print("-" * 80)

    print()
    print("OVERLAPPED SEGMENTS")
    print("=" * 80)

    for index, segment in enumerate(overlapped_segments):
        print(f"Segment {index}")
        print(f"Size: {len(segment)}")
        print(segment)
        print("-" * 80)

        assert segment.strip()
        assert len(segment) <= config.target_size


if __name__ == "__main__":
    main()
