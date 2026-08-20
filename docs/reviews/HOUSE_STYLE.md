# Review brief: house style

**Audience:** an agent reviewing a draft. This is a prompt, so read it as your
instructions.

Check a draft against [`VOICE.md`](../VOICE.md). Read that file first. It is the
standard and this brief is only the procedure for applying it.

This review is the only thing standing between a draft and the repository.
`de check` refuses a reference that does not resolve and declines to judge the
sentence around it, on purpose, so the judgement here is yours.

## Procedure

**1. Audience.** Name the document's audience from `VOICE.md`. Say whether the
draft declares it, and whether the register matches the one that audience gets.
A document serving two audiences is the finding, so report it.

**2. Count the banned patterns.** Report each with line numbers and a count.

| Pattern | How to find it |
| --- | --- |
| Negative parallelism | `, not ` and `rather than` and `instead of` |
| Em dashes | the character itself, and the `--` spelling |
| Apology or correction in the opening | read the first two sentences |
| Pre-empting an objection | look for "that is not", "this does not mean", "nothing here is" |
| Rule of three | three parallel clauses or a three-item list where the count is not forced |
| Announcing the writing | "it is worth noting", "importantly", "in this section" |
| Self-deprecation as credibility | an admission that buys nothing |

A count alone is not a finding. For each one, say whether removing it would cost
meaning. Some survive, and negative parallelism survives where the distinction
between the two statements is itself the point.

**3. Openers.** Quote the first sentence under every heading. Flag each one that
opens with a caveat, a correction, or a limitation instead of the section's
subject.

**4. The three prohibitions.** Confirm the draft changed no number, confidence
interval, p-value, arXiv identifier, or quoted sentence against the file it
replaces. Confirm no correction was deleted that a register in `pyproject.toml`
depends on. Confirm no hedge carrying epistemic status was flattened. Diff
against the previous version and say you did.

**5. Gate hazards.** Prose edits break gates here in ways that are easy to miss.
Check and report:

- **Reflowed text near a citation.** The citation gate binds a number to a quote
  by markdown block, so rewrapping alone can move a figure into a block whose
  identifier has no quote behind it.
- **A number restated from another file.** `site/claims.json` binds published
  figures to verbatim sentences in their source file. Quote any sentence the
  draft changed that a claim depends on.
- **A link or backticked path that resolves only on this machine.**
- **An unterminated code fence**, which re-pools every block in the document.

## Output

A table of findings with line numbers, ordered worst first, then one paragraph
saying whether the draft meets the standard. If it does, say which specific
things it does well, so the next writer can copy them.

A review that says "looks good" has not run.
