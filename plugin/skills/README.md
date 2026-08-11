# Why this directory is empty

This is where skills land **after** a confirmation run gives them a verdict, and
nothing has one yet.

The directory is generated, not authored. `de mirror` copies a skill here only
when its `metadata.verdict` is something other than `UNTESTED`, and removes it
again if that verdict is ever withdrawn. So the rule that an unproven skill
cannot ship is a property of how the directory is built, rather than a check
that has to be remembered.

The skills themselves live in [`../../skills/`](../../skills/) and are usable
today — install them from there, or from
[`../../.agents/skills/`](../../.agents/skills/) if your tool reads that path.
What's missing is not the skill, it is the evidence, and this directory is the
part of the repository that refuses to imply otherwise.

Progress is tracked in [`../../SCORECARD.md`](../../SCORECARD.md).
