/**
 * Regenerates the brand assets: favicon.svg, lockup-{light,dark}.png, og.png.
 *
 * These were hand-drawn once and then sat unchanged through a redesign and a
 * procedure-count change, publishing an identity the site no longer used. So
 * they are generated, and from the same two sources the site itself reads:
 *
 *   - the segment count comes from the routing table in SKILL.md, so a seventh
 *     procedure redraws the favicon the same way it redraws the header mark;
 *   - the palette is parsed out of base.css, so there is no second copy of the
 *     colours to disagree with the first.
 *
 * Nothing here may carry a measured number. A social card is cached by every
 * crawler that has ever seen it and cannot be corrected once posted, which is
 * the same reason Base.astro keeps figures out of its og description.
 *
 *   node scripts/brand_assets.mjs
 *
 * writes favicon.svg directly and three HTML plates under site/.brand-plates/.
 * The PNGs are rasterised from those plates by a browser, because they set type
 * in Geist Mono and a standalone SVG rasteriser has no such font.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const PUBLIC = join(root, 'site', 'public');
const PLATES = join(root, 'site', '.brand-plates');

/* ------------------------------------------------------------------ sources */

/** The count, from the table an agent actually routes on -- not a directory listing. */
async function procedureCount() {
  const md = await readFile(join(root, 'skills', 'decision-making', 'SKILL.md'), 'utf8');
  const rows = md
    .split('\n')
    .filter((l) => /^\|/.test(l))
    .map((l) => l.split('|').map((c) => c.trim()));
  const header = rows.findIndex(
    (r) => r[1] === 'What is hard' && r[2] === 'Read' && r[3] === 'What it produces',
  );
  if (header === -1) throw new Error('SKILL.md: routing table not found.');
  let n = 0;
  for (const row of rows.slice(header + 2)) {
    if (!/`[a-z0-9-]+\.md`/.test(row[2] ?? '')) break;
    n += 1;
  }
  if (n === 0) throw new Error('SKILL.md: routing table has no rows.');
  return n;
}

/** The palette, from the stylesheet the site ships -- not a second copy of it. */
async function palette() {
  const css = await readFile(join(root, 'site', 'src', 'styles', 'base.css'), 'utf8');
  const block = (start) => {
    const at = css.indexOf(start);
    if (at === -1) throw new Error('base.css: `' + start + '` not found.');
    const body = css.slice(at, css.indexOf('\n}', at));
    return (name) => {
      const m = new RegExp('--' + name + ':\\s*(#[0-9a-fA-F]{3,8})').exec(body);
      if (!m) throw new Error('base.css: `--' + name + '` not found in `' + start + '`.');
      return m[1];
    };
  };
  const pick = (get) => ({
    ground: get('ground'),
    rule: get('rule'),
    ruleStrong: get('rule-strong'),
    inkStrong: get('ink-strong'),
    inkSecondary: get('ink-secondary'),
    inkMuted: get('ink-muted'),
    signal: get('signal'),
  });
  return {
    dark: pick(block(':root {')),
    light: pick(block(":root[data-theme='light']")),
  };
}

/* -------------------------------------------------------------------- shapes */

/**
 * The ring. Same geometry as Mark.astro, restated rather than imported because
 * that file is an Astro component and this is a plain script -- if the two ever
 * disagree, the header mark is the one that is right.
 *
 * The lit segment is the signal colour here, not the verdict colour. The header
 * mark reads UNTESTED and renders grey and dashed; a favicon cannot, because a
 * dashed grey arc at 16px is not visible at all. Identity in the icon, status
 * on the page.
 */
function ring({ segments, size, r, stroke, lit = 0, track, on, gap = 0.24 }) {
  const c = size / 2;
  const circumference = 2 * Math.PI * r;
  const arc = circumference / segments;
  const drawn = arc * (1 - gap);
  const seg = (i) =>
    '<circle cx="' + c + '" cy="' + c + '" r="' + r + '" fill="none" stroke="' +
    (i === lit ? on : track) + '" stroke-width="' + stroke +
    '" stroke-dasharray="' + drawn.toFixed(3) + ' ' + (circumference - drawn).toFixed(3) +
    '" stroke-dashoffset="' + (-i * arc).toFixed(3) + '"/>';
  return (
    '<g transform="rotate(-90 ' + c + ' ' + c + ')">' +
    Array.from({ length: segments }, (_, i) => seg(i)).join('') +
    '</g>'
  );
}

/** Browsers render this at device resolution, so it is drawn once and scales. */
function favicon(segments) {
  const geometry = ring({
    segments,
    size: 32,
    r: 12,
    stroke: 5,
    track: 'var(--track)',
    on: 'var(--on)',
    gap: 0.26,
  });
  return [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">',
    '  <style>',
    '    :root { --track: #bdbdb6; --on: #4a5f10; }',
    '    @media (prefers-color-scheme: dark) {',
    '      :root { --track: #333941; --on: #c6f24e; }',
    '    }',
    '  </style>',
    '  <!-- ' + segments + ' segments, one lit: the skill\'s claim drawn rather than',
    '       described. The band is deliberately fat (r=12, stroke=5) so the ring',
    '       survives being drawn into a 16px tab strip. Generated by',
    '       scripts/brand_assets.mjs; edit that, not this. -->',
    '  ' + geometry,
    '</svg>',
    '',
  ].join('\n');
}

