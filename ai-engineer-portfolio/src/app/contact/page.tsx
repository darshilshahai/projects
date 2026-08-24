import type { Metadata } from "next";
import { ContactView } from "@/components/sections/contact-view";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "Contact",
  description:
    "Start a project with Darshil Shah — AI Engineer available for RAG systems, agentic workflows, and full-stack AI product work.",
  path: "/contact",
});

export default function ContactPage() {
  return <ContactView />;
}
