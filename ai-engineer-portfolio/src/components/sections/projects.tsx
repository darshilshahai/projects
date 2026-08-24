"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { projects } from "@/data/projects";
import { getProjectMeta } from "@/data/project-meta";

export function ProjectsSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();
  const [active, setActive] = useState<number | null>(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const featured = projects.slice(0, 4);

  const onMove = (e: React.PointerEvent, index: number) => {
    setActive(index);
    if (e.pointerType === "touch") return;
    setPointer({ x: e.clientX, y: e.clientY });
  };

  return (
    <section className="projects-section" id="projects" ref={sectionRef}>
      <div className="shell">
        <div className="project-index">
          {featured.map((project, index) => {
            const meta = getProjectMeta(project.slug);
            return (
              <Link
                key={project.slug}
                href={`/projects/${project.slug}`}
                className={`project-row${active === index ? " is-active" : ""}`}
                onPointerEnter={(e) => onMove(e, index)}
                onPointerMove={(e) => onMove(e, index)}
                onPointerLeave={() => setActive(null)}
                onFocus={() => setActive(index)}
                onBlur={() => setActive(null)}
              >
                <span className="project-row-num">{String(index + 1).padStart(2, "0")}</span>
                <h3>{project.title}</h3>
                <span className="project-row-meta">{meta.services}</span>
              </Link>
            );
          })}
        </div>

        <div className="project-gallery">
          {projects.slice(0, 4).map((project) => (
            <Link key={project.slug} href={`/projects/${project.slug}`} aria-label={project.title}>
              <img src={getProjectMeta(project.slug).cover} alt="" />
            </Link>
          ))}
        </div>

        <div className="more-work-wrap">
          <Link className="btn-signal" href="/work">
            All projects — {String(projects.length).padStart(2, "0")}
          </Link>
        </div>
      </div>

      <div
        className={`project-preview${active !== null ? " is-visible" : ""}`}
        aria-hidden
        style={{
          left: pointer.x,
          top: pointer.y,
          transition: reduceMotion ? undefined : "opacity 0.2s",
        }}
      >
        {featured.map((project, index) => (
          <img
            key={project.slug}
            src={getProjectMeta(project.slug).cover}
            alt=""
            style={{
              display: active === index ? "block" : "none",
              width: "100%",
              height: "100%",
              objectFit: "cover",
              position: "absolute",
              inset: 0,
            }}
          />
        ))}
        <span className="project-preview-label">View</span>
      </div>
    </section>
  );
}
