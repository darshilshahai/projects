export type ArchitectureNode = {
  label: string;
  detail?: string;
};

export type CodeSnippet = {
  title: string;
  language: string;
  code: string;
};

export type Project = {
  slug: string;
  title: string;
  tagline: string;
  summary: string;
  terminal: string;
  problemShort: string;
  problem: string;
  solutionShort: string;
  solution: string;
  coreCapabilities: string[];
  decisions: string[];
  challenges: string[];
  results: string[];
  futureWork: string[];
  stack: string[];
  architecture: ArchitectureNode[];
  snippet?: CodeSnippet;
  githubUrl?: string;
  liveUrl?: string;
  featured: boolean;
};

export type Experience = {
  role: string;
  company: string;
  period: string;
  location?: string;
  summary: string;
  bullets: string[];
  stack: string[];
};

export type FocusArea = {
  title: string;
  description: string;
};

export type Article = {
  title: string;
  summary: string;
  category: string;
  status: string;
  year: string;
  readingTime: string;
  href?: string;
};
