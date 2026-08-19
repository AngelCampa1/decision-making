/* What this site says about the skill, read from the skill.
 *
 * Every fact here used to be typed twice: once in `skills/decision-making/`
 * and once in a page. On 2026-08-19 `council.md` and `hinge.md` shipped and
 * two pages went on saying "four procedures" -- one of them the social card
 * every link preview uses. Nothing noticed, because nothing could: `docs.py`
 * scans `*.md` and `docs/*.md` and never opens a `.astro` file, and `site.py`
 * hashes the page for staleness without reading a word of it.
 *
 * So the page no longer holds the list. It asks for it, and the build stops if
 * the answer disagrees with the skill.
 *
 * The list comes from SKILL.md's routing table rather than from a directory
 * listing, and that is the load-bearing choice. The table is what an agent
 * actually routes from, so `placebo.md` -- the length-matched control arm,
 * which is not a procedure and must never be advertised as one -- is excluded
 * because it is not in the table, not because its name sits in an exclusion
 * list somebody has to maintain.
 */
import { getCollection, type CollectionEntry } from 'astro:content';

/** The one skill this site is about. Collection ids are lowercased by `keepPath`. */
export const SKILL_ENTRY = 'decision-making/skill';

/** The router itself. In the collection, not in its own table. */
const ROUTER = 'skill';

/** The control arm: same length and shape, no procedure in it. Never a procedure. */
const CONTROL = 'placebo';

/** The table SKILL.md routes from. Matched on the header, so a second table cannot be mistaken for it. */
const TABLE_HEADER = ['What is hard', 'Read', 'What it produces'];

export interface Procedure {
  /** Collection id stem, lowercased: `ledger`. */
  file: string;
  /** What the routing table names: `ledger.md`. */
  md: string;
  /** Position in the routing table, 1-based and zero-padded: `01`. */
  ord: string;
  /** The "What is hard" cell, verbatim. */
  hard: string;
  /** The "What it produces" cell, verbatim. */
  produces: string;
  /** Link to the file on GitHub. */
  path: string;
}

export interface SkillFacts {
  version: string;
  status: string;
  verdict: string;
  procedures: Procedure[];
  count: number;
  /** `Six`, for prose. Capitalised; lowercase it at the call site if needed. */
  countWord: string;
}

const WORDS = ['zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'];

function fail(message: string): never {
  throw new Error(
    `skills/decision-making/SKILL.md: ${message}\n` +
      'The site derives its procedure list from that file. Fix the file or the ' +
      'reader in site/src/lib/facts.ts -- do not hardcode the list back into a page.',
  );
}

/** Split one markdown table row into trimmed cells, dropping the empty ends. */
function cells(row: string): string[] {
  return row
    .split('|')
    .slice(1, -1)
    .map((cell) => cell.trim());
}

