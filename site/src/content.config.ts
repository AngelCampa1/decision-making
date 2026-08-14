import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Every collection reads the markdown **in place** from the repository. There
 * is no second copy of any document: `docs/STATUS.md` is the file GitHub serves
 * and the file this site renders, and the only way to change what the site says
 * is to change the document.
 *
 * `base` uses the relative-string form throughout. That resolves against the
 * Astro project root (the directory holding astro.config.mjs). The `URL` form
 * would resolve against *this* file instead, which is two levels further down,
 * so mixing the two is a silent off-by-one. One form, everywhere.
 *
 * Keep the globs in step with `site/inputs.json`, which is what the staleness
 * gate hashes, and with `RENDERED` in `src/lib/remark-rewrite-links.mjs`, which
 * is what decides whether a link stays on the site or leaves for github.com.
 */

/**
 * Path relative to the collection base, minus the extension, lowercased.
 *
 * Not Astro's default slugifier, which would mangle a run id like
 * `2026-08-13-abb6862-l7-stakes`. Lowercased because GitHub Pages is
 * case-sensitive and `STATUS.md` published at `/docs/STATUS/` is a URL nobody
 * types correctly twice. `remark-rewrite-links.mjs` lowercases to match.
 */
const keepPath = ({ entry }: { entry: string }) => entry.replace(/\.md$/, '').toLowerCase();

const docs = defineCollection({
  loader: glob({ pattern: '**/*.md', base: '../docs', generateId: keepPath }),
});

const notebook = defineCollection({
  loader: glob({ pattern: '*.md', base: '../notebook', generateId: keepPath }),
});

const results = defineCollection({
  loader: glob({ pattern: '*/*/README.md', base: '../results', generateId: keepPath }),
});

const skills = defineCollection({
  loader: glob({ pattern: '**/*.md', base: '../skills', generateId: keepPath }),
});

/**
 * Root-level documents. `CLAUDE.md` is deliberately absent: it is a
 * byte-identical generated mirror of `AGENTS.md` (`de mirror`), and rendering
 * both would publish the same document at two URLs.
 */
const root = defineCollection({
  loader: glob({
    pattern: '{README,SCORECARD,CONTRIBUTING,AGENTS}.md',
    base: '..',
    generateId: keepPath,
  }),
});

export const collections = { docs, notebook, results, skills, root };
