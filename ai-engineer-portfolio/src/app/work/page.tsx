import type { Metadata } from "next";
import { WorkView } from "@/components/sections/work-view";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "Work",
  description: "Selected AI engineering and software development work by Darshil Shah.",
  path: "/work",
});

export default function WorkPage() {
  return <WorkView />;
}
