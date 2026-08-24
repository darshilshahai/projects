export const site = {
  name: "Darshil Shah",
  role: "AI Engineer",
  headline:
    "AI Engineer building reliable RAG systems, AI agents, and scalable backend applications.",
  subheadline:
    "I combine strong software engineering foundations with practical AI engineering to build production-ready applications using Python, FastAPI, LangChain, LangGraph, vector databases, Node.js, and modern frontend frameworks.",
  availability: "Open to AI Engineer and AI Application Engineer opportunities",
  email: "darshilshah.ai@gmail.com",
  location: "India",
  locationNote: "Open to remote and relocation",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://darshilshah.dev",
  github: "https://github.com/darshilshahai",
  linkedin: "https://www.linkedin.com/in/ds06/",
  resume: "/resume.pdf",
  metaTitle: "Darshil Shah — AI Engineer | RAG, AI Agents and Backend Systems",
  metaDescription:
    "Portfolio of Darshil Shah, an AI Engineer and software developer building production-ready RAG systems, agentic workflows, streaming APIs, and scalable AI applications.",
} as const;

export type SiteConfig = typeof site;
