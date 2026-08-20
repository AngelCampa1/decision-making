/* `/llms.txt` -- a plain-text index of this site for a model that is citing it.
 *
 * Generated rather than written. A static file listing the runs and the
 * procedures would be a hand-maintained index, and this repository has two
 * separate written records of hand-maintained indexes drifting: `docs/STATUS.md`
 * opens with the count it got wrong three times, and `SCORECARD.md` carries a
 * note about a status file that claimed to be generated and was not.
 *
 * Every note comes from `descriptionFrom()` on the same body the page's meta
 * description is derived from, so this file and the pages it points at cannot
 * disagree about what a document says.
 *
 * Any figure here goes through `shown()`. Typing a digit into this file would
 * publish a number nothing checks -- `decision_evals.claims` scans this file for
 * exactly those calls, and a bare digit is what it cannot see.
 *
 * The limitation, stated because the convention hides it: this is served at
 * `/decision-making-skills/llms.txt`, not at the origin root, because the origin
 * belongs to a user-pages repository that does not exist. A tool that guesses
 * the root URL gets a 404.
 */
import type { APIRoute } from 'astro';
import { getCollection, render } from 'astro:content';
import { shown } from '../lib/claims.ts';
import { descriptionFrom } from '../lib/descriptions.ts';
import { skillFacts } from '../lib/facts.ts';
import { REPO, SITE_DESCRIPTION } from '../lib/site.ts';
import { stripReadme, titleFrom } from '../lib/titles.ts';

/** Shorter than a meta description: this is a line in a list, not a summary card. */
const NOTE_LIMIT = 110;

/** Documents that answer "how was this measured", in the order a reader needs them. */
const METHOD_DOCS = [
  'methods',
  'protocol',
  'eval_set_datasheet',
  'harness_disclosure',
  'failure_taxonomy',
  'limitations',
];

/** Documents that answer "what came out of it". */
const FINDING_DOCS = ['status', 'research_programme'];

type Body = { body?: string };

export const GET: APIRoute = async ({ site }) => {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const url = (path: string) => new URL(`${base}${path}`, site).href;

  const facts = await skillFacts();
  const docs = await getCollection('docs');
  const results = await getCollection('results');
  const notebook = await getCollection('notebook');

  const byId = new Map(docs.map((entry) => [entry.id, entry]));
  const line = (title: string, path: string, note: string) => `- [${title}](${url(path)}): ${note}`;

  /** Null when the document is absent, so a renamed doc drops a line instead of printing a broken one. */
  const docLine = async (id: string) => {
    const entry = byId.get(id);
    if (!entry) return null;
    const { headings } = await render(entry);
    const title = titleFrom(headings, id);
    return line(title, `/docs/${id}/`, descriptionFrom((entry as Body).body, title, NOTE_LIMIT));
  };

  const methodLines = (await Promise.all(METHOD_DOCS.map(docLine))).filter(Boolean) as string[];
  const findingLines = (await Promise.all(FINDING_DOCS.map(docLine))).filter(Boolean) as string[];

  const runs = await Promise.all(
    results.map(async (entry) => {
      const slug = stripReadme(entry.id).replace(/\/$/, '');
      const { headings } = await render(entry);
      return {
        slug,
        title: titleFrom(headings, entry.id),
        note: descriptionFrom((entry as Body).body, 'A published run.', NOTE_LIMIT),
      };
    }),
  );
  runs.sort((a, b) => (a.slug < b.slug ? 1 : -1));

  const sections = [
    `# decision-making-skills`,
    ``,
    `> ${SITE_DESCRIPTION}`,
    `>`,
    `> Nothing here has passed a confirmatory test. Every result is published,`,
    `> including the measurements that turned out to be broken.`,
    `>`,
    `> Repository: ${REPO}`,
    ``,
    `## The skill`,
    ``,
    line('decision-making', '/skill/', `One router, ${facts.countWord.toLowerCase()} procedures, and it reads one.`),
    ...facts.procedures.map((p) =>
      line(p.md, `/skill/decision-making/${p.file}/`, `When ${p.hard.charAt(0).toLowerCase()}${p.hard.slice(1)}`),
    ),
    ``,
    `## How it is measured`,
    ``,
    ...methodLines,
    ``,
    `## What has been found`,
    ``,
    line('Scorecard', '/scorecard/', 'What may be publicly claimed about each skill. Empty on purpose.'),
    ...findingLines,
    line(
      'The shortcut audit',
      '/docs/status/',
      `The retired trigger corpus was solvable at ${shown('corpus-solvability')} by counting words alone, ` +
        `so every result on it was competing for ${shown('headroom-points')} over a ruler. ` +
        `On the rebuilt corpus the best model-free shortcut reaches ${shown('word-trick-ceiling')}.`,
    ),
    ``,
    `## Published runs`,
    ``,
    ...runs.map((run) => line(run.title, `/results/${run.slug}/`, run.note)),
    ``,
    `## Optional`,
    ``,
    line('Research log', '/notebook/', `${notebook.length} dated entries. Predictions are committed before their runs.`),
    line('Full text', '/llms-full.txt', 'The skill and the methods documents, concatenated.'),
    ``,
  ];

  return new Response(sections.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
