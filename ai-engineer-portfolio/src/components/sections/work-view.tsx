"use client";

import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Grid2X2, Menu } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { LaunchLoader } from "@/components/layout/launch-loader";
import { ContactBand } from "@/components/layout/contact-band";
import { projects } from "@/data/projects";
import { getProjectMeta, type ProjectFilter } from "@/data/project-meta";

type Filter = "All" | ProjectFilter;

export function WorkView() {
  const rootRef = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();
  const [filter, setFilter] = useState<Filter>("All");
  const [view, setView] = useState<"list" | "grid">("list");
  const [active, setActive] = useState<number | null>(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });

  const filtered = useMemo(
    () =>
      projects.filter((p) => {
        if (filter === "All") return true;
        return getProjectMeta(p.slug).filters.includes(filter);
      }),
    [filter],
  );

  const counts = {
    All: projects.length,
    AI: projects.filter((p) => getProjectMeta(p.slug).filters.includes("AI")).length,
    Development: projects.filter((p) => getProjectMeta(p.slug).filters.includes("Development")).length,
  };

  const movePreview = (e: React.PointerEvent, index: number) => {
    setActive(index);
    if (e.pointerType === "touch") return;
    setPointer({ x: e.clientX, y: e.clientY });
  };

  return (
    <main className="work-page" id="main" ref={rootRef}>
      <LaunchLoader words={["Work"]} hold={850} />
      <Navbar />

      <div className="shell page-hero">
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          Selected work across AI systems and product engineering.
        </motion.h1>
      </div>

      <div className="shell">
        <div className="work-toolbar">
          <div className="work-filters" role="tablist" aria-label="Filter projects">
            {(["All", "AI", "Development"] as const).map((item) => (
              <button
                key={item}
                type="button"
                role="tab"
                aria-selected={filter === item}
                className={filter === item ? "is-active" : ""}
                onClick={() => setFilter(item)}
              >
                {item} ({counts[item]})
              </button>
            ))}
          </div>
          <div className="work-view-toggle">
            <button
              type="button"
              className={view === "list" ? "is-active" : ""}
              onClick={() => setView("list")}
              aria-label="List view"
              aria-pressed={view === "list"}
            >
              <Menu size={16} />
            </button>
            <button
              type="button"
              className={view === "grid" ? "is-active" : ""}
              onClick={() => setView("grid")}
              aria-label="Grid view"
              aria-pressed={view === "grid"}
            >
              <Grid2X2 size={16} />
            </button>
          </div>
        </div>

        <AnimatePresence mode="wait">
          {view === "list" ? (
            <motion.div
              key={`list-${filter}`}
              className="work-archive"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onPointerLeave={() => setActive(null)}
            >
              <div className="work-archive-head">
                <span>Project</span>
                <span>Location</span>
                <span>Services</span>
                <span>Year</span>
              </div>
              {filtered.map((project) => {
                const index = projects.findIndex((p) => p.slug === project.slug);
                const meta = getProjectMeta(project.slug);
                return (
                  <Link
                    key={project.slug}
                    href={`/projects/${project.slug}`}
                    className={active === index ? "is-active" : ""}
                    onPointerEnter={(e) => movePreview(e, index)}
                    onPointerMove={(e) => movePreview(e, index)}
                    onFocus={() => setActive(index)}
                    onBlur={() => setActive(null)}
                  >
                    <strong>{project.title}</strong>
                    <span>{meta.location}</span>
                    <span>{meta.services}</span>
                    <span>{meta.year}</span>
                  </Link>
                );
              })}
            </motion.div>
          ) : (
            <motion.div
              key={`grid-${filter}`}
              className="work-grid"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {filtered.map((project) => {
                const meta = getProjectMeta(project.slug);
                return (
                  <Link key={project.slug} href={`/projects/${project.slug}`}>
                    <div>
                      <img src={meta.cover} alt="" />
                      <i>View</i>
                    </div>
                    <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", fontWeight: 400 }}>
                      {project.title}
                    </h2>
                    <p style={{ color: "var(--muted)", fontSize: 13 }}>
                      {meta.services}
                    </p>
                  </Link>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div
        className="work-hover-preview"
        aria-hidden
        style={{
          opacity: active === null || view !== "list" ? 0 : 1,
          left: pointer.x,
          top: pointer.y,
          pointerEvents: "none",
        }}
      >
        {projects.map((project, index) => (
          <img
            key={project.slug}
            className={active === index ? "is-visible" : ""}
            src={getProjectMeta(project.slug).cover}
            alt=""
          />
        ))}
        <span>View</span>
      </div>

      <ContactBand />
    </main>
  );
}