/* -------------------------------------------------------------------- plates */

// Relative, and served over HTTP rather than opened from disk: a headless
// browser refuses `file:` URLs, so the plates are rasterised through a local
// static server rooted at the repository. Both paths below resolve from
// site/.brand-plates/.
const FONTS = '../node_modules/@fontsource-variable';

const face = [
  '@font-face {',
  "  font-family: 'Geist Mono Variable';",
  "  src: url('" + FONTS + "/geist-mono/files/geist-mono-latin-wght-normal.woff2') format('woff2-variations');",
  '  font-weight: 100 900;',
  '}',
  '@font-face {',
  "  font-family: 'Geist Variable';",
  "  src: url('" + FONTS + "/geist/files/geist-latin-wght-normal.woff2') format('woff2-variations');",
  '  font-weight: 100 900;',
  '}',
].join('\n');

function plate({ w, h, css, body }) {
  return [
    '<!doctype html><html><head><meta charset="utf-8"><style>',
    face,
    '* { margin: 0; padding: 0; box-sizing: border-box; }',
    'html, body { width: ' + w + 'px; height: ' + h + 'px; overflow: hidden; }',
    'body { display: flex; }',
    css,
    '</style></head><body>' + body + '</body></html>',
  ].join('\n');
}

function lockup(p, segments) {
  const mark = ring({
    segments,
    size: 96,
    r: 39,
    stroke: 7.5,
    track: p.ruleStrong,
    on: p.signal,
  });
  return plate({
    w: 1200,
    h: 300,
    css: [
      'body { background: ' + p.ground + '; align-items: center; justify-content: center; gap: 34px; }',
      ".word { font: 560 62px/1 'Geist Mono Variable', monospace; letter-spacing: -0.02em; color: " +
        p.inkStrong + '; }',
    ].join('\n'),
    body:
      '<svg width="96" height="96" viewBox="0 0 96 96" fill="none">' + mark + '</svg>' +
      '<span class="word">decision-making-skills</span>',
  });
}

/**
 * The social card. No measured numbers, on purpose -- see the header. The one
 * count on it is the ring, which is structural and regenerates with the table.
 */
function og(p, segments) {
  const mark = ring({
    segments,
    size: 132,
    r: 54,
    stroke: 11,
    track: p.ruleStrong,
    on: p.signal,
    // Drawn at 132 and placed at 54, so the gaps have to be wider than the
    // header mark's or the ring reads as a ragged dotted circle once scaled.
    gap: 0.2,
  });
  return plate({
    w: 1200,
    h: 630,
    css: [
      'body { background: ' + p.ground + '; flex-direction: column; justify-content: space-between; padding: 76px 84px; }',
      '.top { display: flex; align-items: center; gap: 20px; }',
      ".word { font: 560 27px/1 'Geist Mono Variable', monospace; letter-spacing: -0.01em; color: " + p.inkSecondary + '; }',
      "h1 { font: 620 76px/1.06 'Geist Variable', sans-serif; letter-spacing: -0.035em; color: " + p.inkStrong + '; max-width: 15ch; }',
      'h1 em { font-style: normal; color: ' + p.signal + '; }',
      '.foot { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid ' + p.rule + '; padding-top: 26px; }',
      ".foot p { font: 400 26px/1.35 'Geist Variable', sans-serif; color: " + p.inkMuted + '; }',
      ".chip { font: 560 20px/1 'Geist Mono Variable', monospace; letter-spacing: 0.08em; text-transform: uppercase; color: " +
        p.inkMuted + '; border: 1px solid ' + p.ruleStrong + '; border-radius: 3px; padding: 10px 14px; white-space: nowrap; }',
    ].join('\n'),
    body:
      '<div class="top"><svg width="54" height="54" viewBox="0 0 132 132" fill="none">' + mark + '</svg>' +
      '<span class="word">decision-making-skills</span></div>' +
      '<h1>An agent skill for <em>hard choices</em>.</h1>' +
      '<div class="foot"><p>Nothing proven yet. Every result is public.</p>' +
      '<span class="chip">untested</span></div>',
  });
}

/* ---------------------------------------------------------------------- main */

const segments = await procedureCount();
const p = await palette();

await mkdir(PLATES, { recursive: true });
await writeFile(join(PUBLIC, 'favicon.svg'), favicon(segments));
await writeFile(join(PLATES, 'lockup-light.html'), lockup(p.light, segments));
await writeFile(join(PLATES, 'lockup-dark.html'), lockup(p.dark, segments));
await writeFile(join(PLATES, 'og.html'), og(p.dark, segments));

console.log('favicon.svg written (' + segments + ' segments)');
console.log('plates written to site/.brand-plates/ -- rasterise to site/public/');
