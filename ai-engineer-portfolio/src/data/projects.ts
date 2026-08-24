import type { Project } from "@/types";

// GitHub URLs are placeholders — point them at the real repositories.
// Results are written qualitatively on purpose: replace them with measured
// numbers when available instead of inventing metrics.
export const projects: Project[] = [
  {
    slug: "fraud-detection-rag",
    title: "Fraud Detection RAG",
    tagline:
      "A production-oriented retrieval system that examines healthcare claims and surfaces evidence-backed fraud signals.",
    summary:
      "Retrieval-augmented analysis over healthcare claim documents: ingestion, chunking, vector search with metadata filters, and streamed answers with source citations and extracted fraud signals.",
    terminal: "Claim docs · Parser · Chunker · Embeddings",
    problemShort:
      "Claims teams need to find suspicious patterns across long, inconsistent documents without trusting an opaque model verdict.",
    problem:
      "Claim reviewers work through long, inconsistent document sets by hand. Potential fraud indicators — duplicate billing, mismatched dates, unusual provider patterns — are spread across many pages, so review is slow and signals get missed.",
    solutionShort:
      "A citation-first RAG pipeline combines custom chunking, metadata filters, tenant isolation, semantic retrieval, and streamed structured findings.",
    solution:
      "A FastAPI service ingests claim documents, chunks them with a paragraph-first strategy (recursive fallback for dense text), embeds chunks with SentenceTransformers, and stores them in ChromaDB with tenant and document-type metadata. Queries run filtered vector search, build a bounded context window, and stream an LLM analysis over SSE with per-claim citations and structured fraud-signal extraction via Pydantic models.",
    coreCapabilities: [
      "Multi-tenant retrieval",
      "Streaming with citations",
      "Fraud signal extraction",
      "Evaluation-ready pipeline",
    ],
    decisions: [
      "Local SentenceTransformers embeddings instead of a hosted embedding API — predictable cost and no document content leaving the environment.",
      "Paragraph-first chunking with a recursive character splitter as fallback, because claim documents mix narrative sections with dense tables.",
      "Metadata filtering (tenant, document type, date range) applied before vector search, so retrieval never crosses tenant boundaries.",
      "SSE instead of WebSockets for response streaming — the stream is one-way, and SSE keeps the infrastructure plain HTTP.",
      "Structured output validated with Pydantic so fraud signals are machine-readable, not prose that needs re-parsing.",
    ],
    challenges: [
      "Chunk boundaries splitting tables and itemised charges — solved by detecting table-like blocks and keeping them whole.",
      "Balancing retrieval recall against the context budget: more chunks improved recall but diluted answer quality past a threshold.",
      "Keeping citations stable when the same source paragraph appears in multiple retrieved chunks.",
      "Making streamed responses cancellable server-side so abandoned requests stop consuming LLM tokens.",
    ],
    results: [
      "Reviewers get a cited summary of suspicious patterns instead of reading full document sets. (Replace with measured review-time numbers.)",
      "Every claim in the output links back to its source chunk, which made spot-checking answers practical.",
      "The retrieval layer is isolated behind an interface, so chunking and embedding changes can be evaluated without touching the API.",
    ],
    futureWork: [
      "Add a golden-question evaluation set with retrieval hit-rate tracking.",
      "Introduce a reranking stage (cross-encoder) between retrieval and context building.",
      "Expose confidence scoring on extracted fraud signals.",
    ],
    stack: ["Python", "FastAPI", "LangChain", "ChromaDB", "SentenceTransformers"],
    architecture: [
      { label: "Claim docs" },
      { label: "Parser" },
      { label: "Chunker" },
      { label: "Embeddings" },
      { label: "Vector DB" },
      { label: "Retriever" },
      { label: "LLM" },
      { label: "Cited response" },
    ],
    snippet: {
      title: "Filtered retrieval with streamed, cited output",
      language: "python",
      code: `async def stream_analysis(query: AnalysisQuery) -> AsyncIterator[str]:
    chunks = retriever.search(
        text=query.question,
        where={
            "tenant_id": query.tenant_id,
            "doc_type": {"$in": query.doc_types},
        },
        k=8,
    )
    context = build_context(chunks, max_tokens=3000)

    async for event in llm.stream_structured(
        system=FRAUD_ANALYST_PROMPT,
        context=context,
        question=query.question,
        schema=FraudFindings,
    ):
        if event.type == "token":
            yield sse(event.text)
        elif event.type == "citation":
            yield sse_json({"source": event.chunk.source_ref})`,
    },
    githubUrl: "https://github.com/darshilshahai/fraud-detection-rag",
    featured: true,
  },
  {
    slug: "northwind-rag-assistant",
    title: "Northwind RAG Assistant",
    tagline:
      "A grounded business assistant built around a custom, structure-aware retrieval pipeline.",
    summary:
      "A document assistant with a custom chunking pipeline — heading-aware merging and sentence overlap — persistent vector storage, and context-grounded answers over company documentation.",
    terminal: "Documents · Heading parser · Chunk merge · Embedding",
    problemShort:
      "Naive fixed-size chunking cuts across section boundaries, so retrieval returns fragments and answers drift from the source.",
    problem:
      "Company documents are written for humans: headings, nested sections, short paragraphs. Naive fixed-size chunking cuts across section boundaries, so retrieval returns fragments with no context and answers drift away from the source material.",
    solutionShort:
      "A structure-aware chunker merges short blocks under their headings with sentence overlap, keeping every retrieved chunk anchored to its section.",
    solution:
      "A custom chunking pipeline walks the document structure, merges short blocks under their parent heading, and adds sentence-level overlap between neighbours. Chunks are embedded with SentenceTransformers and stored in a persistent ChromaDB collection. At query time, semantic retrieval feeds a context builder that keeps heading paths visible to the LLM, so answers stay grounded in the right section.",
    coreCapabilities: [
      "Heading-aware chunking",
      "Sentence-overlap windows",
      "Persistent vector storage",
      "Grounded answers",
    ],
    decisions: [
      "Chunking is a standalone, testable pipeline stage that writes inspectable JSON — debugging retrieval starts with looking at actual chunks.",
      "Heading paths (e.g. 'Returns Policy > International Orders') are embedded with the chunk text, which measurably improved retrieval for short sections.",
      "Sentence overlap instead of token overlap, so chunk boundaries never split a sentence.",
      "Persistent Chroma collections keyed by document version, so re-ingestion is explicit rather than accidental.",
    ],
    challenges: [
      "Very short sections (two-line policies) embedding poorly on their own — solved by merging them upward into their heading group.",
      "Deciding merge thresholds: too aggressive and chunks span topics, too conservative and context fragments return.",
      "Keeping ingestion idempotent so running the pipeline twice never duplicates vectors.",
    ],
    results: [
      "Answers cite the section they came from, and retrieval no longer returns orphaned fragments without their headings.",
      "The chunk inspector made retrieval failures explainable — most traced back to chunk boundaries, not the model.",
    ],
    futureWork: [
      "Side-by-side evaluation harness comparing chunking strategies on a fixed question set.",
      "Hybrid retrieval combining BM25 keyword scores with vector similarity.",
    ],
    stack: ["Python", "FastAPI", "LangChain", "ChromaDB", "SentenceTransformers"],
    architecture: [
      { label: "Documents" },
      { label: "Structure parser" },
      { label: "Chunk merge" },
      { label: "Overlap pass" },
      { label: "Embeddings" },
      { label: "ChromaDB" },
      { label: "Retriever" },
      { label: "Grounded answer" },
    ],
    snippet: {
      title: "Heading-aware merge with sentence overlap",
      language: "python",
      code: `def merge_section(section: Section, min_chars: int = 350) -> list[Chunk]:
    chunks: list[Chunk] = []
    buffer: list[Block] = []

    for block in section.blocks:
        buffer.append(block)
        if sum(len(b.text) for b in buffer) >= min_chars:
            chunks.append(
                Chunk(
                    text=join_blocks(buffer),
                    heading_path=section.heading_path,
                )
            )
            buffer = [buffer[-1]]  # carry last block forward as overlap

    if buffer:
        chunks.append(
            Chunk(text=join_blocks(buffer), heading_path=section.heading_path)
        )
    return chunks`,
    },
    githubUrl: "https://github.com/darshilshahai/northwind-rag-assistant",
    featured: true,
  },
  {
    slug: "promptforge",
    title: "PromptForge",
    tagline:
      "A streaming AI API platform with persistent conversations, caching, and provider-ready architecture.",
    summary:
      "An AI backend platform: token streaming to the client, PostgreSQL-backed conversation history, Redis caching, request validation, and a provider abstraction that keeps model vendors swappable.",
    terminal: "React · FastAPI · Provider · Stream",
    problemShort:
      "Most AI integrations start as a single OpenAI call and grow into a tangle with no persistence, caching, or clean provider boundary.",
    problem:
      "Most AI integrations start as a single OpenAI call and grow into a tangle: no conversation persistence, no caching, provider lock-in, and no clean place to add validation or rate limits. Teams need AI behind a real API surface.",
    solutionShort:
      "A FastAPI platform treats the LLM as one dependency among many: persistence, caching, validation, and streaming built in from the start.",
    solution:
      "Conversations and messages persist in PostgreSQL, hot conversation context is cached in Redis, every request passes schema validation, and providers sit behind a small interface so OpenAI can be swapped or multiplexed without touching route code. Responses stream token-by-token to a React client.",
    coreCapabilities: [
      "Token streaming",
      "Conversation persistence",
      "Redis context cache",
      "Provider abstraction",
    ],
    decisions: [
      "Conversation context is rebuilt from PostgreSQL but cached in Redis with a short TTL — repeat turns skip the database entirely.",
      "The provider interface exposes only complete(), stream(), and count_tokens(), which kept the abstraction honest and swappable.",
      "Messages are written before the LLM call and finalised after, so a crashed stream never loses the user's input.",
      "Streaming uses an async generator end-to-end; backpressure is handled by the ASGI server rather than manual buffering.",
    ],
    challenges: [
      "Persisting a response that is still streaming: solved with a pending message row finalised on stream completion or error.",
      "Cache invalidation on conversation edits — the TTL-plus-explicit-invalidation combination proved simpler than event-driven invalidation.",
      "Keeping token counting consistent between providers with different tokenizers.",
    ],
    results: [
      "New providers can be added in one module without route changes.",
      "Cached context reads avoid a PostgreSQL round-trip on active conversations. (Replace with measured cache hit rates.)",
      "The same platform now backs multiple internal prototypes instead of each one re-implementing OpenAI calls.",
    ],
    futureWork: [
      "Per-API-key rate limiting and usage metering.",
      "Structured tool-calling support across providers.",
      "OpenTelemetry tracing across the request, provider, and stream path.",
    ],
    stack: ["FastAPI", "PostgreSQL", "Redis", "OpenAI", "React"],
    architecture: [
      { label: "React client" },
      { label: "FastAPI" },
      { label: "Redis cache" },
      { label: "PostgreSQL" },
      { label: "Provider layer" },
      { label: "Token stream" },
    ],
    snippet: {
      title: "Cache-aware context loading",
      language: "python",
      code: `async def load_context(conversation_id: str) -> list[Message]:
    cached = await redis.get(ctx_key(conversation_id))
    if cached is not None:
        return Message.parse_list(cached)

    messages = await db.fetch_recent_messages(
        conversation_id, limit=MAX_CONTEXT_MESSAGES
    )
    await redis.set(
        ctx_key(conversation_id),
        Message.dump_list(messages),
        ex=CONTEXT_TTL_SECONDS,
    )
    return messages`,
    },
    githubUrl: "https://github.com/darshilshahai/promptforge",
    featured: false,
  },
  {
    slug: "ai-email-scheduler",
    title: "AI Email Scheduler",
    tagline:
      "Personalised email generation and scheduled delivery driven by spreadsheet data.",
    summary:
      "Turns spreadsheet rows into personalised, scheduled email campaigns: AI-generated subjects and body content, Excel and Google Sheets ingestion, scheduling workflows, and delivery tracking.",
    terminal: "Sheet · Validator · LLM · Approval",
    problemShort:
      "Outreach run from spreadsheets is slow, error-prone, and impossible to track at any scale.",
    problem:
      "Small teams run outreach from spreadsheets: hundreds of rows, manually copied into emails, personalised by hand, sent at the wrong times. It is slow, error-prone, and impossible to track.",
    solutionShort:
      "AI drafts personalised subjects and bodies from row data; humans approve; software schedules and tracks delivery.",
    solution:
      "A FastAPI backend ingests Excel or Google Sheets data, uses an LLM to draft personalised subjects and bodies from row fields, and queues sends through a scheduling workflow with per-recipient delivery status. A React dashboard covers review, editing, and approval — generated emails are drafts until a human approves them.",
    coreCapabilities: [
      "AI-drafted content",
      "Spreadsheet ingestion",
      "Human approval gate",
      "Delivery tracking",
    ],
    decisions: [
      "Generation and sending are strictly separated stages — nothing sends without explicit approval.",
      "Spreadsheet parsing normalises column names and flags missing personalisation fields instead of silently sending broken emails.",
      "Scheduled sends run through a background job queue, keeping API responses fast and retries isolated.",
    ],
    challenges: [
      "Inconsistent spreadsheet data: half the engineering effort was validation and normalisation before any AI involvement.",
      "Making LLM output respect strict length and tone constraints for subject lines.",
      "Idempotent send jobs so a retried job never emails the same recipient twice.",
    ],
    results: [
      "Campaign preparation went from manual per-row editing to review-and-approve. (Replace with measured prep-time numbers.)",
      "Delivery status is visible per recipient instead of buried in a sent folder.",
    ],
    futureWork: [
      "Reply-detection loop to pause sequences automatically.",
      "A/B testing generated subject-line variants.",
    ],
    stack: ["FastAPI", "React", "Google Sheets", "LLM APIs", "PostgreSQL"],
    architecture: [
      { label: "Spreadsheet" },
      { label: "Ingestion" },
      { label: "LLM draft" },
      { label: "Review UI" },
      { label: "Scheduler" },
      { label: "Delivery" },
    ],
    githubUrl: "https://github.com/darshilshahai/ai-email-scheduler",
    featured: false,
  },
  {
    slug: "url-shortener",
    title: "URL Shortener",
    tagline:
      "A read-heavy redirect service designed around fast short-code lookup and cache-aside access.",
    summary:
      "A read-heavy systems design exercise made real: short-code generation, Redis cache-aside redirects, database persistence, and a partitioning concept for horizontal growth.",
    terminal: "Client · Redirect API · Redis · Database",
    problemShort:
      "A single popular link produces orders of magnitude more redirects than creations — hitting the database for each one wastes the hot path.",
    problem:
      "URL shorteners are write-light and read-heavy — a single popular link can produce orders of magnitude more redirects than creations. Hitting the database for every redirect wastes the most common request in the system.",
    solutionShort:
      "Redirects follow a cache-aside pattern: Redis first, database on miss, with collision-safe codes and a partition-ready schema.",
    solution:
      "An Express service where redirects follow a cache-aside pattern: Redis first, database on miss, then populate the cache with a TTL. Short codes are generated collision-checked and indexed for direct lookup, and the schema is designed so short-code ranges could partition across shards as read volume grows.",
    coreCapabilities: [
      "Cache-aside reads",
      "Collision-safe codes",
      "Hot-path redirects",
      "Partition-ready schema",
    ],
    decisions: [
      "Cache-aside over write-through: most created links are never visited, so caching on first read avoids filling Redis with cold entries.",
      "Redirects return 302 rather than 301 so destinations stay editable and hit counting stays possible.",
      "Base62 codes over sequential IDs to avoid making creation volume guessable.",
    ],
    challenges: [
      "Cache stampede on a suddenly-popular link — bounded by short lock-and-fill on miss.",
      "Deciding TTLs that balance memory use against hit rate for a long-tail access pattern.",
    ],
    results: [
      "Cache hits serve redirects without touching the database. (Replace with measured hit-rate and latency numbers.)",
      "The service degrades gracefully: Redis loss means slower redirects, not downtime.",
    ],
    futureWork: [
      "Click analytics with an async event pipeline.",
      "Custom vanity codes with reserved-word handling.",
    ],
    stack: ["Node.js", "Redis", "MongoDB", "REST"],
    architecture: [
      { label: "Client" },
      { label: "Redirect API" },
      { label: "Redis" },
      { label: "Database" },
      { label: "302 redirect" },
    ],
    githubUrl: "https://github.com/darshilshahai/url-shortener",
    featured: false,
  },
  {
    slug: "brandvoice-agent",
    title: "BrandVoice Agent",
    tagline:
      "A human-in-the-loop content workflow spanning research, writing, voice consistency, and scheduling.",
    summary:
      "A LangGraph multi-agent system: a research agent gathers material, a copywriting agent drafts, brand-voice memory keeps output consistent, and a human approval gate sits before scheduling.",
    terminal: "Brief · Research · Copy agent · Brand check",
    problemShort:
      "Single-prompt content generation produces generic copy that drifts off brand voice and still needs manual scheduling.",
    problem:
      "Content teams need output that is researched, on-brand, and scheduled — three different jobs. A single-prompt approach produces generic copy that drifts off brand voice and still needs manual scheduling.",
    solutionShort:
      "Specialised LangGraph agents share explicit state: research gathers, copywriting drafts against brand-voice memory, and humans approve before anything ships.",
    solution:
      "A LangGraph workflow with specialised agents: research collects and summarises source material, copywriting drafts against a persistent brand-voice memory (tone rules, phrasing examples, banned patterns), and a review state routes every draft through human approval before the scheduling integration queues it. Failed steps route to recovery states instead of crashing the run.",
    coreCapabilities: [
      "Multi-agent workflow",
      "Brand-voice memory",
      "Human approval gate",
      "Error recovery states",
    ],
    decisions: [
      "LangGraph over a hand-rolled loop: explicit states and edges made the workflow debuggable and resumable.",
      "Brand voice lives in structured memory (rules + examples), not in an ever-growing prompt.",
      "Approval is a first-class graph state, so a human decision is just another transition — pause and resume come free.",
      "Each agent has its own bounded toolset; the research agent cannot schedule and the scheduler cannot rewrite copy.",
    ],
    challenges: [
      "Keeping shared state minimal: early versions passed everything everywhere, which made failures hard to trace.",
      "Preventing brand-voice drift over long sessions — solved by re-injecting voice rules at each drafting step rather than relying on conversation history.",
      "Designing retries that distinguish transient tool failures from unrecoverable input problems.",
    ],
    results: [
      "Drafts arrive researched and on-voice, with humans deciding instead of rewriting.",
      "Workflow runs are resumable after failures instead of restarting from scratch.",
    ],
    futureWork: [
      "Voice-consistency scoring as an automated evaluation step.",
      "Multi-channel scheduling with per-platform formatting agents.",
    ],
    stack: ["LangGraph", "Python", "n8n", "LLM APIs", "PostgreSQL"],
    architecture: [
      { label: "Brief" },
      { label: "Research agent" },
      { label: "Copy agent" },
      { label: "Brand check" },
      { label: "Approval" },
      { label: "Scheduler" },
    ],
    githubUrl: "https://github.com/darshilshahai/brandvoice-agent",
    featured: false,
  },
];

export function getProject(slug: string) {
  return projects.find((project) => project.slug === slug);
}
