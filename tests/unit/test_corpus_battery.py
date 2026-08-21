"""Tests for the shortcut battery, and for the guard over the battery itself.

The battery says "no trivial feature solves this corpus". Until 2026-08-13 two
of its eight features could not have said anything else: ``imperative_opener``
reads the first word of the whole turn, the whole turn opens with the body a
triple shares, and the value moved in one triple out of forty. It passed every
run and it was structurally incapable of failing one. That is the fourth
instance in this repository of an estimator that cannot return a non-zero value
and does not announce itself.

So these tests are in two halves, and neither is optional:

* the **known-good** corpus, which the guard must pass before it is allowed to
  fail anything (standing rule 2 --- two falsifiers here were wrong on the day
  they were written); and
* the **planted leaks**, because a gate nobody has watched fire is in exactly
  the category it exists to catch.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from decision_evals.corpus import (
    CORPUS_BASELINE_PATH,
    FEATURES,
    MIN_LEAKS_PER_VIEW,
    VIEWS,
    Finding,
    apply_corpus_baseline,
    attainable_auc,
    battery_report,
    check_corpus,
    load_corpus_baseline,
    majority_baseline,
    null_leak_rate,
    separability,
    stump_accuracy,
)
from decision_evals.triggers import (
    TriggerCase,
    TriggerSet,
    _scan,
    check_trigger_sets,
    deferred_corpus_findings,
    load_trigger_set,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "datasets" / "triggers" / "decision-making" / "index.yaml"


def _messages(findings: list[Finding]) -> list[str]:
    """What a reader sees, for the tests that do not care about the key."""
    return [finding.message for finding in findings]


# --------------------------------------------------------------------------- #
# The known-good corpus.
#
# Three turns, one of each shape a real triple carries, and **the same three
# turns in every triple**. Which of them is the positive rotates, so each shape
# is the positive in exactly a third of the triples.
#
# That construction is what makes it known-good rather than hoped-good. Every
# feature's positives are then an equal mix of the three shapes and so are its
# negatives, and concordance is antisymmetric, so every feature scores exactly
# 0.500 in every view -- not approximately, and not because the turns were
# tuned until it did. A corpus whose labels cannot correlate with anything is
# precisely the case a shortcut gate must not fail.
#
# The three shapes are also chosen so that every feature takes more than one
# value across them, which is what makes each feature *live*: it moves inside
# every triple, so labels exist that would have pushed it out of band.
# ``generates`` carries an extra short sentence so ``sentence_count`` (2, 2, 3)
# is one of the features that moves -- added 2026-08-14 alongside the fix to
# ``_shared_body``, since a feature added to the battery is untested by this
# fixture until it can move here too.
# --------------------------------------------------------------------------- #
DECIDES = "Should I take the offer or stay put? I keep going round in circles and cannot decide."
LOOKS_UP = "Here's the thread. What does the notice period clause mean, rather than what I ought?"
GENERATES = (
    "Draft the reply to my landlord about the April move. Warm but short, and fairly brief."
    " Nothing fancy."
)

SHAPES = (("decides", DECIDES), ("looks_up", LOOKS_UP), ("generates", GENERATES))


def _rotating_corpus(turns: dict[str, str] | None = None, triples: int = 6) -> TriggerSet:
    """``triples`` triples of the same three turns, positive role rotating."""
    text = dict(SHAPES) | (turns or {})
    cases: list[TriggerCase] = []
    for index in range(triples):
        for offset, (shape, _) in enumerate(SHAPES):
            fires = offset == index % len(SHAPES)
            cases.append(
                TriggerCase(
                    id=f"t{index}{shape}",
                    turn=text[shape],
                    should_fire=fires,
                    why="fixture",
                    routes=("ledger",) if fires else (),
                    band="s",
                    triple=f"t{index}",
                    domain="money",
                    stakes="low",
                    ask="explicit",
                    kind=None if fires else "lookup",
                )
            )
    return TriggerSet(skill="decision-making", cases=tuple(cases), version=3)


class TestTheGuardPassesACorpusItShouldPass:
    """Standing rule 2. The falsifier is run against a known-good case first."""

    def test_the_known_good_corpus_raises_nothing(self) -> None:
        assert check_corpus(_rotating_corpus(), Path("known-good.yaml")) == []

    def test_every_feature_scores_exactly_chance_in_every_view(self) -> None:
        """Not "close to" chance. The rotation makes it an identity."""
        corpus = _rotating_corpus()
        for view in VIEWS.values():
            texts = view(corpus)
            for name, feature in FEATURES.items():
                assert separability(corpus, feature, texts) == pytest.approx(0.5), name

    def test_every_feature_could_nonetheless_have_failed(self) -> None:
        """Chance because of the labels, not because the feature cannot move.

        A corpus that passed by pinning every feature would be the defect these
        tests exist for, wearing a green tick.
        """
        for check in battery_report(_rotating_corpus()):
            if check.view == "turn":
                assert not check.inert, check.feature

    def test_no_feature_is_inert_in_all_three_views(self) -> None:
        report = battery_report(_rotating_corpus())
        for name in FEATURES:
            family = [check for check in report if check.feature == name]
            assert not all(check.inert for check in family), name

    def test_the_stump_buys_nothing_over_the_majority_class(self) -> None:
        corpus = _rotating_corpus()
        assert stump_accuracy(corpus) == pytest.approx(majority_baseline(corpus))


class TestThePlantedLeaksAreCaught:
    """And symmetrically: a gate nobody has seen fire has not been shown to work."""

    #: Three shapes with exactly one ``?`` each, sitting mid-turn.
    MID_QUESTION: ClassVar[dict[str, str]] = {
        "decides": "Should I take the offer or stay put? I keep going round in circles.",
        "looks_up": "Here's the thread I was sent. What does the notice period clause mean?"
        " Just the rules.",
        "generates": "Draft the reply to my landlord. Which April date should it name?"
        " Warm but short.",
    }

    #: The same sentences in a different order, so the ``?`` lands last.
    #:
    #: Same words, same characters, same one question mark. **The only thing
    #: that differs between a positive and a negative in this fixture is where
    #: the question mark sits**, which is why it isolates the leak: every other
    #: feature in the battery is a bag-of-words quantity and cannot see it.
    TAIL_QUESTION: ClassVar[dict[str, str]] = {
        "decides": "I keep going round in circles. Should I take the offer or stay put?",
        "looks_up": "Here's the thread I was sent. Just the rules."
        " What does the notice period clause mean?",
        "generates": "Draft the reply to my landlord. Warm but short."
        " Which April date should it name?",
    }

    def _planted(self) -> TriggerSet:
        """Positives end in ``?``; negatives put the same ``?`` mid-turn."""
        negatives = _rotating_corpus(self.MID_QUESTION)
        positives = {case.id: case for case in _rotating_corpus(self.TAIL_QUESTION).cases}
        return TriggerSet(
            skill=negatives.skill,
            version=3,
            cases=tuple(
                positives[case.id] if case.should_fire else case for case in negatives.cases
            ),
        )

    def test_the_old_battery_was_blind_to_it(self) -> None:
        """``question_marks`` counts them; every turn here has exactly one."""
        planted = self._planted()
        assert {FEATURES["question_marks"](case.turn) for case in planted.cases} == {1.0}
        assert separability(planted, FEATURES["question_marks"]) == pytest.approx(0.5)

    def test_terminal_position_catches_it(self) -> None:
        planted = self._planted()
        assert separability(planted, FEATURES["terminal_question"]) == pytest.approx(1.0)

    def test_and_it_is_the_only_feature_that_sees_it(self) -> None:
        """Reordering sentences leaves every bag-of-words feature untouched."""
        planted = self._planted()
        blind = {
            name: separability(planted, feature)
            for name, feature in FEATURES.items()
            if name != "terminal_question"
        }
        assert blind == {name: pytest.approx(0.5) for name in blind}

    def test_the_gate_reports_it_and_names_the_feature(self) -> None:
        issues = _messages(check_corpus(self._planted(), Path("planted.yaml")))
        assert any("terminal_question" in issue and "AUC 1.000" in issue for issue in issues)

    #: Two sentences that close a turn, and which of them comes last is the
    #: only thing separating a positive from a negative.
    PLEA = "I do not know what I ought to do."
    ORDER = "List the options and the dates."

    def _closing_leak(self) -> TriggerSet:
        """Every turn is the same bag of words; only the order differs.

        Which makes the whole-turn battery **provably** blind: word counts,
        character counts, rates and ratios are all order-free, so every one of
        them is identical on a positive and on a negative and scores exactly
        0.500. The label lives entirely in which sentence lands last, and the
        only way to see it is to look there.

        The shipped corpus's situation in miniature, where up to 5,118 of 5,776
        characters are shared and the ask is the remainder.

        **Reversing a two-sentence tail leaks at both ends, not one.** A
        constant third sentence in front of the swapped pair looks like a fix
        for an open-view leak, but it is not one: :func:`_shared_body` finds
        the raw byte-identical prefix, so a sentence that never varies is
        *body* by that definition and is stripped along with the rest,
        leaving the ask exactly as it was. There is no way to plant a leak
        that swaps which sentence is last without also swapping which is
        first when the tail has only two sentences -- ``close`` and ``open``
        are opposite ends of the same swap, and both are meant to catch it.
        """
        body = "Some background that says nothing, repeated. "
        cases: list[TriggerCase] = []
        for index in range(6):
            for offset, shape in enumerate(("a", "b", "c")):
                fires = offset == index % 3
                tail = (self.ORDER, self.PLEA) if fires else (self.PLEA, self.ORDER)
                cases.append(
                    TriggerCase(
                        id=f"c{index}{shape}",
                        turn=body * (50 + index) + " ".join(tail),
                        should_fire=fires,
                        why="fixture",
                        band="l",
                        triple=f"c{index}",
                        domain="money",
                        stakes="low",
                        ask="explicit",
                        kind=None if fires else "lookup",
                    )
                )
        return TriggerSet(skill="decision-making", cases=tuple(cases), version=3)

    def test_a_leak_only_in_the_closing_sentence_is_reported(self) -> None:
        leaky = self._closing_leak()
        turn = [check for check in battery_report(leaky) if check.view == "turn"]
        assert all(check.auc == pytest.approx(0.5) for check in turn), [
            (check.feature, check.auc) for check in turn if check.leaks
        ]
        issues = _messages(check_corpus(leaky, Path("closing.yaml")))
        assert any("on the 'close' view" in issue for issue in issues)
        assert not any("alone separates the labels" in issue for issue in issues)
        # And the fixture is structurally sound, so what it reports is the leak
        # rather than a band it has drifted out of.
        assert not any("outside 200-400" in issue or "wider than" in issue for issue in issues)

    def test_the_closing_imperative_is_what_sees_it(self) -> None:
        """``imperative_opener`` reads the first word of whatever it is given.

        On the whole turn that is the body, which is why it has been pinned at
        chance on the shipped corpus since it was written. On the closing
        sentence it is the word that decides the label.
        """
        leaky = self._closing_leak()
        closes = VIEWS["close"](leaky)
        assert separability(leaky, FEATURES["imperative_opener"]) == pytest.approx(0.5)
        assert separability(leaky, FEATURES["imperative_opener"], closes) == pytest.approx(0.0)


class TestTheInertFeatureGuard:
    """A feature no label could have moved is not a passing check."""

    def test_a_feature_with_no_variance_anywhere_is_inert(self) -> None:
        corpus = _rotating_corpus()
        low, high = attainable_auc(corpus, lambda _: 1.0)
        assert (low, high) == (0.5, 0.5)

    def test_a_feature_constant_within_every_triple_is_pinned_at_chance(self) -> None:
        """Varying across triples buys nothing: every triple has the same shape.

        One positive and two negatives in each, so a triple's contribution to
        every other triple's is matched by the reverse pair. The interval is a
        point, and the point is 0.500.
        """
        corpus = _rotating_corpus()
        per_triple = {case.id: float(int(case.triple[1:])) for case in corpus.cases}
        assert attainable_auc(corpus, float, per_triple) == (0.5, 0.5)

    def test_a_set_without_triples_constrains_nothing(self) -> None:
        corpus = _rotating_corpus()
        loose = TriggerSet(
            skill=corpus.skill,
            version=3,
            cases=tuple(
                TriggerCase(
                    id=case.id,
                    turn=case.turn,
                    should_fire=case.should_fire,
                    why=case.why,
                    band=case.band,
                )
                for case in corpus.cases
            ),
        )
        assert attainable_auc(loose, FEATURES["word_count"]) == (0.0, 1.0)

    def test_an_empty_set_is_chance_rather_than_a_crash(self) -> None:
        empty = TriggerSet(skill="decision-making", cases=(), version=3)
        assert attainable_auc(empty, FEATURES["word_count"]) == (0.5, 0.5)

    def test_the_gate_names_the_dead_feature_and_every_view(self) -> None:
        """A corpus in which one feature is matched away everywhere."""
        corpus = _rotating_corpus({"looks_up": LOOKS_UP.replace("Here's the thread.", "So then.")})
        issues = _messages(check_corpus(corpus, Path("pinned.yaml")))
        assert any(
            "'paste_cues' is inert in every view" in issue
            and "turn could only reach" in issue
            and "close could only reach" in issue
            for issue in issues
        )

    def test_a_feature_live_in_only_one_view_is_not_reported(self) -> None:
        """Matching a feature inside triples is how the design removes it.

        Pinning is a success on the whole turn and a failure only when it holds
        in every view at once, which is why the fix for ``imperative_opener``
        was a view it can move in rather than a corpus change.
        """
        report = battery_report(load_trigger_set(CORPUS))
        by_view = {check.view: check for check in report if check.feature == "imperative_opener"}
        assert by_view["turn"].inert
        assert not by_view["close"].inert
        assert not any(
            "'imperative_opener' is inert" in issue
            for issue in _messages(check_corpus(load_trigger_set(CORPUS), CORPUS))
        )


class TestThePerBandBreakdownIsReported:
    def test_every_check_carries_its_bands(self) -> None:
        report = battery_report(load_trigger_set(CORPUS))
        assert {band for check in report for band in check.per_band} == {"s", "m", "l", "xl"}

    def test_a_failure_prints_the_bands_that_produced_it(self) -> None:
        """A pooled number that hides two rulers pointing opposite ways is how
        the XL band was missed the first time.

        ``xl 0.309`` is ``sentence_count``'s current ``cancel:`` finding
        (dispersion rather than mean-shift) -- see ``corpus-baseline.txt``.
        Re-pinned 2026-08-14 from ``0.235``: the opener-leak fix
        (``notebook/2026-08-14-the-opener-leak-closed-by-touching-both-
        sides.md``) prepended a short lead-in sentence to several `xl`
        positives so their ask no longer opened with a bare question, which
        also raised their sentence count. The reporting mechanism (one
        ``band value`` pair per band, comma-separated) is unchanged; only the
        number moved, which is what a corpus edit is supposed to do. Re-pin
        again if the corpus moves further.

        Re-pinned 2026-08-20 from ``0.309`` to ``0.293``: version 5 added three
        `xl` triples for `council` and three for `hinge`, so the band went from
        seventeen triples to twenty-three and its dispersion rate moved with the
        denominator. Same reporting mechanism, same check, a different corpus
        underneath it.
        """
        issues = _messages(check_corpus(load_trigger_set(CORPUS), CORPUS))
        assert any("xl 0.293" in issue for issue in issues)

    def test_a_band_with_no_cases_is_left_out_rather_than_reported_as_chance(self) -> None:
        assert {
            band for check in battery_report(_rotating_corpus()) for band in check.per_band
        } == {"s"}


class TestTheThresholdIsDerivedRatherThanChosen:
    """``MIN_LEAKS_PER_VIEW`` has to be re-derivable, not remembered.

    The permutation null is the one the matched design implies: hold every turn
    where it is and re-draw which member of each triple is the positive. Under
    it the corpus carries nothing, so the failure rate *is* the gate's rate of
    failing a clean corpus.
    """

    DRAWS = 4_000

    def test_the_derived_views_fail_a_clean_corpus_no_more_often_than_the_gated_one(
        self,
    ) -> None:
        corpus = load_trigger_set(CORPUS)
        gated = null_leak_rate(corpus, "turn", leaks=1, draws=self.DRAWS)
        for view in VIEWS:
            if view == "turn":
                continue
            rate = null_leak_rate(corpus, view, leaks=MIN_LEAKS_PER_VIEW, draws=self.DRAWS)
            assert rate <= gated, f"{view} fails a signal-free corpus at {rate:.4f} > {gated:.4f}"

    def test_gating_the_derived_views_per_feature_would_have_been_far_worse(self) -> None:
        """The measurement that rejected the obvious design.

        The absolute rate this asserted against (0.10, "one run in five" on the
        two derived views combined) was measured at 40 triples and is stale --
        the corpus has since grown to 64 and then 87, and a larger corpus has a
        tighter null, so every rate in this class has fallen with it. What has
        not changed is the *shape* of the argument ``MIN_LEAKS_PER_VIEW`` rests
        on: gating one feature at a time on a derived view still fails a clean
        corpus far more often than the count gate that shipped. 48x at today's
        size (0.012 against 0.00025) is that argument holding at a different
        corpus size, not a new one. ``MIN_LEAKS_PER_VIEW`` and this module's own
        docstring table are due a full re-derivation once the in-progress
        long-band merge settles the corpus at a fixed size -- re-deriving them
        against a still-moving target would just be measuring the move.
        """
        corpus = load_trigger_set(CORPUS)
        single = null_leak_rate(corpus, "close", leaks=1, draws=self.DRAWS)
        counted = null_leak_rate(corpus, "close", leaks=MIN_LEAKS_PER_VIEW, draws=self.DRAWS)
        assert single > counted * 10

    def test_a_design_the_null_does_not_fit_returns_zero_rather_than_a_number(self) -> None:
        """No triples means no null to draw from, and a made-up rate is worse
        than an obvious one."""
        corpus = _rotating_corpus()
        loose = TriggerSet(
            skill=corpus.skill,
            version=3,
            cases=tuple(
                TriggerCase(id=case.id, turn=case.turn, should_fire=case.should_fire, why=case.why)
                for case in corpus.cases
            ),
        )
        assert null_leak_rate(loose, "turn", draws=64) == 0.0

    def test_a_lopsided_triple_returns_zero_rather_than_a_number(self) -> None:
        corpus = _rotating_corpus()
        lopsided = TriggerSet(
            skill=corpus.skill,
            version=3,
            cases=tuple(corpus.cases[:-1]),
        )
        assert null_leak_rate(lopsided, "turn", draws=64) == 0.0

    def test_the_gated_view_is_where_the_derivation_says_it_is(self) -> None:
        """The per-feature gate's own false-failure rate, recomputed.

        The band this asserted (0.01-0.06, "about three times in a hundred")
        was measured at 40 triples. The corpus has since grown to 64 and then
        87 -- more triples means a tighter null, so the rate has fallen with
        every merge (0.0094 at 64 per the entry ``MATCHED_Z`` cites; 0.00175
        today). The mechanism ``null_leak_rate`` exists to check is unchanged
        and this pins the *current* measurement rather than a stale one; see
        ``test_gating_the_derived_views_per_feature_would_have_been_far_worse``
        for why a full re-derivation of ``MIN_LEAKS_PER_VIEW`` waits for the
        corpus size to stop moving.

        Re-pinned 2026-08-20 at 110 triples, and the lower bound is gone rather
        than lowered. Version 5's twenty-four `council`/`hinge` triples take the
        rate to **0.0**: not one draw in 8,000 produced a leak, checked at 2,000
        and at 8,000. A floor of 0.0005 asks for one failure in two thousand
        draws and the null no longer delivers one, so asserting it would be
        asserting that the gate is *less* conservative than it now is. The
        ceiling is what the test was for and it stays.
        """
        rate = null_leak_rate(load_trigger_set(CORPUS), "turn", leaks=1, draws=self.DRAWS)
        assert rate <= 0.01


class TestTheBaselineIsNarrowRatherThanBlanket:
    """Standing rule 2, applied to the baseline instead of to the gate.

    A baseline is a falsifier with the sign flipped: it decides what *stops*
    failing. So the thing to demonstrate is not that it defers the two known
    findings --- that is what it was written to do --- but that a **third**
    finding still turns the build red. Otherwise the honest description of it
    is "the shortcut battery is switched off", and nobody would have known.
    """

    @staticmethod
    def _apply(corpus: TriggerSet, baseline: set[str]) -> tuple[list[str], list[str]]:
        findings = [("x.yaml", finding) for finding in check_corpus(corpus, Path("x.yaml"))]
        return apply_corpus_baseline(findings, baseline)

    def _leaky(self) -> TriggerSet:
        return TestThePlantedLeaksAreCaught()._closing_leak()

    #: The exact close-view finding the fixture produces.
    KEY: ClassVar[str] = (
        "x.yaml|leak:close:char_count,first_person_rate,imperative_opener,"
        "type_token_ratio,word_count"
    )

    #: The symmetric open-view finding -- see ``_closing_leak``'s docstring:
    #: reversing a two-sentence tail leaks at both ends, not one, because a
    #: sentence that never varies is *body* by ``_shared_body``'s own
    #: definition and cannot be planted in front of the swap to shield ``open``.
    OPEN_KEY: ClassVar[str] = (
        "x.yaml|leak:open:char_count,first_person_rate,imperative_opener,"
        "type_token_ratio,word_count"
    )

    def _baseline(self) -> set[str]:
        """Every finding this fixture currently produces, keyed.

        The whole set rather than a hand-picked subset. The battery gained a
        dozen ``matched:``/``cancel:`` checks after this fixture was written,
        and this fixture -- an order-swap over two sentences -- trips several
        of them (the swap is, after all, a rank the positive holds inside its
        own triple). A test about baseline *narrowness* should baseline
        everything a corpus currently produces and show that anything *beyond*
        that still fails, not quietly under-baseline and call the gap narrow.
        """
        return {
            f"x.yaml|{finding.key}"
            for finding in check_corpus(self._leaky(), Path("x.yaml"))
            if finding.key
        }

    def test_the_baselined_findings_stop_failing_and_are_still_reported(self) -> None:
        issues, deferred = self._apply(self._leaky(), self._baseline())
        assert issues == []
        assert any("on the 'close' view" in message for message in deferred)

    def test_a_fifth_feature_joining_the_leak_fails(self) -> None:
        """The requirement the key exists for: identity is the whole set."""
        leaky = self._leaky()
        widened = TriggerSet(
            skill=leaky.skill,
            version=3,
            cases=tuple(
                TriggerCase(
                    id=case.id,
                    # `says_should_i` joins the closing set, and nothing else moves.
                    turn=case.turn.replace(
                        TestThePlantedLeaksAreCaught.PLEA,
                        "Should I do it or not, because I do not know what I ought to do?",
                    ),
                    should_fire=case.should_fire,
                    why=case.why,
                    band=case.band,
                    triple=case.triple,
                    domain=case.domain,
                    stakes=case.stakes,
                    ask=case.ask,
                    kind=case.kind,
                )
                for case in leaky.cases
            ),
        )
        issues, _ = self._apply(widened, self._baseline())
        assert any("features separate the labels on the 'close' view" in i for i in issues)

    def test_the_same_leak_on_another_view_fails(self) -> None:
        """A key names its view, so the leak cannot migrate under the baseline."""
        moved = {self.KEY.replace("leak:close:", "leak:ask:")}
        issues, _ = self._apply(self._leaky(), moved | self._baseline() - {self.KEY})
        assert any("on the 'close' view" in issue for issue in issues)

    def test_a_new_inert_feature_fails(self) -> None:
        issues, _ = self._apply(self._leaky(), {self.KEY})
        assert any("is inert in every view" in issue for issue in issues)

    def test_a_baseline_entry_that_no_longer_matches_fails(self) -> None:
        """May only shrink, enforced the way the other two baselines enforce it.

        Includes the case that matters most here: the corpus *improved*, four
        leaking features became three, and the key changed. That fails until
        somebody shrinks the line, which is the point --- an improvement the
        baseline cannot see is an improvement it has stopped measuring.
        """
        stale = self._baseline() | {"x.yaml|leak:close:char_count,word_count"}
        issues, _ = self._apply(self._leaky(), stale)
        assert any(
            "is baselined but matches no current finding" in issue and "Delete the line" in issue
            for issue in issues
        )

    def test_a_structural_defect_cannot_be_baselined_at_all(self) -> None:
        """There is no backlog to defer: a broken triple is fixable now."""
        corpus = _rotating_corpus()
        broken = TriggerSet(skill=corpus.skill, version=3, cases=corpus.cases[:-1])
        findings = check_corpus(broken, Path("x.yaml"))
        structural = [f for f in findings if "every triple is one positive" in f.message]
        assert structural
        assert all(finding.key == "" for finding in structural)
        issues, _ = self._apply(broken, {f"x.yaml|{f.key}" for f in findings})
        assert any("every triple is one positive" in issue for issue in issues)


class TestTheShippedBaseline:
    """The real file against the real corpus, and a third leak against both."""

    def test_it_defers_exactly_the_known_findings_and_nothing_else(self) -> None:
        """Five, as of the 2026-08-19 router-table gap -- see ``corpus-baseline.txt``.

        Was three from the 2026-08-14 opener-leak fix until the shipped router
        grew ``council`` and ``hinge`` without the answer key growing with it,
        which opened one ``unreachable:`` finding on each of the two corpora.
        Those two are not shortcut leaks and close differently: by authoring
        positives and versioning the key, or by dropping the two rows.

        Was five right after the 2026-08-14 long-band merge: two `word_count`
        findings had just closed and three opened, including `open`'s
        ``question_marks``/``terminal_question`` pair (the newline-cut fix had
        un-pinned it). Two of those five close here: the opener-leak fix
        (``notebook/2026-08-14-the-opener-leak-closed-by-touching-both-
        sides.md``) balances the rate at which positives and negatives open
        their ask with a question in `l`/`xl`, and ``question_marks``/
        ``terminal_question`` on `open` stop reproducing. `sentence_count`
        (both views, `cancel:` dispersion) and `type_token_ratio` (`ask`,
        `matched:`) are unrelated to the opener and still open. The corpus is
        still being worked on as this file is edited, so re-pin this count
        against whatever `corpus-baseline.txt` names once that settles.

        Still five on 2026-08-20, and the membership moved twice rather than
        once. Version 5 authored `council` and `hinge` positives for the banded
        corpus, which closed one of the two ``unreachable:`` entries -- the
        `decision-making.yaml` one stays, because that corpus is superseded and
        was not fixed. The same commit put ``cancel:close:type_token_ratio``
        over the gate, not by changing the rate (0.9186 before, 0.9182 after)
        but by adding twenty-four triples to a proportion whose z scales with
        the square root of `n`.

        Four on 2026-08-21. Blind adjudication of the seventy-two items version
        5 added disputed three labels, and rewriting those three closing asks
        took ``matched:ask:type_token_ratio`` from 3.03 to 2.91 null standard
        errors, under the gate. Three asks out of 330 items moved it, so the
        entry comes off the baseline and `corpus-baseline.txt` says in writing
        that a corpus edit turning a gate green is the shape of the leak this
        repository keeps finding. What earns it here is that the agents who
        wrote those asks saw neither a judge's verdict nor that file.
        """
        assert check_trigger_sets(REPO_ROOT) == []
        deferred = deferred_corpus_findings(REPO_ROOT)
        # Four since 2026-08-21: three shortcut leaks and one `unreachable:`
        # gap, where it was four leaks and one gap.
        assert len(deferred) == 4
        unreachable = [
            message
            for message in deferred
            if "are the correct answer for no positive: council, hinge" in message
        ]
        assert len(unreachable) == 1
        # It names the corpus it is about. Counting alone was once satisfied by
        # two byte-identical strings, which is the defect a56cd8f fixed; now
        # that only one of the two corpora still carries the gap, naming it is
        # what stops this passing on a message about the other one.
        assert {message.split(":", 1)[0] for message in unreachable} == {
            "datasets/triggers/decision-making.yaml",
        }
        assert any(
            "'sentence_count' on the 'turn' view puts the positive at an extreme" in message
            for message in deferred
        )
        assert any(
            "'sentence_count' on the 'ask' view puts the positive at an extreme" in message
            for message in deferred
        )
        # Closed 2026-08-21 by the three rewritten asks; see the docstring.
        assert not any(
            "'type_token_ratio' on the 'ask' view sits below" in message for message in deferred
        )
        assert not any(
            "'question_marks' on the 'open' view sits above" in message for message in deferred
        )
        assert not any(
            "'terminal_question' on the 'open' view sits above" in message for message in deferred
        )

    def test_a_third_finding_on_the_real_corpus_still_fails(self) -> None:
        """Standing rule 2 against the shipped baseline rather than a fixture."""
        # Everything the gate really produces, not one corpus's battery: the
        # baseline also defers `unreachable:` findings, which come from the
        # scan rather than from `check_corpus`, and a partial view of the
        # findings would read those entries as stale.
        findings = _scan(REPO_ROOT)[1]
        baseline = load_corpus_baseline(REPO_ROOT)
        assert apply_corpus_baseline(findings, baseline)[0] == []

        planted = Finding("leak:turn:terminal_question", "a third finding nobody has seen")
        issues, _ = apply_corpus_baseline(
            [*findings, (CORPUS.relative_to(REPO_ROOT).as_posix(), planted)], baseline
        )
        assert issues == ["a third finding nobody has seen"]

    def test_every_line_in_the_file_is_load_bearing(self) -> None:
        """A baseline entry for a corpus that does not exist would never go stale."""
        baseline = load_corpus_baseline(REPO_ROOT)
        assert {entry.split("|", 1)[0] for entry in baseline} == {
            "datasets/triggers/decision-making.yaml",
            "datasets/triggers/decision-making/index.yaml",
        }

    def test_each_entry_carries_the_condition_that_closes_it(self) -> None:
        text = (REPO_ROOT / CORPUS_BASELINE_PATH).read_text(encoding="utf-8")
        assert text.count("CLOSED BY:") == len(load_corpus_baseline(REPO_ROOT))
        assert "MAY ONLY SHRINK" in text


class TestTheDerivedAsk:
    def test_the_shared_body_is_removed_where_a_triple_has_one(self) -> None:
        corpus = load_trigger_set(CORPUS)
        asks = VIEWS["ask"](corpus)
        xl = [case for case in corpus.cases if case.band == "xl"]
        assert max(len(asks[case.id]) for case in xl) < min(len(case.turn) for case in xl) / 4

    def test_a_triple_that_shares_no_body_keeps_its_whole_turn(self) -> None:
        """Measured, and it is most of the corpus: XL, some L triples, and a
        handful of short-band triples that happen to open the same way were
        authored from -- or coincide on -- one body. The rest of ``s``/``m``
        keeps its whole turn as the ask.

        126 rather than the full 144 ``s``/``m`` items: the short-band unit
        added 2026-08-13 introduced six triples (``s09``, ``s21``, ``m04``,
        ``m15``, ``m20``, ``m23``) whose members happen to share an opening
        word or two, which the body-detection logic in :func:`_shared_body`
        cannot distinguish from an authored shared body -- and should not try
        to, since a real coincidence is exactly as much of a leak risk as a
        deliberate one.

        Re-pinned 2026-08-20: 141 of the full 180 ``s``/``m`` items. Version 5
        added twelve short-band triples and seven of them detect a shared body
        (``s26``, ``s27``, ``s28``, ``s29``, ``m26``, ``m29``, ``m30``), which
        is the construction working rather than a coincidence -- in those the
        first negative was authored to repeat the positive's opening sentence
        verbatim, so there is a real body to strip. The other five diverge in
        the first clause and keep the whole turn.
        """
        corpus = load_trigger_set(CORPUS)
        asks = VIEWS["ask"](corpus)
        untouched = [case for case in corpus.cases if asks[case.id] == case.turn]
        assert len([case for case in untouched if case.band in {"s", "m"}]) == 141
        assert len([case for case in untouched if case.band == "xl"]) == 0

    def test_the_body_is_cut_at_a_word_boundary(self) -> None:
        """A prefix ending mid-word makes every feature measure the cut."""
        corpus = _rotating_corpus(
            {
                "decides": "Should I take the offer today?",
                "looks_up": "Should I take the number instead, or the other one entirely?",
                "generates": "Should I take the note down, please, and keep it fairly short?",
            }
        )
        asks = VIEWS["ask"](corpus)
        assert asks["t0decides"] == "offer today?"

    def test_the_body_is_cut_at_a_newline_rather_than_one_word_short_of_it(self) -> None:
        """Bug 1: a shared word before the newline used to leak into every ask.

        Every authored body ends with a newline before the ask, and that
        newline -- along with the word before it -- is part of the raw
        byte-identical prefix, so the character scan walks straight through
        it. Cutting back to the last *space* then throws the newline away
        because a newline is not a space, and the cut lands one word short:
        the word before the newline (here ``"today."``, in the shipped XL
        band ``"believed."``) leaked into every derived ask as its opening
        word, which is why opener features read exactly 0.500 on every
        triple with a real shared body.
        """
        corpus = _rotating_corpus(
            {
                "decides": "Some background here today.\nShould I take the offer or stay put?",
                "looks_up": "Some background here today.\nWhat does the notice period mean?",
                "generates": "Some background here today.\nDraft a short warm reply, please.",
            }
        )
        asks = VIEWS["ask"](corpus)
        assert asks["t0decides"] == "Should I take the offer or stay put?"
        assert asks["t0looks_up"] == "What does the notice period mean?"
        assert asks["t0generates"] == "Draft a short warm reply, please."
        assert not any(ask.startswith("today.") for ask in asks.values())

    def test_a_triple_sharing_no_whole_word_keeps_its_whole_turn(self) -> None:
        """A common prefix with no space in it is not a body, it is a coincidence."""
        corpus = _rotating_corpus(
            {"decides": "Shall I go?", "looks_up": "Shale prices?", "generates": "Shape it?"}
        )
        assert VIEWS["ask"](corpus)["t0decides"] == "Shall I go?"

    def test_a_set_with_one_label_only_is_chance_rather_than_a_crash(self) -> None:
        corpus = _rotating_corpus()
        one_sided = TriggerSet(
            skill=corpus.skill,
            version=3,
            cases=tuple(case for case in corpus.cases if case.should_fire),
        )
        assert separability(one_sided, FEATURES["word_count"]) == 0.5

    def test_the_closing_sentence_is_the_view_that_needs_no_triple(self) -> None:
        closes = VIEWS["close"](_rotating_corpus())
        assert closes["t0generates"] == "Nothing fancy."
