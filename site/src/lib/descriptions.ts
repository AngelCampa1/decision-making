/* A description for each page, derived from the document that page renders.
 *
 * Until 2026-08-20 all 159 pages shipped the same `<meta name="description">`.
 * That string is what a search engine prints under the link, so every document
 * in this repository was advertised with one sentence about the skill -- the
 * research log, the run records and the limitations page included.
 *
 * These documents carry no frontmatter and must not gain any. `titles.ts` is
 * the statement of that design, and the reason a title is read off the first
 * heading rather than declared. The same constraint applies to a description,
 * so it is derived from the body: nothing about the source file changes, and a
 * document rewritten on github.com carries its new summary here for free.
 *
 * The standing limitation, so a green gate is not read for more than it says:
 * a derived string bypasses `decision_evals.claims`, which scans `.astro`,
 * `.ts` and `.svelte` source text and cannot see a sentence assembled at build
 * time out of markdown. `retractedPhrases()` below is the compensation and it
 * is weaker than the gate -- it matches the registered phrase and nothing else.
 */
import { retractedPhrases } from './claims.ts';

/** Google truncates around 155-160 characters. Past that is not published, it is discarded. */
export const DESCRIPTION_LIMIT = 155;

/** Shorter than this and the block is a stray line, not a summary of anything. */
const MIN_BLOCK = 25;

/** Blocks that are structure rather than prose. Tested against the block's first line. */
const STRUCTURAL = /^(#|\||>?\s*[-*+]\s|>?\s*\d+\.\s|-{3,}|\*{3,}|<|!\[|\[!\[)/;

/** Remove fenced code and HTML comments, which are not prose and often contain prose. */
function stripBlocks(text: string): string {
  return text
    .replace(/^---\n[\s\S]*?\n---\n/, '')
    .replace(/^(```|~~~)[\s\S]*?^\1[^\n]*$/gm, '')
    .replace(/<!--[\s\S]*?-->/g, '');
}

/** Markdown down to the words a reader would actually say out loud. */
function stripInline(block: string): string {
  return block
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[`*_]/g, '')
    .replace(/&[a-z]+;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Cut on a word boundary. A description that stops mid-word reads as broken markup. */
function truncate(text: string, limit: number): string {
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit - 1);
  const space = cut.lastIndexOf(' ');
  return `${(space > limit * 0.5 ? cut.slice(0, space) : cut).replace(/[,;:.\s]+$/, '')}\u2026`;
}

/**
 * The first paragraph of `body` that reads as prose, cut to `limit`.
 *
 * Falls back rather than throwing. `notebook/` and `results/` are append-only
 * evidence, so a document whose opening happens to be a table, or to quote a
 * phrase this repository has retracted, must not be able to make the site
 * unbuildable -- the only two ways out of that would be editing an append-only
 * record or deleting the guard.
 */
export function descriptionFrom(
  body: string | undefined,
  fallback: string,
  limit = DESCRIPTION_LIMIT,
): string {
  if (!body) return fallback;
  const retracted = retractedPhrases();

  for (const raw of stripBlocks(body).split(/\n\s*\n/)) {
    const block = raw.trim();
    if (!block || STRUCTURAL.test(block)) continue;

    // A blockquote's marker is structure; its content is often the best
    // sentence in the file. `docs/ACCUMULATION_VENUE.md` opens with one.
    const unquoted = block.replace(/^>\s?/gm, '').trim();
    if (!unquoted || STRUCTURAL.test(unquoted)) continue;

    const text = stripInline(unquoted);
    if (text.length < MIN_BLOCK) continue;
    if (retracted.some((phrase) => text.includes(phrase))) continue;

    return truncate(text, limit);
  }
  return truncate(fallback, limit);
}
