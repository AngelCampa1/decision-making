/**
 * Relative links that resolve twice.
 *
 * Every document this site renders is read in place from the repository, so a
 * link written for github.com has to keep working there and resolve inside the
 * site. `docs/README.md` links `../SCORECARD.md`; `docs/STATUS.md` links into
 * `../notebook/` and into published run directories under `../results/`. Those
 * two readings are not the same URL, and nothing else reconciles them.
 *
 * The rule: resolve the target against the file that wrote it -- the same base
 * `decision_evals.docs.check_path_references` uses -- and then decide. A target
 * this site renders becomes a site URL. A target it does not becomes an
 * absolute github.com blob or tree URL. A target that exists nowhere throws.
 *
 * **What this cannot catch.** It checks that a path resolves, never that the
 * sentence around it is true, and it does not validate anchors. Anchors are
 * passed through byte-for-byte because Astro slugs headings with
 * `github-slugger`, the same library GitHub uses, so the two agree by
 * construction rather than by checking. Validating them would be the "gate that
 * flags prose becomes noise" failure `docs.py` warns about in its own
 * docstring.
 */
import { existsSync, statSync, readFileSync } from 'node:fs';
import { dirname, resolve, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { visit } from 'unist-util-visit';

const REPO_ROOT = fileURLToPath(new URL('../../..', import.meta.url));
const GH = 'https://github.com/AngelCampa1/decision-making-skills';
const RAW = 'https://raw.githubusercontent.com/AngelCampa1/decision-making-skills';
const BRANCH = 'main';

/**
 * Files served at the site root. An image in `site/public/` is the one asset
 * location both readings can agree on: github.com resolves the repository path
 * and finds the committed file, and the site serves the same bytes one
 * directory shallower.
 */
const PUBLIC_DIR = 'site/public/';

/** Site base path, matching `base` in astro.config.mjs. */
const SITE_BASE = '/decision-making-skills';

/**
 * Repository directories this site renders, mapped to their route prefix.
 * A target inside one of these becomes an internal link; anything else is
 * off-site. Keep in step with `site/inputs.json` and `src/content.config.ts`.
 */
const RENDERED = [
  ['docs/', '/docs/'],
  ['notebook/', '/notebook/'],
  ['results/', '/results/'],
  ['skills/', '/skill/'],
];

/**
 * Root-level markdown rendered at its own slug. `README.md` does not take `/`:
 * the landing page lives there and is different content, so pointing a README
 * link at it would quietly send the reader somewhere else. `CLAUDE.md` shares
 * the AGENTS route because it is a byte-identical generated mirror.
 */
const ROOT_PAGES = {
  'README.md': '/readme/',
  'SCORECARD.md': '/scorecard/',
  'CONTRIBUTING.md': '/contributing/',
  'AGENTS.md': '/agents/',
  'CLAUDE.md': '/agents/',
};

/**
 * Targets that no longer resolve and are allowed not to.
 *
 * `notebook/` and `results/**` are append-only records: `docs.py` states that a
 * notebook entry naming a since-deleted file "is correct history, and a gate
 * that demanded it be edited would destroy the evidence". Without this list the
 * first commit that deletes a referenced file makes the site unbuildable, and
 * the only ways out are editing an append-only entry or switching the check
 * off. Shrink-only, like `[tool.decision-evals.unwired]`: an entry that starts
 * resolving again is itself an error.
 */
const DEAD_LINKS = new Set(
  JSON.parse(readFileSync(new URL('../../dead-links.json', import.meta.url), 'utf8')).allowed,
);

const toPosix = (p) => p.split(sep).join('/');

/** Strip the trailing `#anchor` / `?query`, which are carried through verbatim. */
function splitTarget(url) {
  const cut = url.search(/[#?]/);
  return cut < 0 ? [url, ''] : [url.slice(0, cut), url.slice(cut)];
}

function siteUrlFor(repoRel) {
  // Only markdown is rendered. `results/provenance-baseline.txt` sits inside a
  // rendered directory and is not a page, and treating it as one produced a
  // link to a directory that never existed.
  if (!repoRel.endsWith('.md')) return null;
  for (const [prefix, route] of RENDERED) {
    if (!repoRel.startsWith(prefix)) continue;
    const rest = repoRel.slice(prefix.length).replace(/\.md$/, '');
    // A directory's README is the directory's page.
    const slug = rest
      .replace(/(^|\/)README$/, '')
      .replace(/\/$/, '')
      // Must match `keepPath` in content.config.ts, or every link into docs/
      // points one case away from the page that exists.
      .toLowerCase();
    return `${SITE_BASE}${route}${slug ? `${slug}/` : ''}`;
  }
  if (repoRel in ROOT_PAGES) return `${SITE_BASE}${ROOT_PAGES[repoRel]}`;
  return null;
}

/**
 * Where an image lives once the page is served.
 *
 * Images are not links and must not be rewritten like them: a `blob` URL is an
 * HTML page, so an `<img>` pointing at one renders as a broken image rather
 * than as a picture of anything. Assets under `site/public/` are served by this
 * site; anything else has to come from raw.githubusercontent, which returns the
 * bytes.
 */
function assetUrlFor(repoRel) {
  if (repoRel.startsWith(PUBLIC_DIR)) return `${SITE_BASE}/${repoRel.slice(PUBLIC_DIR.length)}`;
  return `${RAW}/${BRANCH}/${repoRel}`;
}

export default function remarkRewriteLinks() {
  return function transformer(tree, file) {
    const src = file.path ?? file.history?.[0];
    // Never skip silently. If the content layer ever stops populating this,
    // every relative link would quietly pass through unrewritten and the site
    // would fill with 404s that still looked fine in review. Fail the build.
    if (!src) {
      throw new Error(
        'remark-rewrite-links: no source path on the vfile, so relative links ' +
          'cannot be resolved against the file that wrote them. This plugin ' +
          'must not run without one.',
      );
    }

    const fromDir = dirname(src);
    const fromRel = toPosix(relative(REPO_ROOT, src));

    /** Already-correct targets: absolute, protocol-relative, mail, bare anchor. */
    const passthrough = (url) =>
      !url || /^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith('//') || url.startsWith('#');

    /**
     * Resolve one target against the file that wrote it.
     *
     * Returns `null` only for a target this build is allowed to leave alone.
     * Anything else that does not resolve throws, because a link the reader
     * cannot follow is the same defect as a command that does not run.
     */
    function locate(url, kind) {
      const [pathPart, rest] = splitTarget(url);
      if (!pathPart) return null;

      const abs = resolve(fromDir, pathPart);
      const repoRel = toPosix(relative(REPO_ROOT, abs));

      if (repoRel.startsWith('..')) {
        throw new Error(
          `remark-rewrite-links: ${fromRel} ${kind} \`${url}\`, which resolves ` +
            'outside the repository.',
        );
      }

      if (!existsSync(abs)) {
        if (DEAD_LINKS.has(repoRel)) return null;
        throw new Error(
          `remark-rewrite-links: ${fromRel} ${kind} \`${url}\`, which does not ` +
            `exist (resolved to ${repoRel}). A link the reader cannot follow is ` +
            'the same defect as a command that does not run. If the target was ' +
            'deleted and the linking file is an append-only record, add ' +
            `"${repoRel}" to site/dead-links.json.`,
        );
      }

      return { repoRel, rest, isDir: statSync(abs).isDirectory() };
    }

    visit(tree, ['link', 'definition'], (node) => {
      if (passthrough(node.url)) return;
      const found = locate(node.url, 'links to');
      if (!found) return;
      const { repoRel, rest, isDir } = found;

      // A directory is its README, exactly as on github.com -- so the site and
      // the repository agree by construction rather than by coincidence.
      const candidates = isDir ? [`${repoRel}/README.md`, `${repoRel}/index.md`] : [repoRel];

      for (const candidate of candidates) {
        if (!existsSync(resolve(REPO_ROOT, candidate))) continue;
        const internal = siteUrlFor(candidate);
        if (internal) {
          node.url = internal + rest;
          return;
        }
      }

      node.url = `${GH}/${isDir ? 'tree' : 'blob'}/${BRANCH}/${repoRel}${rest}`;
      node.data = node.data || {};
      node.data.hProperties = { ...(node.data.hProperties || {}), rel: 'noopener' };
    });

    visit(tree, 'image', (node) => {
      if (passthrough(node.url)) return;
      const found = locate(node.url, 'shows');
      if (!found) return;
      node.url = assetUrlFor(found.repoRel) + found.rest;
    });

    // Raw HTML blocks. The README's theme-swapping lockup is a `<picture>`,
    // which is an `html` node rather than an `image` one, so it never reaches
    // the visitor above. GitHub strips `<style>` from an inline SVG, so a
    // `<picture>` of two PNGs is the only way that mark renders on both themes
    // -- which makes this the one place the site has to read attributes.
    visit(tree, 'html', (node) => {
      node.value = node.value.replace(
        /\b(src|srcset)=(["'])([^"']+)\2/g,
        (whole, attr, quote, value) => {
          // `srcset` is a comma-separated candidate list, each optionally
          // followed by a `2x` or `640w` descriptor. Rewriting the raw value
          // would send the whole list through as one filename.
          const rewritten = value
            .split(',')
            .map((candidate) => {
              const [, lead, url, tail] = /^(\s*)(\S+)(.*)$/.exec(candidate) ?? [];
              if (!url || passthrough(url) || url.startsWith('/')) return candidate;
              const found = locate(url, `sets ${attr} to`);
              if (!found) return candidate;
              return `${lead}${assetUrlFor(found.repoRel)}${found.rest}${tail}`;
            })
            .join(',');
          return `${attr}=${quote}${rewritten}${quote}`;
        },
      );
    });
  };
}
