"use client";

import { useState } from "react";

import { AskPanel } from "./components/ask-panel";
import { DocumentUpload } from "./components/document-upload";
import { ThemeSwitcher } from "./components/theme-switcher";

export default function Home() {
  const [healthRefreshKey, setHealthRefreshKey] = useState(0);

  return (
    <main className="mx-auto w-full max-w-2xl px-5 py-14 sm:py-20">
      <header className="mb-10 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">
            Northwind document assistant
          </h1>
          <p className="mt-2 text-base leading-7 text-muted">
            Retrieval-augmented answers over your document corpus. Add sources,
            ask questions, and inspect the chunks behind every answer.
          </p>
        </div>
        <ThemeSwitcher />
      </header>

      <div className="flex flex-col gap-10">
        <DocumentUpload
          onIndexed={() => setHealthRefreshKey((key) => key + 1)}
        />
        <AskPanel healthRefreshKey={healthRefreshKey} />
      </div>
    </main>
  );
}
