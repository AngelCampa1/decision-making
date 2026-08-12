"""The vendored corpus and the refusals that keep it honest.

No test here touches the network. The download is a thin seam in the CLI; what
matters and what is tested is that a corpus which is *not the pinned one* cannot
be loaded silently.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals.corpora import (
    CORPUS_PATH,
    LOCK_PATH,
    TASKS,
    UNIX_ONLY_TASKS,
    CorpusError,
    ShardedInstruction,
    VendorLock,
    load_corpus,
    load_lock,
    parse_corpus,
    sha256_of,
    shard_summary,
    verify,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_RECORDS = [
    {
        "task_id": "sharded-HumanEval/105",
        "task": "code",
        "shards": [
            {"shard_id": 1, "shard": "Turn digits into names in a list"},
            {"shard_id": 2, "shard": "Starting with a list of numbers"},
        ],
        "metadata": {"func_name": "by_length"},
    },
    {
        "task_id": "sharded-math-7",
        "task": "math",
        "shards": [
            {"shard_id": 1, "shard": "A train leaves at noon"},
            {"shard_id": 2, "shard": "It travels at 60mph"},
            {"shard_id": 3, "shard": "How far by 3pm?"},
        ],
        "answer": "180",
    },
]


def _write_lock(root: Path, **overrides: object) -> VendorLock:
    payload = {
        "repo": "microsoft/lost_in_conversation",
        "commit": "c865793fe34a929d316119b0451d01bd9183bcfd",
        "member": "data/sharded_instructions_600.json",
        "size_bytes": 10,
        "sha256": "0" * 64,
        "code_license": "MIT",
        "data_license": "CDLA-Permissive-2.0",
        "retrieved": "2026-08-11",
    }
    payload.update(overrides)
    (root / "datasets" / "vendor").mkdir(parents=True, exist_ok=True)
    (root / LOCK_PATH).write_text(json.dumps(payload), encoding="utf-8")
    return load_lock(root)


class TestLock:
    def test_the_committed_lock_parses(self) -> None:
        lock = load_lock(REPO_ROOT)
        assert lock.repo == "microsoft/lost_in_conversation"
        assert len(lock.commit) == 40
        assert len(lock.sha256) == 64

    def test_the_url_pins_the_commit_not_main(self) -> None:
        """A URL on ``main`` would silently re-point when upstream moves."""
        lock = load_lock(REPO_ROOT)
        assert lock.commit in lock.url
        assert "/main/" not in lock.url

    def test_a_missing_lock_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(CorpusError, match="nothing to verify the corpus against"):
            load_lock(tmp_path)


class TestVerify:
    def test_a_matching_file_passes(self, tmp_path: Path) -> None:
        target = tmp_path / "payload.json"
        target.write_bytes(b"0123456789")
        lock = _write_lock(tmp_path, size_bytes=10, sha256=sha256_of(target))
        verify(target, lock)

    def test_a_missing_file_names_the_fetch_command(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path)
        with pytest.raises(CorpusError, match="de fetch"):
            verify(tmp_path / "absent.json", lock)

    def test_the_wrong_size_is_reported_as_size_not_hash(self, tmp_path: Path) -> None:
        """A truncated download is the common case and deserves the clearer error."""
        target = tmp_path / "payload.json"
        target.write_bytes(b"short")
        lock = _write_lock(tmp_path, size_bytes=10)
        with pytest.raises(CorpusError, match="is 5 bytes, expected 10"):
            verify(target, lock)

    def test_the_right_size_and_wrong_hash_is_refused(self, tmp_path: Path) -> None:
        """The case that matters: same length, different content."""
        target = tmp_path / "payload.json"
        target.write_bytes(b"0123456789")
        lock = _write_lock(tmp_path, size_bytes=10, sha256="a" * 64)
        with pytest.raises(CorpusError, match="incomparable"):
            verify(target, lock)

    def test_the_refusal_says_not_to_re_pin_the_lock(self, tmp_path: Path) -> None:
        """The tempting wrong fix, named in the error so it is not taken."""
        target = tmp_path / "payload.json"
        target.write_bytes(b"0123456789")
        lock = _write_lock(tmp_path, size_bytes=10, sha256="a" * 64)
        with pytest.raises(CorpusError, match="find out what changed first"):
            verify(target, lock)

    def test_hashing_is_chunked_and_matches_a_one_shot_hash(self, tmp_path: Path) -> None:
        import hashlib

        target = tmp_path / "big.bin"
        blob = b"x" * (3 * (1 << 20) + 17)  # spans several 1 MiB chunks
        target.write_bytes(blob)
        assert sha256_of(target) == hashlib.sha256(blob).hexdigest()


class TestParse:
    def test_shard_objects_become_ordered_turn_text(self) -> None:
        parsed = parse_corpus(json.dumps(_RECORDS))
        assert parsed[0].shards == (
            "Turn digits into names in a list",
            "Starting with a list of numbers",
        )

    def test_bare_string_shards_are_accepted(self) -> None:
        parsed = parse_corpus(json.dumps([{"task_id": "x", "task": "math", "shards": ["a", "b"]}]))
        assert parsed[0].shards == ("a", "b")

    def test_family_specific_fields_survive_in_the_payload(self) -> None:
        """The schema is heterogeneous per family; flattening it would lose graders."""
        parsed = parse_corpus(json.dumps(_RECORDS))
        assert parsed[1].payload["answer"] == "180"
        assert parsed[0].payload["metadata"] == {"func_name": "by_length"}

    def test_the_identity_fields_are_not_duplicated_into_the_payload(self) -> None:
        parsed = parse_corpus(json.dumps(_RECORDS))
        assert not {"task_id", "task", "shards"} & set(parsed[0].payload)

    def test_n_turns_is_the_shard_count(self) -> None:
        parsed = parse_corpus(json.dumps(_RECORDS))
        assert [item.n_turns for item in parsed] == [2, 3]

    def test_a_non_list_top_level_is_refused(self) -> None:
        with pytest.raises(CorpusError, match="got dict"):
            parse_corpus(json.dumps({"task_id": "x"}))

    def test_a_non_object_record_is_refused(self) -> None:
        with pytest.raises(CorpusError, match="record 0 is str"):
            parse_corpus(json.dumps(["nope"]))

    @pytest.mark.parametrize("missing", ["task_id", "task", "shards"])
    def test_a_record_missing_a_required_field_is_refused(self, missing: str) -> None:
        record = {k: v for k, v in _RECORDS[1].items() if k != missing}
        with pytest.raises(CorpusError, match=f"missing {missing}"):
            parse_corpus(json.dumps([record]))

    def test_malformed_records_are_refused_rather_than_skipped(self) -> None:
        """Skipping would shrink the benchmark without saying so."""
        with pytest.raises(CorpusError):
            parse_corpus(json.dumps([_RECORDS[0], {"task": "math"}]))


class TestLoadCorpus:
    def _stage(self, root: Path, records: list[dict[str, object]]) -> None:
        (root / "datasets" / "vendor").mkdir(parents=True, exist_ok=True)
        target = root / CORPUS_PATH
        target.write_text(json.dumps(records), encoding="utf-8")
        _write_lock(root, size_bytes=target.stat().st_size, sha256=sha256_of(target))

    def test_it_loads_a_verified_corpus(self, tmp_path: Path) -> None:
        self._stage(tmp_path, _RECORDS)
        assert len(load_corpus(tmp_path)) == 2

    def test_nothing_is_excluded_by_default(self, tmp_path: Path) -> None:
        """A loader that silently drops a family is how an item count goes unexplained."""
        self._stage(tmp_path, _RECORDS)
        assert {item.task for item in load_corpus(tmp_path)} == {"code", "math"}

    def test_excluding_the_unix_only_family_drops_exactly_it(self, tmp_path: Path) -> None:
        self._stage(tmp_path, _RECORDS)
        loaded = load_corpus(tmp_path, exclude_tasks=UNIX_ONLY_TASKS)
        assert [item.task for item in loaded] == ["math"]

    def test_a_tampered_corpus_is_refused(self, tmp_path: Path) -> None:
        self._stage(tmp_path, _RECORDS)
        (tmp_path / CORPUS_PATH).write_text(json.dumps(_RECORDS[:1]), encoding="utf-8")
        with pytest.raises(CorpusError):
            load_corpus(tmp_path)

    def test_skipping_the_hash_check_still_requires_the_file(self, tmp_path: Path) -> None:
        _write_lock(tmp_path)
        with pytest.raises(CorpusError, match="de fetch"):
            load_corpus(tmp_path, check_hash=False)

    def test_skipping_the_hash_check_loads_a_tampered_corpus(self, tmp_path: Path) -> None:
        """Documents the hazard the flag carries, so the default is never changed."""
        self._stage(tmp_path, _RECORDS)
        (tmp_path / CORPUS_PATH).write_text(json.dumps(_RECORDS[:1]), encoding="utf-8")
        assert len(load_corpus(tmp_path, check_hash=False)) == 1


class TestShardSummary:
    def test_it_reports_the_distribution(self) -> None:
        parsed = parse_corpus(json.dumps(_RECORDS))
        summary = shard_summary(parsed)
        assert (summary.n_instructions, summary.min_turns, summary.max_turns) == (2, 2, 3)
        assert summary.mean_turns == pytest.approx(2.5)
        assert summary.tasks == ("code", "math")

    def test_median_of_an_even_count_is_interpolated(self) -> None:
        items = [ShardedInstruction("a", "math", ("x",) * n) for n in (2, 4, 6, 8)]
        assert shard_summary(items).median_turns == pytest.approx(5.0)

    def test_median_of_an_odd_count_is_the_middle_value(self) -> None:
        items = [ShardedInstruction("a", "math", ("x",) * n) for n in (2, 4, 9)]
        assert shard_summary(items).median_turns == pytest.approx(4.0)

    def test_an_empty_set_has_no_distribution(self) -> None:
        with pytest.raises(ValueError, match="no instructions"):
            shard_summary([])


def test_the_declared_families_match_what_the_lock_measured() -> None:
    """TASKS is prose in a constant; the lock is what was counted. Keep them equal."""
    measured = json.loads((REPO_ROOT / LOCK_PATH).read_text(encoding="utf-8"))
    assert tuple(measured["measured_on_retrieval"]["task_families_present"]) == TASKS


def test_the_excluded_family_is_one_we_declare() -> None:
    assert set(TASKS) >= UNIX_ONLY_TASKS
