import type { Article } from "@/types";

// Add an `href` when a piece is published and the card becomes a link.
export const articles: Article[] = [
  {
    title: "Chunking strategies that survive production",
    summary:
      "Why fixed-size chunking fails on structured documents, and how heading-aware merging with sentence overlap changes retrieval quality.",
    category: "RAG SYSTEMS",
    status: "Draft",
    year: "2026",
    readingTime: "8 min",
  },
  {
    title: "Why async matters for AI applications",
    summary:
      "Async generators, SSE formatting, client cancellation, and persisting a message that is still being written.",
    category: "BACKEND",
    status: "Draft",
    year: "2026",
    readingTime: "6 min",
  },
  {
    title: "What negative cosine similarity actually means",
    summary:
      "Embeddings, similarity scores, and the geometry behind semantic search — explained without hand-waving.",
    category: "AI FUNDAMENTALS",
    status: "Draft",
    year: "2026",
    readingTime: "4 min",
  },
  {
    title: "Evaluating RAG systems without fooling yourself",
    summary:
      "Golden question sets, retrieval hit rate, groundedness checks, and why demo-driven iteration produces worse systems.",
    category: "EVALUATION",
    status: "Draft",
    year: "2026",
    readingTime: "7 min",
  },
];
