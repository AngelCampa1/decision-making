// @ts-check
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import rewriteLinks from './src/lib/remark-rewrite-links.mjs';
import rehypeTables from './src/lib/rehype-tables.mjs';

// The content collections read markdown from directories above this project
// root (../docs, ../notebook, ...). Astro's content layer reads those with
// Node's fs, so the build never asks Vite to resolve them -- but the dev
// server's /@fs/ guard would refuse them the moment a rendered .md gained a
// relative image. There are none today. This entry is the insurance, and it is
// deliberate rather than leftover: delete it only if the content roots move
// inside site/.
const repoRoot = fileURLToPath(new URL('..', import.meta.url));

export default defineConfig({
  // Svelte is here for exactly one island, the router demo on the landing page.
  // It is loaded `client:visible`, and all of its panels are server-rendered, so
  // the page is complete and readable before any of this arrives.
  integrations: [svelte()],
  site: 'https://angelcampa1.github.io',
  base: '/decision-making-skills',
  // Astro's default content cache is node_modules/.astro, which survives a
  // `rm -rf .astro dist` and then serves markdown rendered by an older version
  // of the link-rewrite plugin -- a stale page that looks perfectly fine. Put
  // it somewhere `de site` can find and clear.
  cacheDir: './.astro-cache',
  markdown: {
    remarkPlugins: [rewriteLinks],
    rehypePlugins: [rehypeTables],
    // No syntax highlighting. Astro's default is a fixed dark theme, which is
    // wrong on a light page, and the dual-theme output is a rainbow -- this
    // system highlights with weight and one hue or not at all. Most fenced
    // blocks here are shell commands anyway, where the copy target is the whole
    // line and colouring it is decoration. Plain output also lets --code-fg and
    // --code-bg follow the theme instead of fighting inline styles.
    syntaxHighlight: false,
  },
  vite: { server: { fs: { allow: [repoRoot] } } },
});
