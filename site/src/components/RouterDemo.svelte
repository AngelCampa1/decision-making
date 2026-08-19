<script>
  /**
   * The router, demonstrated rather than described.
   *
   * A question arrives, one procedure lights, and the panel shows what that
   * procedure hands back. This is the only interactive element on the site and
   * the only island: it exists because "it picks one of six depending on what
   * is hard" is a sentence people read past, and a thing they watch happen once
   * is a thing they understand.
   *
   * The examples are illustrative and the panel says so. They are not recorded
   * runs, and this repository would be the wrong place to blur that.
   *
   * Every panel is server-rendered into the HTML, so the first one is complete
   * and readable with JavaScript off.
   *
   * The other five are not reachable without it. This comment claimed they were
   * "reachable as anchors" until an adversarial review on 2026-08-19 checked:
   * the tabs are buttons with no href, the hidden panels are `display: none`,
   * and there is no `:target` rule anywhere in the built CSS. What a no-JS
   * visitor loses is the five worked examples. What they keep is the procedure
   * list further down the page, which names every method and when it fires --
   * so nothing here is the only route to a fact, but the demonstration itself
   * does need the script.
   */
  let { examples = [], segments = 6, repo = '' } = $props();

  let active = $state(0);
  let engaged = $state(false);

  const R = 26;
  const CIRCUMFERENCE = 2 * Math.PI * R;
  const arc = CIRCUMFERENCE / segments;
  const drawn = arc * 0.78;

  const ring = Array.from({ length: segments }, (_, i) => ({
    index: i,
    dasharray: `${drawn.toFixed(3)} ${(CIRCUMFERENCE - drawn).toFixed(3)}`,
    dashoffset: (-i * arc).toFixed(3),
  }));

  const current = $derived(examples[active] ?? examples[0]);

  /**
   * Advance until the reader takes over, then stop for good.
   *
   * Rotation that resumes after an interaction fights whoever is reading, and a
   * panel that changes while its text is being read is worse than one that
   * never moved. Reduced motion opts out entirely -- the tabs still work.
   */
  $effect(() => {
    if (engaged || examples.length < 2) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const id = setInterval(() => {
      active = (active + 1) % examples.length;
    }, 5200);
    return () => clearInterval(id);
  });

  function choose(i) {
    engaged = true;
    active = i;
  }

  /**
   * Move selection *and* focus together.
   *
   * The roving `tabindex` means the unselected tabs are `tabindex="-1"`. Moving
   * selection without moving focus therefore stranded the focus ring on a tab
   * that was no longer selected and no longer in the tab order: a sighted
   * keyboard user saw the ring and the highlight on two different tabs, a
   * screen-reader user heard nothing change at all, and the next `Tab` went
   * back *into* the tablist instead of leaving it.
   *
   * Up and down as well as left and right, because below 46rem the tabs wrap to
   * a 3x2 grid and horizontal is no longer the only axis a reader would try.
   * Home and End because a six-item tablist is long enough to want them.
   */
  function onKey(event) {
    const last = examples.length - 1;
    let next;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      next = active === last ? 0 : active + 1;
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      next = active === 0 ? last : active - 1;
    } else if (event.key === 'Home') {
      next = 0;
    } else if (event.key === 'End') {
      next = last;
    } else {
      return;
    }
    event.preventDefault();
    choose(next);
    // After the DOM has the new `tabindex`, or focus lands on an element that
    // is still -1 and the browser drops it.
    const id = `demo-tab-${examples[next].file}`;
    requestAnimationFrame(() => document.getElementById(id)?.focus());
  }
</script>

