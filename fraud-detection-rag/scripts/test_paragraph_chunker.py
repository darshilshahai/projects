from app.ingestion.chunk_config import ChunkConfig
from app.ingestion.chunkers import ParagraphChunker
from app.ingestion.processors import TextNormalizer


def main() -> None:
    raw_text = """
    Health Insurance Policy

    Hospitalization expenses are covered when the insured person is admitted
    for more than twenty-four hours.

    Cosmetic treatments are not covered unless they are medically necessary
    due to an accident or reconstructive procedure.

    Claims must be submitted within thirty days of discharge.

    Investigation may be initiated when submitted documents contain
    inconsistencies, altered invoices, duplicate bills, conflicting patient
    details, unusual treatment patterns, or suspicious provider information.
    """

    config = ChunkConfig(
        target_size=180,
        overlap=30,
        min_chunk_size=50,
    )

    normalizer = TextNormalizer()
    normalized_text = normalizer.normalize(raw_text)

    chunker = ParagraphChunker(config)
    segments = chunker.split(normalized_text)

    print(f"Generated segments: {len(segments)}")
    print()

    for index, segment in enumerate(segments):
        print(f"Segment {index}")
        print(f"Size: {len(segment)}")
        print(repr(segment))
        print("-" * 80)


if __name__ == "__main__":
    main()
