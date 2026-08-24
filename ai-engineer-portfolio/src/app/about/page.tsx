import type { Metadata } from "next";
import { AboutView } from "@/components/sections/about-view";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "About",
  description:
    "About Darshil Shah, an AI Engineer and software developer building production-ready RAG systems, agentic workflows, and scalable AI applications.",
  path: "/about",
});

export default function AboutPage() {
  return <AboutView />;
}