<div class="demo">
  <div class="demo__head">
    <p class="demo__ask" aria-live="polite">
      <span class="demo__quote">{current.ask}</span>
    </p>

    <svg class="demo__ring" viewBox="0 0 64 64" width="64" height="64" fill="none" aria-hidden="true">
      <g transform="rotate(-90 32 32)" stroke-width="5" stroke-linecap="butt">
        {#each ring as segment (segment.index)}
          <circle
            class={segment.index === active ? 'lit' : 'track'}
            cx="32"
            cy="32"
            r={R}
            stroke-dasharray={segment.dasharray}
            stroke-dashoffset={segment.dashoffset}
          />
        {/each}
      </g>
    </svg>
  </div>

  <!-- svelte-ignore a11y_no_noninteractive_element_to_interactive_role -->
  <div class="demo__tabs" role="tablist" aria-label="Which method runs" onkeydown={onKey}>
    {#each examples as example, i (example.md)}
      <button
        type="button"
        role="tab"
        id={`demo-tab-${example.file}`}
        aria-selected={i === active}
        aria-controls={`demo-panel-${example.file}`}
        tabindex={i === active ? 0 : -1}
        class:is-active={i === active}
        onclick={() => choose(i)}
      >
        <span class="demo__ord">{example.ord}</span>
        <span class="demo__name">{example.name}</span>
      </button>
    {/each}
  </div>

  {#each examples as example, i (example.md)}
    <div
      class="demo__panel"
      id={`demo-panel-${example.file}`}
      role="tabpanel"
      aria-labelledby={`demo-tab-${example.file}`}
      hidden={i !== active}
    >
      <p class="demo__when">
        {example.when}
        <a class="demo__file" href={`${repo}/blob/main/${example.path}`}>{example.md}</a>
      </p>
      <pre class="demo__out">{example.after}</pre>
    </div>
  {/each}

  <p class="demo__note">
    Examples, not recorded runs. They show the shape of the answer.
  </p>
</div>

<style>
  .demo {
    border: 1px solid var(--rule);
    border-radius: var(--radius-3);
    background: var(--raised);
    overflow: hidden;
  }

  .demo__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-lg);
    padding: var(--space-lg) var(--space-lg) var(--space-md);
    border-bottom: 1px solid var(--rule-hair);
  }

  .demo__ask {
    margin: 0;
    font-size: clamp(1.0625rem, 1rem + 0.4vw, 1.375rem);
    line-height: 1.35;
    color: var(--ink-strong);
    letter-spacing: -0.018em;
    text-wrap: balance;
  }

  .demo__quote::before {
    content: '\201C';
  }

  .demo__quote::after {
    content: '\201D';
  }

  .demo__ring {
    flex: none;
  }

  .demo__ring .track {
    stroke: var(--mark-track);
  }

  .demo__ring .lit {
    stroke: var(--signal);
  }

  @media (prefers-reduced-motion: no-preference) {
    .demo__ring circle {
      transition: stroke var(--dur-2) var(--ease);
    }
  }

  .demo__tabs {
    display: grid;
    grid-template-columns: repeat(var(--tabs, 6), minmax(0, 1fr));
    border-bottom: 1px solid var(--rule-hair);
  }

  .demo__tabs button {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    align-items: flex-start;
    padding: var(--space-sm) var(--space-md);
    background: transparent;
    border: 0;
    border-inline-start: 1px solid var(--rule-hair);
    border-bottom: 2px solid transparent;
    cursor: pointer;
    text-align: left;
    color: var(--ink-muted);
    transition:
      color var(--dur-1) var(--ease),
      background var(--dur-1) var(--ease);
  }

  .demo__tabs button:first-child {
    border-inline-start: 0;
  }

  .demo__tabs button:hover {
    color: var(--ink-secondary);
    background: var(--inset);
  }

  .demo__tabs button.is-active {
    color: var(--ink-strong);
    border-bottom-color: var(--signal);
    background: var(--ground);
  }

  .demo__ord {
    font: 500 0.625rem/1 var(--font-mono);
    letter-spacing: 0.1em;
    color: var(--ink-muted);
  }

  .demo__name {
    font: 500 0.8125rem/1.25 var(--font-sans);
    letter-spacing: -0.005em;
  }

  .demo__file {
    float: right;
    margin-inline-start: var(--space-md);
    font: 500 0.75rem/1.6 var(--font-mono);
    color: var(--ink-muted);
  }

  .demo__file:hover {
    color: var(--signal);
  }

  .demo__panel {
    padding: var(--space-lg);
    background: var(--ground);
  }

  .demo__panel[hidden] {
    display: none;
  }

  .demo__when {
    margin: 0 0 var(--space-md);
    font-size: 0.9375rem;
    color: var(--ink-secondary);
  }

  .demo__out {
    margin: 0;
    padding: 0;
    border: 0;
    background: transparent;
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    line-height: 1.75;
    color: var(--ink);
    white-space: pre-wrap;
    overflow-x: auto;
  }

  .demo__note {
    margin: 0;
    padding: var(--space-sm) var(--space-lg);
    border-top: 1px solid var(--rule-hair);
    font: 400 0.75rem/1.5 var(--font-mono);
    color: var(--ink-muted);
  }

  @media (max-width: 46rem) {
    .demo__head {
      flex-direction: column-reverse;
      align-items: flex-start;
    }

    .demo__tabs {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .demo__tabs button {
      border-top: 1px solid var(--rule-hair);
    }
  }
</style>
