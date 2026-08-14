/**
 * Two things markdown cannot say about a table, applied at render time.
 *
 * Neither touches the source. `notebook/` and `results/` are append-only dated
 * records and `docs/` is read on github.com as much as here, so a presentation
 * problem is fixed in the renderer or not at all.
 *
 * 1. **Numeric columns are right-aligned, mono and tabular.** `0.9529` has to
 *    sit digit over digit above `0.9118` or the reader parses each figure
 *    instead of scanning the column. Markdown has an alignment syntax and none
 *    of these documents use it, because it is invisible in the source.
 *
 * 2. **Emoji ticks become text glyphs.** GitHub renders `✅`/`❌` in the OS
 *    emoji font, which ignores every colour token, breaks the mono grid, and
 *    carries pass/fail on colour alone (WCAG 1.4.1). They become `✓`/`✕` in the
 *    status inks with a visually-hidden word.
 */
import { visit } from 'unist-util-visit';

/** A cell that is a measurement: 0.9529, 2,555, ~4,240, 89%, +2.9pp, -0.03, n/a dash. */
const NUMERIC = /^[~+-]?[\d,]+(\.\d+)?\s*(%|pp|x|ms|s)?$/i;
const NIL = /^(—|--|n\/a|-)$/i;

const TICKS = {
  '✅': ['✓', 'passed', 'mark-pass'],
  '❌': ['✕', 'failed', 'mark-fail'],
  '✔️': ['✓', 'passed', 'mark-pass'],
  '✖️': ['✕', 'failed', 'mark-fail'],
};

const textOf = (node) => {
  let out = '';
  visit(node, 'text', (t) => {
    out += t.value;
  });
  return out.trim();
};

const isRow = (n) => n.type === 'element' && n.tagName === 'tr';
const cellsOf = (row) =>
  row.children.filter((c) => c.type === 'element' && (c.tagName === 'td' || c.tagName === 'th'));

/** Idempotent: Astro renders an entry more than once per build, so a plain
 *  push produces `class="num num"`. */
function addClass(node, cls) {
  node.properties = node.properties || {};
  const existing = node.properties.className;
  const list = Array.isArray(existing) ? existing : existing ? [existing] : [];
  if (!list.includes(cls)) list.push(cls);
  node.properties.className = list;
}

export default function rehypeTables() {
  return function transformer(tree) {
    // --- emoji ticks, anywhere in the document ------------------------------
    visit(tree, 'element', (node) => {
      if (!node.children) return;
      const next = [];
      let changed = false;
      for (const child of node.children) {
        if (child.type !== 'text') {
          next.push(child);
          continue;
        }
        const parts = child.value.split(/(✅|❌|✔️|✖️)/);
        if (parts.length === 1) {
          next.push(child);
          continue;
        }
        changed = true;
        for (const part of parts) {
          if (part in TICKS) {
            const [glyph, word, cls] = TICKS[part];
            next.push({
              type: 'element',
              tagName: 'span',
              properties: { className: [cls], 'aria-hidden': 'true' },
              children: [{ type: 'text', value: glyph }],
            });
            next.push({
              type: 'element',
              tagName: 'span',
              properties: { className: ['sr-only'] },
              children: [{ type: 'text', value: word }],
            });
          } else if (part) {
            next.push({ type: 'text', value: part });
          }
        }
      }
      if (changed) node.children = next;
    });

    // --- numeric column detection ------------------------------------------
    visit(tree, 'element', (node) => {
      if (node.tagName !== 'table') return;

      const rows = [];
      visit(node, isRow, (row) => rows.push(row));

      // A row with no cells is neither a header nor a body row. Classifying by
      // `every(th)` puts it in the header, because [].every() is true -- which
      // silently shifted the column index and left most of a numeric column
      // unmarked.
      const populated = rows.filter((r) => cellsOf(r).length > 0);
      if (populated.length < 2) return;

      const head = populated.filter((r) => cellsOf(r).every((c) => c.tagName === 'th'));
      const body = populated.filter((r) => cellsOf(r).some((c) => c.tagName === 'td'));
      if (body.length === 0) return;

      const width = Math.max(...body.map((r) => cellsOf(r).length));

      for (let col = 0; col < width; col++) {
        const values = body
          .map((r) => cellsOf(r)[col])
          .filter(Boolean)
          .map((c) => textOf(c));
        if (values.length === 0) continue;

        const meaningful = values.filter((v) => v !== '' && !NIL.test(v));
        if (meaningful.length === 0) continue;
        // A column is numeric only if every value that says anything is a
        // number. One prose cell and it is a prose column.
        if (!meaningful.every((v) => NUMERIC.test(v))) continue;

        for (const row of body) {
          const cell = cellsOf(row)[col];
          if (!cell) continue;
          addClass(cell, 'num');
          if (NIL.test(textOf(cell))) addClass(cell, 'nil');
        }
        for (const row of head) {
          const cell = cellsOf(row)[col];
          if (cell) addClass(cell, 'num');
        }
      }
    });
  };
}