/** The single code span in a cell: `` `ledger.md` `` -> `ledger.md`. */
function code(cell: string): string | null {
  const match = cell.match(/^`([^`]+)`$/);
  return match ? match[1] : null;
}

/** A markdown table row, as the source line sits: leading whitespace, then `|`. */
function isRow(line: string): boolean {
  return line.trimStart().startsWith('|');
}

function routingTable(body: string): string[][] {
  const lines = body.split('\n');
  const header = lines.findIndex((line) => {
    if (!isRow(line)) return false;
    const parsed = cells(line);
    return (
      parsed.length === TABLE_HEADER.length && parsed.every((cell, i) => cell === TABLE_HEADER[i])
    );
  });
  if (header === -1) fail(`no table with the header ${TABLE_HEADER.join(' | ')}`);

  // Header, then the `|---|---|---|` separator, then the rows.
  //
  // Adjacency is read off the source lines, not off a filtered list of every
  // pipe line in the body. Filtering first deletes the blank line between two
  // tables, which makes a later table contiguous with this one: an adversarial
  // review on 2026-08-19 appended a single pipe row inside a fenced example and
  // the page published "Seven methods." with `ledger.md` listed twice. Nothing
  // threw, because the loop's `break` was testing cell count on a list that had
  // already lost the only evidence the table had ended -- and the comment that
  // used to sit here asserted the opposite of what the code did.
  const body_rows: string[][] = [];
  for (let i = header + 2; i < lines.length; i += 1) {
    if (!isRow(lines[i])) break;
    const parsed = cells(lines[i]);
    if (parsed.length !== TABLE_HEADER.length) {
      // Not `break`. A wrong cell count inside the table is a mistyped pipe,
      // and skipping it silently dropped that row and every row after it --
      // surfacing, when it surfaced at all, as the backwards check below
      // complaining about a file that was in the table all along.
      fail(
        `routing table row ${i - header - 1} has ${parsed.length} cells, not ` +
          `${TABLE_HEADER.length}: ${lines[i].trim()}`
      );
    }
    body_rows.push(parsed);
  }
  if (body_rows.length < 2) fail('the routing table has fewer than two rows');
  return body_rows;
}

/**
 * The skill's own account of itself: version, verdict, and the procedures it routes to.
 *
 * Throws rather than returning a partial answer. A build that cannot read the
 * skill must not publish a page that describes it -- and `de site` refuses to
 * write a manifest over a failed build, so the throw is what keeps a stale
 * page from being republished as green.
 */
export async function skillFacts(): Promise<SkillFacts> {
  const all = await getCollection('skills');
  const router = all.find((entry) => entry.id === SKILL_ENTRY);
  if (!router) fail(`no entry \`${SKILL_ENTRY}\` in the skills collection`);

  const body = (router as CollectionEntry<'skills'> & { body?: string }).body;
  if (!body) fail('the entry has no body to read the routing table from');

  const metadata = (router.data as { metadata?: Record<string, unknown> }).metadata;
  if (!metadata) fail('frontmatter has no `metadata` block');
  for (const field of ['version', 'status', 'verdict'] as const) {
    if (!metadata[field]) fail(`frontmatter has no \`metadata.${field}\``);
  }

  const rows = routingTable(body);
  const procedures: Procedure[] = rows.map((row, i) => {
    const md = code(row[1]);
    if (!md) fail(`routing table row ${i + 1} has no file in its "Read" column`);
    return {
      file: md.replace(/\.md$/, ''),
      md,
      ord: String(i + 1).padStart(2, '0'),
      hard: row[0],
      produces: row[2],
      path: `skills/decision-making/${md}`,
    };
  });

  // Both directions, or this is a convenience and not a guard.
  //
  // Forwards: a file the table routes to must exist, or the page links to
  // nothing. Backwards: a file that exists must be in the table, or we are
  // back at council.md and hinge.md shipping unmentioned -- which is the
  // failure that produced this module and the only one a page cannot notice
  // by looking at itself.
  const named = new Set(procedures.map((p) => p.file));
  const present = new Set(
    all
      .map((entry) => entry.id)
      .filter((id) => id.startsWith('decision-making/'))
      .map((id) => id.slice('decision-making/'.length)),
  );
  for (const procedure of procedures) {
    if (!present.has(procedure.file)) {
      fail(`the routing table names \`${procedure.md}\`, which is not in the skills collection`);
    }
  }
  for (const file of present) {
    if (file === ROUTER || file === CONTROL || named.has(file)) continue;
    fail(
      `\`${file}.md\` is in skills/decision-making/ and not in the routing table. ` +
        'Add it to the table (and it becomes a procedure the site publishes), or ' +
        `name it as a control the way \`${CONTROL}.md\` is.`,
    );
  }

  const count = procedures.length;
  return {
    version: String(metadata.version),
    status: String(metadata.status),
    verdict: String(metadata.verdict),
    procedures,
    count,
    countWord: WORDS[count] ?? String(count),
  };
}

/**
 * Runs written up on this site.
 *
 * Not the same number as `docs/RUN_INDEX.md`, which lists thirteen: the
 * baselined `results/evidence-ledger/2026-08-10-baseline-corpus/` has no
 * README.md, so the collection glob `*​/*​/README.md` cannot see it. Both counts
 * are honest about different sets. If that run should be published, write its
 * README -- this number will move on its own. Do not widen the glob.
 */
export async function publishedRunCount(): Promise<number> {
  return (await getCollection('results')).length;
}

/** Dated notebook entries, excluding the index that introduces them. */
export async function notebookEntryCount(): Promise<number> {
  return (await getCollection('notebook')).filter((entry) => entry.id !== 'readme').length;
}

/** One row of a published arm table. */
export interface Arm {
  arm: string;
  accuracy: number;
  precision: number;
  recall: number;
  fpr: number;
}

