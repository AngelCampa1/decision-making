/* `/llms-full.txt`: the citable documents, concatenated, for a model that has
 * followed `/llms.txt` and wants the text rather than the links.
 *
 * Deliberately not everything. The repository is ~170 published documents, and
 * most of that weight is `notebook/` and `results/`, which are append-only
 * evidence: valuable to a person auditing a specific run, useless as a citation
 * source when it arrives as several megabytes of dated entries. What is here is
 * the skill itself and the documents that say how it is measured and what has
 * come out. Those are the parts somebody would actually be citing.
 *
 * Each document is preceded by its own source path, so a quotation taken from
 * this file can be traced back to the file it came from rather than to this
 * concatenation.
 *
 * The limitation, stated rather than left implied: this publishes whole bodies
 * verbatim, so it carries every corrected-in-place figure those documents carry,
 * including the ones `site/claims.json` records as retracted. That is the same
 * text `/docs/status/` already renders and it arrives with its correction
 * attached, but a reader lifting a number out of a correction would get the
 * withdrawn one. No guard here would help: removing the sentence would destroy
 * the correction it belongs to.
 */
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { BRANCH, REPO } from '../lib/site.ts';

/** Repository documents worth citing, as `collection:id` pairs, in reading order. */
const INCLUDE = [
  'skills:decision-making/skill',
  'skills:decision-making/ledger',
  'skills:decision-making/fit',
  'skills:decision-making/cascade',
  'skills:decision-making/timing',
  'skills:decision-making/council',
  'skills:decision-making/hinge',
  'skills:decision-making/placebo',
  'docs:methods',
  'docs:protocol',
  'docs:eval_set_datasheet',
  'docs:harness_disclosure',
  'docs:limitations',
  'docs:failure_taxonomy',
  'docs:status',
  'root:scorecard',
];

type Loaded = { id: string; body?: string; filePath?: string };

export const GET: APIRoute = async () => {
  const collections = new Map<string, Map<string, Loaded>>();
  for (const name of ['skills', 'docs', 'root'] as const) {
    const entries = (await getCollection(name)) as unknown as Loaded[];
    collections.set(name, new Map(entries.map((entry) => [entry.id, entry])));
  }

  const parts: string[] = [
    '# decision-making-skills, full text',
    '',
    'The skill and the documents describing how it is measured. The research log',
    `and the run records are not here; they are at ${REPO}.`,
    '',
  ];

  for (const spec of INCLUDE) {
    const [collection, id] = spec.split(':');
    const entry = collections.get(collection)?.get(id);
    // A renamed document drops out rather than emitting an empty section.
    if (!entry?.body) continue;
    const source = (entry.filePath ?? '').replace(/\\/g, '/').replace(/^(\.\.\/)+/, '');
    parts.push('---', '', `Source: ${REPO}/blob/${BRANCH}/${source}`, '', entry.body.trim(), '');
  }

  return new Response(parts.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
