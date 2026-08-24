import type { Metadata } from "next";
import { WritingView } from "@/components/sections/writing-view";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "Writing",
  description:
    "Technical writing on RAG, agentic AI, streaming APIs, and production AI engineering by Darshil Shah.",
  path: "/writing",
});

export default function WritingPage() {
  return <WritingView />;
}
