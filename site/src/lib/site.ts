/** Canonical repository URL. Every off-site rewrite is built from this. */
export const REPO = 'https://github.com/AngelCampa1/decision-making-skills';

/** Branch the blob/tree rewrites point at. */
export const BRANCH = 'main';

/**
 * What the skill is, in one sentence, for the machines.
 *
 * Used by the `SoftwareSourceCode` node on the landing page and the skill
 * index, and as the `/skill/` page's own description. Deliberately carries no
 * measured number: a crawler caches it and there is no correcting it once
 * posted, so it says only what stays true.
 */
export const SKILL_DESCRIPTION =
  'One skill that works out what is hard about a decision, then runs a single ' +
  'procedure for it. Plain markdown, Apache-2.0, and free.';

/**
 * What this site is, in one sentence.
 *
 * The `WebSite` node of every page's structured data carries it, so it is the
 * site-level answer rather than any page's, and `Doc.astro` falls back to it
 * for a document whose body yields no summary. Same rule as above: no measured
 * number.
 *
 * It read `placebo-controlled` until 2026-08-20. The placebo arm is written and
 * `check_placebo_match` sizes it on every gate run, and no published run has
 * used it, so the present indicative claimed a control that has never stood in
 * for anything. Arms belong here as a design or not at all.
 */
export const SITE_DESCRIPTION =
  'Agent skills for decisions under uncertainty, and the evaluation harness ' +
  'that measures them: pre-registered predictions, blind labels, every run ' +
  'published.';

export interface NavItem {
  label: string;
  href: string;
  /** Hidden on narrow viewports rather than wrapped. */
  wide?: boolean;
}

export const NAV: NavItem[] = [
  { label: 'skill', href: '/skill/' },
  { label: 'results', href: '/docs/status/' },
  { label: 'scorecard', href: '/scorecard/' },
  { label: 'notebook', href: '/notebook/', wide: true },
  { label: 'docs', href: '/docs/', wide: true },
];