/**
 * The description arms, read from the run that published them.
 *
 * The landing page draws these as a plot, and a plot is the most quotable
 * thing on a page — so it is the last place a retyped number belongs. They
 * come from the run record's own table, which is the artefact the numbers were
 * published in and the one a reader is sent to check.
 *
 * Cells are stripped of the emphasis a markdown table carries freely (`**`,
 * backticks) before parsing, so re-bolding a row in the record does not change
 * what the site draws — and a changed digit does.
 */
export async function armResults(run: string): Promise<Arm[]> {
  const record = (await getCollection('results')).find((entry) => entry.id.includes(run));
  if (!record) throw new Error(`No published run matching \`${run}\` in results/.`);

  const body = (record as { body?: string }).body;
  if (!body) throw new Error(`Run \`${run}\` has no body to read the arm table from.`);

  // Line-adjacent, for the same reason `routingTable` is: a run record holds
  // several tables, and filtering the pipe lines first lets the next one
  // continue this one.
  const lines = body.split('\n');
  const header = lines.findIndex((line) => {
    if (!isRow(line)) return false;
    const parsed = cells(line).map((cell) => cell.toLowerCase());
    return parsed[0] === 'arm' && parsed.includes('accuracy');
  });
  if (header === -1) throw new Error(`Run \`${run}\` has no table starting with an \`arm\` column.`);

  const names = cells(lines[header]).map((cell) => cell.toLowerCase());
  const at = (label: string) => names.indexOf(label);
  const bare = (cell: string) => cell.replace(/[*`]/g, '').trim();

  // Every column this reads, checked before a row is read. `indexOf` returns
  // -1 for a column that is not there and `parsed[-1]` is `undefined`, so a
  // renamed column arrived as a bare TypeError out of `bare`, carrying nothing
  // that named the run, the column or the file.
  const absent = (['accuracy', 'precision', 'recall', 'fpr'] as const).filter(
    (label) => at(label) === -1
  );
  if (absent.length) {
    throw new Error(
      `Run \`${run}\`'s arm table has no ${absent.map((l) => `\`${l}\``).join(', ')} ` +
        `column. It has: ${names.map((n) => `\`${n}\``).join(', ')}.`
    );
  }

  const arms: Arm[] = [];
  for (let i = header + 2; i < lines.length; i += 1) {
    if (!isRow(lines[i])) break;
    const parsed = cells(lines[i]);
    if (parsed.length !== names.length) break;
    const value = (label: string) => Number(bare(parsed[at(label)]));
    arms.push({
      arm: bare(parsed[0]),
      accuracy: value('accuracy'),
      precision: value('precision'),
      recall: value('recall'),
      fpr: value('fpr'),
    });
  }

  if (!arms.length) throw new Error(`Run \`${run}\`'s arm table has no rows.`);
  for (const arm of arms) {
    for (const [key, n] of Object.entries(arm)) {
      if (key !== 'arm' && !Number.isFinite(n as number)) {
        throw new Error(`Run \`${run}\`, arm \`${arm.arm}\`: \`${key}\` did not parse as a number.`);
      }
    }
  }
  return arms;
}

/**
 * Join the derived procedures to hand-written copy, and refuse a partial join.
 *
 * The plain-English names and examples a landing page needs have no source in
 * the repository and are legitimately written by hand. What is not legitimate
 * is letting them decide how many procedures there are: an array of four is
 * how the page came to say four while the skill said six.
 *
 * So the derived list drives the loop and the copy is a lookup that must be
 * total. A seventh procedure fails the build with its own name in the message
 * instead of quietly publishing six.
 */
export function requireCopy<T>(procedures: Procedure[], copy: Record<string, T>): (Procedure & T)[] {
  const missing = procedures.filter((p) => !(p.md in copy)).map((p) => p.md);
  if (missing.length) {
    throw new Error(
      `No landing copy for ${missing.join(', ')}. ` +
        "They are in SKILL.md's routing table, so the page has to say something about them.",
    );
  }
  const named = new Set(procedures.map((p) => p.md));
  const extra = Object.keys(copy).filter((md) => !named.has(md));
  if (extra.length) {
    throw new Error(
      `Landing copy for ${extra.join(', ')}, which SKILL.md no longer routes to. ` +
        'Delete the copy, or put the procedure back in the table.',
    );
  }
  return procedures.map((p) => ({ ...p, ...copy[p.md] }));
}
