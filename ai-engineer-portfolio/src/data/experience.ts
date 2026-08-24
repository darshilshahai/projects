import type { Experience } from "@/types";

// Periods are editable placeholders — confirm exact dates before publishing.
export const experiences: Experience[] = [
  {
    role: "Full-Stack Developer",
    company: "TrueCover",
    period: "2023 — Present",
    location: "India",
    summary:
      "Building backend services and internal AI systems for enterprise insurance workflows.",
    bullets: [
      "Build Node.js and FastAPI services for enterprise reporting and operational workflows.",
      "Strengthen APIs with validation, logging, error handling, and maintainable service boundaries.",
      "Work across MongoDB, PostgreSQL, Redis, RabbitMQ, and modern frontend applications.",
      "Review code, mentor junior developers, and build internal AI-assisted tools.",
    ],
    stack: ["FastAPI", "Node.js", "MongoDB", "Redis"],
  },
  {
    role: "Software Developer",
    company: "Triveni GlobalSoft",
    period: "2020 — 2023",
    location: "India",
    summary:
      "Full-stack delivery with a backend focus: APIs, data modelling, and async workflows.",
    bullets: [
      "Delivered backend APIs and full-stack product features.",
      "Designed database access patterns and optimised expensive queries.",
      "Used Redis caching and RabbitMQ for asynchronous workflows.",
    ],
    stack: ["Node.js", "Redis", "RabbitMQ", "SQL"],
  },
];
