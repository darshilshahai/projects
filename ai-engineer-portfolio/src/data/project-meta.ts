export type ProjectFilter = "AI" | "Development";

export type ProjectMeta = {
  services: string;
  year: string;
  location: string;
  filters: ProjectFilter[];
  cover: string;
  gallery: string[];
};

export const projectMeta: Record<string, ProjectMeta> = {
  "fraud-detection-rag": {
    services: "RAG Design & Development",
    year: "2026",
    location: "India",
    filters: ["AI"],
    cover:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1800&q=88",
    gallery: [
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1800&q=88",
      "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1600&q=88",
      "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1400&q=88",
      "https://images.unsplash.com/photo-1449157291145-7efd050a4d8e?auto=format&fit=crop&w=1400&q=88",
    ],
  },
  "northwind-rag-assistant": {
    services: "AI Interaction & Development",
    year: "2025",
    location: "Remote",
    filters: ["AI"],
    cover:
      "https://images.unsplash.com/photo-1497604401993-f2e922e5cb0a?auto=format&fit=crop&w=1800&q=88",
    gallery: [
      "https://images.unsplash.com/photo-1497604401993-f2e922e5cb0a?auto=format&fit=crop&w=1800&q=88",
      "https://images.unsplash.com/photo-1487958449943-2429e8be8625?auto=format&fit=crop&w=1600&q=88",
      "https://images.unsplash.com/photo-1511818966892-d7d671e672a0?auto=format&fit=crop&w=1400&q=88",
      "https://images.unsplash.com/photo-1503387531678-3c0cfa1bf409?auto=format&fit=crop&w=1400&q=88",
    ],
  },
  promptforge: {
    services: "AI Product Development",
    year: "2025",
    location: "India",
    filters: ["AI", "Development"],
    cover:
      "https://images.unsplash.com/photo-1448630360428-65456885c650?auto=format&fit=crop&w=1800&q=88",
    gallery: [
      "https://images.unsplash.com/photo-1448630360428-65456885c650?auto=format&fit=crop&w=1800&q=88",
      "https://images.unsplash.com/photo-1511818966892-d7d671e672a0?auto=format&fit=crop&w=1600&q=88",
      "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1400&q=88",
      "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1400&q=88",
    ],
  },
  "ai-email-scheduler": {
    services: "AI Product Development",
    year: "2025",
    location: "Remote",
    filters: ["AI", "Development"],
    cover:
      "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1800&q=88",
    gallery: [
      "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1800&q=88",
      "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1600&q=88",
      "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=88",
      "https://images.unsplash.com/photo-1497366412874-3415097a27e7?auto=format&fit=crop&w=1400&q=88",
    ],
  },
  "url-shortener": {
    services: "Backend Design & Development",
    year: "2024",
    location: "India",
    filters: ["Development"],
    cover:
      "https://images.unsplash.com/photo-1486325212027-8081e485255e?auto=format&fit=crop&w=1800&q=88",
    gallery: [
      "https://images.unsplash.com/photo-1486325212027-8081e485255e?auto=format&fit=crop&w=1800&q=88",
      "https://images.unsplash.com/photo-1479839672679-a46483c0e7c8?auto=format&fit=crop&w=1600&q=88",
      "https://images.unsplash.com/photo-1481026469463-66327c86e544?auto=format&fit=crop&w=1400&q=88",
      "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1400&q=88",
    ],
  },
  "brandvoice-agent": {
    services: "Agentic Workflow Design",
    year: "2026",
    location: "Remote",
    filters: ["AI"],
    cover:
      "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1800&q=88",
    gallery: [
      "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1800&q=88",
      "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=88",
      "https://images.unsplash.com/photo-1497604401993-f2e922e5cb0a?auto=format&fit=crop&w=1400&q=88",
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1400&q=88",
    ],
  },
};

export const fallbackMeta: ProjectMeta = {
  services: "Design & Development",
  year: "2026",
  location: "India",
  filters: ["Development"],
  cover:
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1800&q=88",
  gallery: [
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1800&q=88",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1600&q=88",
    "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1400&q=88",
    "https://images.unsplash.com/photo-1449157291145-7efd050a4d8e?auto=format&fit=crop&w=1400&q=88",
  ],
};

export function getProjectMeta(slug: string): ProjectMeta {
  return projectMeta[slug] ?? fallbackMeta;
}

export function countProjectsByFilter(
  filter: "All" | ProjectFilter,
  slugs: string[],
) {
  if (filter === "All") return slugs.length;
  return slugs.filter((slug) => getProjectMeta(slug).filters.includes(filter)).length;
}
