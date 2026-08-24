from app.ingestion.chunk_config import ChunkConfig
from app.ingestion.processors import TextNormalizer
from app.ingestion.schemas import Document


def main() -> None:
    document = Document(
        content=(
            "Health Insurance Policy   \r\n"
            "\r\n"
            "\r\n"
            "Hospitalization expenses are covered.   \r\n"
        ),
        source="data/health-policy.pdf",
        file_type=".PDF",
        metadata={
            "policy_id": "POL-2026-001",
        },
    )

    config = ChunkConfig(
        target_size=1_000,
        overlap=150,
        min_chunk_size=100,
    )

    normalizer = TextNormalizer()
    normalized_content = normalizer.normalize(document.content)

    print("Source:", document.source)
    print("File type:", document.file_type)
    print("Target size:", config.target_size)
    print("Normalized content:")
    print(repr(normalized_content))


if __name__ == "__main__":
    main()
