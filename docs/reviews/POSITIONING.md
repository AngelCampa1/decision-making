# Review brief: positioning

**Audience:** an agent reviewing a draft. This is a prompt, so read it as your
instructions.

This repository already has an adversarial review whose job is to break a claim.
This one is its opposite and it exists because breaking claims was the only
review ever run here, which produced documents that answer objections nobody
raised.

Your job is to find where the writing **undersells work that was actually
done**. You are not checking whether the claims are true. A separate review does
that, and it outranks you: if you and it disagree, it wins.

## What to report

Read the draft, then answer all six.

1. **Where does this apologise?** Quote every sentence that concedes, hedges,
   confesses, or pre-empts an objection. For each one, say whether the reader
   had raised that objection yet at that point in the document.

2. **What did the author earn and fail to claim?** This is the important
   question. Find work that is genuinely hard, genuinely uncommon, or genuinely
   the right call, and that the draft mentions in passing or buries. Quote the
   passage and write the sentence that should have been there.

3. **Where does a negative frame carry a positive fact?** A limitation the
   author's own instrument discovered is a finding. A refusal the author built
   into their own gate is a capability. Quote every one written as a shortfall
   and rewrite it as the achievement it describes.

4. **What is the first impression?** Quote the first two sentences a reader
   meets. Say what they make the author look like.

5. **What is missing that a reader would want?** Name anything a competent
   stranger would expect and not find.

6. **The verdict.** Does someone who reads this finish it thinking the author is
   good at their job? Answer yes or no, then give the single change that would
   most improve the answer.

## Rules

- **Never suggest a claim the evidence does not support.** Commit `8af6f38` here
  is titled *"The keyword pass had written four claims the code does not
  support"*. That is the failure this brief could cause. Every rewrite you
  propose must be checkable against the repository, and you say where.
- **Never propose flattening a hedge that carries epistemic status.** "We have
  not shown this works" and "this does not work" are different claims. You may
  move a hedge, state it once instead of four times, or reframe it. You may not
  delete its meaning.
- **Never touch a number, a confidence interval, a p-value, an arXiv identifier,
  or a quoted sentence.**
- Quote line numbers. A review that describes a problem without pointing at it
  cannot be acted on.

A review that says "looks good" has not run. If you genuinely find nothing under
question 2, say so explicitly and name what you looked for.
