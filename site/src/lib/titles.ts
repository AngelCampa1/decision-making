/**
 * These documents carry no frontmatter -- they are read on github.com as much
 * as here, and a title block added for the site would be a change to the
 * document made for the renderer's convenience. So the title is taken from the
 * first heading the markdown already has, and the id is the fallback.
 */
export function titleFrom(headings: { depth: number; text: string }[], id: string): string {
  const first = headings.find((h) => h.depth === 1) ?? headings[0];
  if (first) return first.text;
  return id.split('/').pop() ?? id;
}

/**
 * `decision-making/2026-08-13-abb6862-l7-stakes/readme` -> the run directory.
 * Ids arrive lowercased from `keepPath`, so this matches lowercase.
 */
export function stripReadme(id: string): string {
  return id.replace(/(^|\/)readme$/, '');
}

/**
 * The repository-relative path of the file behind an entry, for the provenance
 * link on every rendered document.
 *
 * Taken from `filePath` rather than rebuilt from the id, because ids are
 * lowercased for the URL and the files are not: deriving it sent every doc's
 * "view source" link to `docs/protocol.md`, which does not exist.
 */
export function sourcePath(filePath: string | undefined, fallback: string): string {
  if (!filePath) return fallback;
  return filePath.replace(/\\/g, '/').replace(/^(\.\.\/)+/, '');
}
