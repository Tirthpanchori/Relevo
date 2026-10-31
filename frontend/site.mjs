export const site = {
  name: 'Relevo',
  repository: 'https://github.com/Tirthpanchori/Relevo',
  canonical: process.env.RELEVO_SITE_URL || (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}/` : 'http://localhost:4173/'),
  pages: [
    { slug: '', title: 'Relevo — Background work can recover', description: 'A durable task execution engine. Explore how jobs are claimed, retried, and recovered when workers fail.' },
    { slug: 'engine', title: 'Relevo — Engine', description: 'Follow a job through the engine and step through actual recorded failure and recovery tests.' },
    { slug: 'results', title: 'Relevo — Results', description: 'Inspect local measurements, workload comparisons, raw evidence, and the limits of the experiment.' },
    { slug: 'docs', title: 'Relevo — Docs', description: 'Run Relevo locally with Docker Compose, submit a job, and reproduce the evidence.' },
    { slug: 'about', title: 'Relevo — About', description: 'The project, the relay, and the engineering choices behind Relevo.' },
    { slug: 'privacy', title: 'Relevo — Privacy', description: 'How the static Relevo website handles browser preferences, requests, and external links.' },
  ],
};
