"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useState } from "react";
import type { Project } from "@/types";
import { LaunchLoader } from "@/components/layout/launch-loader";
import { Navbar } from "@/components/layout/navbar";
import { SiteFooter } from "@/components/layout/site-footer";
import { getProjectMeta } from "@/data/project-meta";
import { projects } from "@/data/projects";

export function ProjectCaseView({
  project,
  projectIndex,
  nextProject,
}: {
  project: Project;
  projectIndex: number;
  nextProject: Project;
}) {
  const meta = getProjectMeta(project.slug);
  const nextMeta = getProjectMeta(nextProject.slug);
  const images = meta.gallery;
  const actionHref = project.liveUrl || project.githubUrl;
  const reduceMotion = useReducedMotion();
  const [nextHovered, setNextHovered] = useState(false);
  const [nextPointer, setNextPointer] = useState({ x: 0, y: 0 });

  return (
    <main className="project-case-page" id="main">
      <LaunchLoader words={[project.title.split(" ")[0] ?? "Case"]} hold={800} />
      <Navbar />

      <header className="project-case-hero">
        <motion.h1
          initial={{ opacity: 0, y: 48 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          {project.title}
        </motion.h1>
        <div className="project-case-meta">
          <div>
            <span>Services</span>
            <p>{meta.services}</p>
          </div>
          <div>
            <span>Credits</span>
            <p>Design &amp; development — Darshil Shah</p>
          </div>
          <div>
            <span>Location · Year</span>
            <p>
              {meta.location} · {meta.year}
            </p>
          </div>
        </div>
        {actionHref ? (
          <a className="project-case-live" href={actionHref} target="_blank" rel="noopener noreferrer">
            {project.liveUrl ? "Live site →" : "Repository →"}
          </a>
        ) : null}
        <motion.div
          className="project-case-cover"
          initial={reduceMotion ? {} : { clipPath: "inset(100% 0 0 0)" }}
          animate={{ clipPath: "inset(0% 0 0 0)" }}
          transition={{ duration: 1, delay: 0.9, ease: [0.76, 0, 0.24, 1] }}
        >
          <img src={images[0]} alt={`${project.title} preview`} />
        </motion.div>
      </header>

      <section className="project-case-copy">
        <p className="section-tag">
          <em>—</em> Overview
        </p>
        <div className="project-story-grid">
          <h2>{project.tagline}</h2>
          <div>
            <p>
              <strong>Problem. </strong>
              {project.problem}
            </p>
            <p>
              <strong>Approach. </strong>
              {project.solution}
            </p>
          </div>
        </div>
        <ul className="project-capability-pills">
          {project.coreCapabilities.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </section>

      <section className="project-case-gallery" aria-label={`${project.title} gallery`}>
        <figure>
          <img src={images[1]} alt={`${project.title} at scale`} />
        </figure>
        <div className="project-browser-frame">
          <div>
            <i /><i /><i />
            <span style={{ marginLeft: 12 }}>{project.slug}.app</span>
          </div>
          <img src={images[2]} alt="Desktop interface" />
        </div>
        <div className="project-mobile-showcase">
          {[images[0], images[2], images[3]].map((src, i) => (
            <figure key={`${src}-${i}`}>
              <img src={src} alt="" />
            </figure>
          ))}
        </div>
      </section>

      <footer className="project-next-case">
        <span style={{ font: "11px var(--font-mono)", letterSpacing: "0.12em", textTransform: "uppercase" }}>
          Next project
        </span>
        <Link
          className={nextHovered ? "is-active" : ""}
          href={`/projects/${nextProject.slug}`}
          onPointerEnter={(e) => {
            setNextHovered(true);
            const b = e.currentTarget.getBoundingClientRect();
            setNextPointer({ x: e.clientX - b.left - 50, y: e.clientY - b.top - 50 });
          }}
          onPointerMove={(e) => {
            if (e.pointerType === "touch") return;
            const b = e.currentTarget.getBoundingClientRect();
            setNextPointer({ x: e.clientX - b.left - 50, y: e.clientY - b.top - 50 });
          }}
          onPointerLeave={() => setNextHovered(false)}
        >
          <h2>{nextProject.title}</h2>
          <img src={nextMeta.cover} alt="" />
          <motion.i
            animate={{
              opacity: nextHovered ? 1 : 0,
              scale: nextHovered ? 1 : 0.4,
              x: nextPointer.x,
              y: nextPointer.y,
            }}
            transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 260, damping: 22 }}
          >
            Next
          </motion.i>
        </Link>
        <Link className="all-work-link" href="/work">
          All work · {String(projectIndex + 1).padStart(2, "0")}/{String(projects.length).padStart(2, "0")}
        </Link>
        <SiteFooter compact />
      </footer>
    </main>
  );
}
