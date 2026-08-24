from app.core.config import get_settings
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
from app.llm import (
    LLMConfig,
    OpenAILLM,
)
from app.retrieval import (
    RetrievalConfig,
    SemanticRetriever,
)
from app.services import RAGService
from app.vectorstores import (
    ChromaVectorStore,
    VectorStoreConfig,
)


def main() -> None:
    settings = get_settings()

    # ---------------------------------------------------------
    # 1. Create source document
    # ---------------------------------------------------------

    document = Document(
        content="""
        Health Insurance Fraud Investigation Guidelines

        Duplicate invoices may indicate that the same medical service was
        billed more than once. Investigators should compare invoice numbers,
        provider names, treatment dates, diagnosis details, and billed amounts.

        Repeated claims from the same provider should be compared with
        historical claim records. Unusual claim frequency may indicate
        provider-level fraud.

        Altered invoices, modified billing amounts, conflicting dates, and
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

    # ---------------------------------------------------------
    # 2. Chunk the document
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 3. Generate embeddings
    # ---------------------------------------------------------

    embedding_config = EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=16,
        normalize_embeddings=True,
        device=None,
    )

    embedder = SentenceTransformerEmbedder(embedding_config)

    embedding_batch = embedder.embed_chunks(chunks)

    # ---------------------------------------------------------
    # 4. Store vectors
    # ---------------------------------------------------------

    vector_store_config = VectorStoreConfig(
        persist_directory="data/chroma",
        collection_name="insurance_fraud_documents",
        distance_metric="cosine",
        expected_dimension=embedder.dimension,
    )

    vector_store = ChromaVectorStore(vector_store_config)

    vector_store.upsert(embedding_batch)

    # ---------------------------------------------------------
    # 5. Create retriever
    # ---------------------------------------------------------

    retrieval_config = RetrievalConfig(
        top_k=3,
        fetch_k=8,
        minimum_score=None,
        maximum_context_characters=3_000,
        remove_duplicate_content=True,
        include_metadata=True,
    )

    retriever = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
        config=retrieval_config,
    )

    # ---------------------------------------------------------
    # 6. Create LLM
    # ---------------------------------------------------------

    llm_config = LLMConfig(
        model_name=settings.openai_model,
        api_key=settings.openai_api_key,
        max_output_tokens=700,
        timeout_seconds=60,
        max_retries=2,
    )

    llm = OpenAILLM(llm_config)

    # ---------------------------------------------------------
    # 7. Create RAG service
    # ---------------------------------------------------------

    rag_service = RAGService(
        retriever=retriever,
        llm=llm,
    )

    # ---------------------------------------------------------
    # 8. Ask a question
    # ---------------------------------------------------------

    question = "What signs may indicate duplicate billing fraud?"

    response = rag_service.ask(
        question,
        where={
            "tenant_id": "INSURER-001",
        },
    )

    print("=" * 80)
    print("QUESTION")
    print("=" * 80)
    print(response.question)

    print()
    print("=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(response.answer)

    print()
    print("=" * 80)
    print("SOURCES")
    print("=" * 80)

    for source in response.sources:
        print(f"Source number: {source.number}")
        print(f"Chunk ID: {source.chunk_id}")
        print(f"Source: {source.source}")
        print(f"Score: {source.score:.4f}")
        print(f"Preview: {source.content_preview}")
        print("-" * 80)

    print()
    print("=" * 80)
    print("MODEL INFORMATION")
    print("=" * 80)
    print(f"Provider: {response.provider}")
    print(f"Model: {response.model_name}")
    print(f"Response ID: {response.response_id}")
    print(f"Input tokens: {response.input_tokens}")
    print(f"Output tokens: {response.output_tokens}")
    print(f"Total tokens: {response.total_tokens}")


if __name__ == "__main__":
    main()
