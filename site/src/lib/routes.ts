/**
 * Root-level documents published on the site, keyed by collection id.
 *
 * Ids arrive lowercased from `keepPath` in content.config.ts, so the slug and
 * the id are the same string -- but the set is written out rather than derived,
 * because it is also the answer to "which root documents does the site
 * publish?", and that is a decision rather than a consequence.
 *
 * `README` does not take `/`: the landing page lives there and is different
 * content. `CLAUDE.md` is absent because it is a byte-identical generated
 * mirror of `AGENTS.md`, and publishing both would put one document at two
 * URLs.
 *
 * Keep in step with `ROOT_PAGES` in `remark-rewrite-links.mjs`.
 */
export const ROOT_ROUTES = new Set(['readme', 'scorecard', 'contributing', 'agents']);
