# Five repeats: firing is stable, routing is not

**2026-08-12.** Track M2/M3. 73 cases × 5 repeats = 365 isolated calls, Haiku,
0 unparseable, 0 isolation failures. Supersedes both single runs from earlier
today.

**No numeric bands were registered before this run.** It was launched as "repeats
are now the priority" without predictions attached. That is the third
pre-registration slip today — one band was unscoreable as written, one entry was
written after its run started, and this run had none — so the numbers below are
descriptive and none of them scores a prediction.

## Firing is stable and it is good

| | mean | sd | range |
|---|---|---|---|
| precision | **0.942** | 0.039 | 0.889–1.000 |
| recall | **0.878** | 0.025 | 0.833–0.889 |
| false-positive rate | **0.018** | 0.013 | 0.000–0.036 |

**70 of 73 items returned the identical verdict all five times.** Three moved:
`p09` fired 4/5, `n11` 3/5, `n07` 2/5. ICC 0.741, and `repeats_for_reliability`
says 4 repeats for r = 0.9. So five was about right and one was never going to be
enough.

One in fifty-five look-alike negatives interrupting an ordinary turn is the
number that decides whether the skill is worth having installed, and it holds up
across repeats.

## Routing is not stable, and one run of it means nothing

| repeat | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| routing accuracy | 0.857 | 0.643 | 0.643 | 0.571 | 0.714 |

**mean 0.686, sd 0.108, range 0.571–0.857.**

The two earlier runs today both read 0.643 and this run's repeat 0 reads 0.857.
Those are not three findings. They are three draws from one distribution with a
standard deviation of eleven points, on fourteen labelled items.

This morning's entry concluded that "the aggregate is stable while per-item
verdicts move". **That was right about firing and wrong about routing.** Routing
looked stable because two independent single runs happened to land on the same
value, which at sd = 0.108 is a coincidence I read as a result.

## The cascade/timing confusion is real underneath the noise

Per-item, across five repeats:

| Item | Wanted | Right | What it returned |
|---|---|---|---|
| `p01` `p02` `p05` `p08` `p10` `p11` `x-n23` | — | **5/5** | stable and correct |
| `p09` | cascade | 4/5 | one `None` |
| `x-n20` | timing | 4/5 | one `cascade` |
| `p04` | fit | 3/5 | `cascade`, `timing` |
| `p03` | ledger | 1/5 | `fit` ×3, `None` |
| `p07` | cascade | 1/5 | `timing` ×4 |
| `p06` | fit | **0/5** | `cascade` ×2, `timing` ×3 |
| `x-n22` | timing | **0/5** | `None` ×5 — it never fires |

Seven items are perfectly stable, five wobble, two are stably wrong. So the
router has a **hard core and a noisy shell**, and only the core is worth acting
on:

- `p06` is never routed to `fit` and `p07` almost never to `cascade`. Both drift
  to `timing`.
- `p07` was already repaired once today to remove its time words, and it still
  goes to `timing` four times in five. The repair was not the problem.

**`cascade` and `timing` are genuinely confusable**, which the router's own table
would predict — one is about what an action sets in motion, the other about when
to take it, and most decisions have both. That survives the noise. The specific
per-run confusion lists do not.

## Two labels of mine are worth eleven points of recall

`x-n21` (*"The disk is at 99%. Do we need to act?"*) and `x-n22` (*"The build is
green. Can I deploy?"*) **fired 0 times out of 5 each**. They are the only two
misses in the whole set.

| | precision | recall | FPR |
|---|---|---|---|
| all 73 cases | 0.942 | **0.878** | 0.018 |
| excluding `x-n21`, `x-n22` | 0.942 | **0.988** | 0.018 |

That is what the comment in `decision-making.yaml` demanded be reported both
ways, and the gap is larger than I expected: **recall is 0.878 or 0.988 depending
on two labels I wrote myself, in one sitting, alongside the argument for
promoting them.**

What five repeats *do* settle is that this is a **stable disagreement, not a coin
flip**. This morning the evidence was "one fired once, two never fired" and could
not distinguish noise from signal. Now it can: of the five cases promoted out of
`evidence-ledger`'s negatives, `x-n03`, `x-n20` and `x-n23` fire 5/5 and `x-n21`
and `x-n22` fire 0/5. Nothing in between.

The two readings from this morning both survive — either the promotion was wrong,
or consolidating four skills behind one router widened the description on paper
and not in behaviour — and the run still cannot separate them. But it is now a
disagreement about a label rather than a question about measurement, which is the
form in which it belongs to the maintainer.

## What is quotable now

- **Firing: precision 0.942, recall 0.878, FPR 0.018**, over 5 repeats, with the
  recall caveat above stated in the same breath.
- **Routing: 0.686 ± 0.108.** Not 0.643 and not 0.857.
- **Availability is not the problem; selection within the bundle is.** That
  reading from this morning survives, and the gap is now bigger than it looked:
  0.942 against 0.686.
- Still a **proxy**. The model is shown one description and asked whether it
  would fire. In the real harness that description sits among others, in a longer
  context, mid-task. Skill shadowing is precisely the claim that other
  descriptions change this number.

## Next

- **Four repeats minimum** for anything on this instrument, from ICC 0.741.
- **`p06` and `p07` are worth reading as router-table defects**, not as noise.
  They are the two items the router gets stably wrong.
- The `p_fire` calibration run is wired and predicted; it has not been run.
