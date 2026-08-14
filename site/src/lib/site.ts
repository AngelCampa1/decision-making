/** Canonical repository URL. Every off-site rewrite is built from this. */
export const REPO = 'https://github.com/AngelCampa1/decision-making-skills';

/** Branch the blob/tree rewrites point at. */
export const BRANCH = 'main';

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
