from app.ingestion.chunk_config import ChunkConfig
from app.ingestion.chunkers import RecursiveChunker
from app.ingestion.processors import TextNormalizer


def main() -> None:
    raw_text = """
    Health Insurance Policy

    Hospitalization expenses are covered when the insured person is admitted
    for more than twenty-four hours.

    Fraud Investigation Guidelines

    A claim may be selected for additional investigation when the submitted
    documents contain inconsistent patient details. The system should compare
    invoice dates, admission dates, discharge dates, provider information,
    diagnosis codes, treatment descriptions, duplicate bills, and previously
    submitted claims. Investigators should also examine unusual treatment
    frequency, repeated claims from the same provider, unexpected billing
    amounts, altered documents, and conflicts between medical records and
    submitted invoices.

    Exclusions

    Cosmetic procedures are generally excluded unless they are medically
    necessary following an accident or reconstructive treatment.
    """

    config = ChunkConfig(
        target_size=220,
        overlap=40,
        min_chunk_size=60,
    )

    normalizer = TextNormalizer()
    normalized_text = normalizer.normalize(raw_text)

    chunker = RecursiveChunker(config)
    segments = chunker.split(normalized_text)

    print(f"Generated segments: {len(segments)}")
    print()

    for index, segment in enumerate(segments):
        print(f"Segment {index}")
        print(f"Size: {len(segment)}")
        print(segment)
        print("-" * 80)

        assert segment.strip()
        assert len(segment) <= config.target_size


if __name__ == "__main__":
    main()
