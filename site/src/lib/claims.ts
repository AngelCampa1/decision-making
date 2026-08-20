/* Measured numbers the site publishes that nothing in the repository can compute.
 *
 * Most facts on this site are derived -- see `facts.ts`, where the procedure
 * list is read from SKILL.md and a page that disagrees fails the build. These
 * are the ones that cannot be: how many model calls have been made, how many
 * of our own measurements turned out broken, how much of the trigger corpus a
 * word count can solve. They live in prose in `docs/STATUS.md` and
 * `SCORECARD.md`, which are hand-maintained and say so.
 *
 * A number that cannot be derived can still be *bound*. Each entry in
 * `site/claims.json` carries the sentence it came from, and
 * `decision_evals.claims` refuses `de check` when that sentence is no longer
 * in the document. One file, two readers -- the same arrangement as
 * `site/inputs.json`, and for the same reason: a generated second copy would
 * recreate the disagreement the arrangement exists to prevent.
 *
 * The standing limitation, so nobody reads more into a green gate than is
 * there: this binds a number to a sentence, and cannot tell whether that
 * sentence is still the document's answer. `docs/STATUS.md` corrects by
 * appending and holds three true totals at once.
 */
import data from '../../claims.json';

export interface Claim {
  id: string;
  /** The figure as the source states it: `~4,816`. */
  value: string;
  /** What the page prints instead, when the page publishes fewer digits. */
  rounded: string | null;
  /** Repo-relative path to the document this came from. */
  source: string;
  /** The sentence, verbatim. The Python gate re-finds it. */
  quote: string;
  /** Regex whose *last* match in the source must still be `value`, for documents that correct by appending. */
  latest: string | null;
  /** Why this is a claim and not a derivation. Required. */
  why: string;
}

const CLAIMS: Map<string, Claim> = new Map(
  (data.claims as Claim[]).map((entry) => [entry.id, entry]),
);

/**
 * One claim, by id.
 *
 * Throws on an unknown id rather than rendering `undefined` into a published
 * page. `decision_evals.claims` greps for these call sites, so a claim
 * declared and never published is also a refusal -- the binding runs both ways.
 */
export function claim(id: string): Claim {
  const found = CLAIMS.get(id);
  if (!found) {
    throw new Error(
      `No claim \`${id}\` in site/claims.json. Declare it there, with the ` +
        'sentence it comes from, or do not publish the number.',
    );
  }
  return found;
}

/** What the page prints: the rounded figure when there is one, the source figure otherwise. */
export function shown(id: string): string {
  const found = claim(id);
  return found.rounded ?? found.value;
}

/**
 * Phrases this repository has withdrawn, as `site/claims.json` records them.
 *
 * `decision_evals.claims` refuses a page whose source text carries one. A
 * description derived from markdown at build time is not source text and is not
 * seen by that gate, so `descriptions.ts` reads this register directly. One
 * list, two readers -- the same arrangement as the claims above, and for the
 * same reason.
 */
export function retractedPhrases(): string[] {
  return (data.retractions as { phrase: string }[]).map((entry) => entry.phrase);
}

/** Where a figure came from, for a citation line under a statistic. */
export function attribution(id: string): { source: string; href: string } {
  const found = claim(id);
  return { source: found.source, href: found.source };
}
