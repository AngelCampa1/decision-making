/* The verdict vocabulary, as this site spells it.
 *
 * The vocabulary itself belongs to `SCORECARD.md`, which defines what each one
 * licenses you to claim, and to `decision_evals.skills.VERDICTS`, which
 * enforces it on skill frontmatter. This module is neither of those. It is the
 * lowercase spelling the CSS keys on, plus a guard so a typo in a `data-state`
 * attribute fails the build instead of silently rendering an unstyled badge.
 *
 * Deliberately not a second source of truth: nothing here decides which verdict
 * a skill has, and nothing on this site branches on which one it is. If a
 * seventh verdict is ever added to SCORECARD.md, this list is one of the two
 * places that has to learn about it — the other is `base.css` — and both fail
 * loudly rather than quietly.
 */

export const VERDICT_STATES = [
  'ship',
  'provisional',
  'null',
  'harmful',
  'untested',
  'withdrawn',
] as const;

export type VerdictState = (typeof VERDICT_STATES)[number];

/**
 * Normalise a frontmatter verdict (`UNTESTED`) to the spelling the CSS uses.
 *
 * Throws on anything unrecognised. A verdict this site cannot render is a
 * verdict this site must not guess at — the whole point of the vocabulary is
 * that `UNTESTED` and `HARMFUL` are different claims.
 */
export function verdictState(verdict: string): VerdictState {
  const lower = verdict.trim().toLowerCase();
  if ((VERDICT_STATES as readonly string[]).includes(lower)) {
    return lower as VerdictState;
  }
  throw new Error(
    `Unknown verdict \`${verdict}\`. SCORECARD.md defines the vocabulary: ` +
      `${VERDICT_STATES.join(', ')}.`,
  );
}
