/** Canonical repository URL. Every off-site rewrite is built from this. */
export const REPO = 'https://github.com/AngelCampa1/decision-making-skills';

/** Branch the blob/tree rewrites point at. */
export const BRANCH = 'main';

/**
 * What this site is, in one sentence, for the machines.
 *
 * Used by the `WebSite` node of every page's structured data, so it is the
 * site-level answer rather than any page's. Deliberately carries no measured
 * number: it is repeated on 159 pages and cached by every crawler that has seen
 * one of them, so it says only what stays true.
 */
export const SITE_DESCRIPTION =
  'Agent skills for decisions under uncertainty, plus the evaluation harness ' +
  'that measures whether they work: pre-registered, placebo-controlled, and ' +
  'public about what has not been shown.';

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
