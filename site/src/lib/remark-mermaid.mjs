/**
 * Mermaid fences become elements the browser can render.
 *
 * The diagrams in `docs/ARCHITECTURE.md` and `docs/DOCUMENTATION_MAP.md` are
 * authored as ```` ```mermaid ```` fences because that is the one form that is
 * a diagram on github.com and a diff in git at the same time. Nothing in the
 * repository stores a rendered copy, for the same reason the site renders the
 * repository's markdown in place: a generated image is a second version of a
 * document, and a second version falls behind.
 *
 * This runs on the mdast, before `syntaxHighlight: false` decides what a code
 * block turns into, so the language tag is read from `node.lang` and not from
 * a class name a highlighter may or may not have attached.
 *
 * What lands in the HTML is `<pre class="mermaid">` holding the escaped source.
 * Mermaid reads `textContent`, so the escaping round-trips, and a reader whose
 * JavaScript never arrives gets the source as text rather than a blank space
 * where a diagram was promised.
 */
import { visit } from 'unist-util-visit';

/** `&` first, or the entities this produces get escaped a second time. */
const escape = (source) =>
  source
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

export default function remarkMermaid() {
  return function transformer(tree) {
    visit(tree, 'code', (node, index, parent) => {
      if (node.lang !== 'mermaid' || !parent || index === null) return;
      // `figure` rather than a bare `pre`: the diagram is a block-level
      // illustration with its own scroller, and `.doc__body > *` grid rules
      // need one element to place.
      parent.children[index] = {
        type: 'html',
        value:
          '<figure class="diagram">' +
          `<pre class="mermaid">${escape(node.value)}</pre>` +
          '</figure>',
      };
    });
  };
}
