/* schema.org JSON-LD for every page, in one module.
 *
 * Structured data is the machine-readable half of a page: it is what a search
 * engine, and increasingly a model, reads to decide what a URL *is* rather than
 * which words are on it. This site had none, so 159 pages of methodology, dated
 * research log and published run records were indistinguishable from each other
 * and from the landing page.
 *
 * What is deliberately absent, and why. There is no `aggregateRating`, no
 * `Review`, no `FAQPage`: that is the markup which asserts a thing is good, and
 * no skill here carries a verdict. A rating on a repository whose scorecard
 * reads 0 proven would be the same overclaim as a Beta classifier, one metadata
 * layer further out.
 *
 * `kindMeta()` throws, on the pattern `verdicts.ts` set. The consequence is
 * that the eyebrow string on a rendered document is load-bearing: change
 * `kind="the skill"` in a page template and the build fails rather than quietly
 * publishing a run record as an article. That is the intended trade.
 */
import { REPO, BRANCH } from './site.ts';

export const LICENSE_URL = 'https://www.apache.org/licenses/LICENSE-2.0';

export const PERSON = { name: 'Angel Campa', url: 'https://github.com/AngelCampa1' };

export interface Section {
  /** Must match the `h1` the section index prints, or the breadcrumb lies. */
  label: string;
  /** Base-relative, with both slashes: `/docs/`. */
  path: string;
}

export interface KindMeta {
  ogType: 'article' | 'website';
  schemaType: 'TechArticle' | 'Dataset';
  /** `null` for a root document, which sits directly under the site. */
  section: Section | null;
}

/** Keyed on the `kind` strings the page templates already pass to `Doc.astro`. */
export const KINDS: Record<string, KindMeta> = {
  documentation: {
    ogType: 'article',
    schemaType: 'TechArticle',
    section: { label: 'Documentation', path: '/docs/' },
  },
  'notebook · append-only': {
    ogType: 'article',
    schemaType: 'TechArticle',
    section: { label: 'Research log', path: '/notebook/' },
  },
  'published run record': {
    ogType: 'article',
    schemaType: 'Dataset',
    section: { label: 'Published runs', path: '/results/' },
  },
  'the skill': {
    ogType: 'article',
    schemaType: 'TechArticle',
    section: { label: 'The skill', path: '/skill/' },
  },
  repository: { ogType: 'article', schemaType: 'TechArticle', section: null },
};

/** Throws on a kind this module has never been told about. */
export function kindMeta(kind: string): KindMeta {
  const found = KINDS[kind];
  if (!found) {
    throw new Error(
      `Unknown page kind \`${kind}\`. The structured data is keyed on the ` +
        `eyebrow string, so a new one is declared here: ${Object.keys(KINDS).join(', ')}.`,
    );
  }
  return found;
}

/**
 * `2026-08-19-d52236a-n7-remaining-arms` -> `2026-08-19`.
 *
 * Undefined when the id carries no date, which is every document under `docs/`.
 * A publication date is never inferred from a file mtime: the only one CI has
 * is the clone time, which would stamp a single fabricated date across the site.
 */
export function dateFromId(id: string): string | undefined {
  return (id.split('/').pop() ?? id).match(/^(\d{4}-\d{2}-\d{2})/)?.[1];
}

export function graph(nodes: object[]): object {
  return { '@context': 'https://schema.org', '@graph': nodes };
}

export function personNode(siteRoot: string): object {
  return { '@type': 'Person', '@id': `${siteRoot}#angel-campa`, ...PERSON };
}

export function websiteNode(siteRoot: string, description: string): object {
  return {
    '@type': 'WebSite',
    '@id': `${siteRoot}#website`,
    url: siteRoot,
    name: 'decision-making-skills',
    inLanguage: 'en',
    description,
    license: LICENSE_URL,
    publisher: { '@id': `${siteRoot}#angel-campa` },
  };
}

/** The repository itself, referenced by `@id` from the landing page and the skill index. */
export function softwareNode(siteRoot: string, description: string, version: string): object {
  return {
    '@type': 'SoftwareSourceCode',
    '@id': `${siteRoot}#skill`,
    name: 'decision-making',
    description,
    codeRepository: REPO,
    programmingLanguage: 'Markdown',
    runtimePlatform: 'AI agent (Agent Skills standard)',
    version,
    license: LICENSE_URL,
    isAccessibleForFree: true,
    author: { '@id': `${siteRoot}#angel-campa` },
    keywords: [
      'agent skills',
      'LLM evaluation',
      'evaluation harness',
      'decision making',
      'ablation study',
      'placebo control',
    ],
  };
}

export function webPageNode(
  canonical: string,
  siteRoot: string,
  title: string,
  description: string,
): object {
  return {
    '@type': 'WebPage',
    '@id': canonical,
    url: canonical,
    name: title,
    description,
    inLanguage: 'en',
    isPartOf: { '@id': `${siteRoot}#website` },
    about: { '@id': `${siteRoot}#skill` },
  };
}

export function collectionNode(
  canonical: string,
  siteRoot: string,
  title: string,
  description: string,
): object {
  return {
    '@type': 'CollectionPage',
    '@id': canonical,
    url: canonical,
    name: title,
    description,
    inLanguage: 'en',
    isPartOf: { '@id': `${siteRoot}#website` },
  };
}

export function documentNode(opts: {
  canonical: string;
  siteRoot: string;
  title: string;
  description: string;
  meta: KindMeta;
  sourcePath: string;
  datePublished?: string;
}): object {
  const { canonical, siteRoot, title, description, meta, sourcePath, datePublished } = opts;
  const dataset = meta.schemaType === 'Dataset';
  return {
    '@type': meta.schemaType,
    '@id': `${canonical}#${dataset ? 'dataset' : 'article'}`,
    url: canonical,
    [dataset ? 'name' : 'headline']: title,
    description,
    inLanguage: 'en',
    license: LICENSE_URL,
    [dataset ? 'creator' : 'author']: { '@id': `${siteRoot}#angel-campa` },
    isPartOf: { '@id': `${siteRoot}#website` },
    // Where the document actually lives. This site renders the repository in
    // place, so the link is provenance rather than a citation.
    isBasedOn: `${REPO}/blob/${BRANCH}/${sourcePath}`,
    ...(dataset ? { isAccessibleForFree: true } : { mainEntityOfPage: canonical }),
    ...(datePublished ? { datePublished } : {}),
  };
}

export function breadcrumbNode(opts: {
  canonical: string;
  siteRoot: string;
  title: string;
  section: Section | null;
}): object {
  const { canonical, siteRoot, title, section } = opts;
  const root = siteRoot.replace(/\/$/, '');
  const trail: object[] = [
    { '@type': 'ListItem', position: 1, name: 'decision-making-skills', item: siteRoot },
  ];
  if (section) {
    trail.push({
      '@type': 'ListItem',
      position: 2,
      name: section.label,
      item: `${root}${section.path}`,
    });
  }
  trail.push({ '@type': 'ListItem', position: trail.length + 1, name: title });
  return { '@type': 'BreadcrumbList', '@id': `${canonical}#breadcrumb`, itemListElement: trail };
}
