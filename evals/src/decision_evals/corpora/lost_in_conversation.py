"""The published sharded corpus from arXiv:2505.06120.

**Why a vendored corpus instead of another authored one.** This repository has
built three corpora and discarded all three, and 21 of 21 scored failures across
them turned out to be the answer key rather than the model. Authoring is the
activity here with the worst track record. arXiv:2505.06120 released the
instrument its result was measured with, so Track A1 uses it and the authoring
step disappears.

**The corpus is not committed.** ``sharded_instructions_600.json`` is 28.9 MB,
which is more than belongs in a git history for a file that is byte-identical
upstream. Committed instead is :data:`LOCK_PATH`, a manifest pinning the
upstream commit, the byte count and the SHA-256. ``de fetch`` downloads the
payload and :func:`verify` refuses anything that does not match.

That refusal is the same rule the golden files enforce, for the same reason: a
benchmark that changes silently makes every earlier number incomparable with
every later one. Upstream is a live ``main`` branch, so pinning a commit is what
makes "we ran the published corpus" a checkable statement rather than a hope.

**Three things the file disagrees with, all measured 2026-08-11 rather than
assumed.** They are recorded here because each one would have become a wrong
number in a paper:

* It holds **627** records, not the 600 its filename claims.
* It holds **six** task families, not the seven the paper describes. The seventh,
  ``translation``, is a separate file (``data/sharded_translation.json``).
* Shard counts run **3 to 12**, mean 5.97, median 6 — see :func:`shard_summary`.
  The programme's "~6 turns" figure was flagged as invented and having no source.
  It turns out to be right, and it is now measured instead of guessed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

#: Upstream, pinned. ``main`` moves; this does not.
REPO: Final = "microsoft/lost_in_conversation"
COMMIT: Final = "c865793fe34a929d316119b0451d01bd9183bcfd"
CORPUS_MEMBER: Final = "data/sharded_instructions_600.json"

#: Code is MIT; the data release is CDLA-Permissive-2.0. Both permit
#: redistribution, which is why fetching rather than vendoring is a size
#: decision and not a licensing one.
CODE_LICENSE: Final = "MIT"
DATA_LICENSE: Final = "CDLA-Permissive-2.0"

LOCK_PATH: Final = "datasets/vendor/lost_in_conversation.lock.json"
CORPUS_PATH: Final = "datasets/vendor/sharded_instructions_600.json"

#: The six families actually present in the file. ``translation`` is the paper's
#: seventh and ships separately, so it is deliberately absent from this tuple.
TASKS: Final[tuple[str, ...]] = (
    "actions",
    "code",
    "data2text",
    "database",
    "math",
    "summary",
)

#: Excluded from Track A1. The ``code`` family is graded by executing test cases
#: under a Unix-only harness, so on this machine it would score as failure for a
#: reason that has nothing to do with multi-turn degradation. Not a default:
#: callers pass this explicitly, because a loader that silently drops a sixth of
#: the corpus is how an unexplained item count reaches a paper.
UNIX_ONLY_TASKS: Final[frozenset[str]] = frozenset({"code"})


class CorpusError(RuntimeError):
    """The vendored corpus is missing, or is not the one that was pinned."""


@dataclass(frozen=True, slots=True)
class VendorLock:
    """The pinned identity of a vendored file."""

    repo: str
    commit: str
    member: str
    size_bytes: int
    sha256: str
    code_license: str
    data_license: str
    retrieved: str

    @property
    def url(self) -> str:
        """The raw URL for exactly this commit, not for ``main``."""
        return f"https://raw.githubusercontent.com/{self.repo}/{self.commit}/{self.member}"


@dataclass(frozen=True, slots=True)
class ShardedInstruction:
    """One instruction, split into the turns it will be delivered over.

    Attributes:
        task_id: Upstream identifier, e.g. ``sharded-HumanEval/105``.
        task: Task family, one of :data:`TASKS`.
        shards: The turn texts in delivery order.
        payload: Every remaining upstream field, unmodified. The schema is
            heterogeneous by family — ``database`` carries ``reference_sql`` and
            ``schema_sql``, ``math`` carries ``answer``, ``summary`` carries
            ``documents`` — so it is kept whole rather than flattened into a
            union type that would need editing for each new grader.
    """

    task_id: str
    task: str
    shards: tuple[str, ...]
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def n_turns(self) -> int:
        """Turns this instruction is delivered over. One shard, one turn."""
        return len(self.shards)


def load_lock(repo_root: Path) -> VendorLock:
    """Read the committed manifest.

    Raises:
        CorpusError: The lock is absent. Without it there is nothing to verify
            against, and an unverified corpus is not usable as a benchmark.
    """
    path = repo_root / LOCK_PATH
    if not path.is_file():
        raise CorpusError(f"{LOCK_PATH} is missing; there is nothing to verify the corpus against")
    data = json.loads(path.read_text(encoding="utf-8"))
    return VendorLock(
        repo=data["repo"],
        commit=data["commit"],
        member=data["member"],
        size_bytes=int(data["size_bytes"]),
        sha256=data["sha256"],
        code_license=data["code_license"],
        data_license=data["data_license"],
        retrieved=data["retrieved"],
    )


def sha256_of(path: Path) -> str:
    """Hash a file in chunks, so a 29 MB corpus is not read into memory twice."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, lock: VendorLock) -> None:
    """Confirm a downloaded file is the pinned one, byte for byte.

    Size is checked first purely so the common failure — a truncated or
    error-page download — reports something more useful than a hash mismatch.

    Raises:
        CorpusError: The file is absent, the wrong size, or the wrong hash.
    """
    if not path.is_file():
        raise CorpusError(f"{path} is missing. Run `de fetch` to download it from {lock.url}")
    actual_size = path.stat().st_size
    if actual_size != lock.size_bytes:
        raise CorpusError(
            f"{path} is {actual_size} bytes, expected {lock.size_bytes}. A truncated download "
            "or an error page saved under the data's name are the usual causes; re-fetch."
        )
    actual_hash = sha256_of(path)
    if actual_hash != lock.sha256:
        raise CorpusError(
            f"{path} hashes to {actual_hash}, expected {lock.sha256}. This is the same refusal "
            "the golden files make: a benchmark that changes underneath the results makes every "
            "earlier number incomparable with every later one. Do not proceed by re-pinning the "
            "lock -- find out what changed first."
        )


def parse_corpus(text: str) -> list[ShardedInstruction]:
    """Parse the upstream JSON into instructions.

    Raises:
        CorpusError: A record is missing ``task_id``, ``task`` or ``shards``, or
            the top level is not a list. Upstream's shape is not ours to
            assume, and a loader that skipped malformed records would quietly
            shrink the benchmark.
    """
    data = json.loads(text)
    if not isinstance(data, list):
        raise CorpusError(f"expected a JSON list of records, got {type(data).__name__}")

    instructions: list[ShardedInstruction] = []
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise CorpusError(f"record {index} is {type(record).__name__}, not an object")
        missing = [key for key in ("task_id", "task", "shards") if key not in record]
        if missing:
            raise CorpusError(f"record {index} is missing {', '.join(missing)}")

        # Upstream shards are objects carrying `shard_id` and `shard`; the
        # ordering is positional and shard_id is 1-based, so the text alone is
        # what a turn needs.
        shards = tuple(
            shard["shard"] if isinstance(shard, dict) else str(shard) for shard in record["shards"]
        )
        payload = {k: v for k, v in record.items() if k not in ("task_id", "task", "shards")}
        instructions.append(
            ShardedInstruction(
                task_id=str(record["task_id"]),
                task=str(record["task"]),
                shards=shards,
                payload=payload,
            )
        )
    return instructions


def load_corpus(
    repo_root: Path,
    *,
    exclude_tasks: frozenset[str] = frozenset(),
    check_hash: bool = True,
) -> list[ShardedInstruction]:
    """Load the vendored corpus, verifying it against the lock first.

    Args:
        repo_root: Repository root.
        exclude_tasks: Families to drop. Pass :data:`UNIX_ONLY_TASKS` for Track
            A1. Empty by default so that dropping items is always something a
            caller did on purpose.
        check_hash: Hashing 29 MB costs a moment. Set ``False`` only where the
            file has already been verified in the same process — never for a
            run whose numbers will be reported.

    Raises:
        CorpusError: The lock or the corpus is missing, the corpus does not
            match the lock, or a record is malformed.
    """
    lock = load_lock(repo_root)
    path = repo_root / CORPUS_PATH
    if check_hash:
        verify(path, lock)
    elif not path.is_file():
        raise CorpusError(f"{path} is missing. Run `de fetch` to download it from {lock.url}")

    instructions = parse_corpus(path.read_text(encoding="utf-8"))
    if exclude_tasks:
        instructions = [item for item in instructions if item.task not in exclude_tasks]
    return instructions


@dataclass(frozen=True, slots=True)
class ShardSummary:
    """Turn-count distribution over a set of instructions."""

    n_instructions: int
    tasks: tuple[str, ...]
    min_turns: int
    median_turns: float
    mean_turns: float
    max_turns: int


def shard_summary(instructions: list[ShardedInstruction]) -> ShardSummary:
    """Measure the turn-count distribution.

    This exists because a number was invented. The programme sized Track A1
    around casefiles sharded "across ~6 turns", the work order's first standing
    rule is that an invented parameter is indistinguishable from a measured one
    three days later, and this is the function that settles it.

    Raises:
        ValueError: On an empty set, which has no distribution to report.
    """
    if not instructions:
        raise ValueError("no instructions to summarise")
    counts = sorted(item.n_turns for item in instructions)
    n = len(counts)
    middle = n // 2
    median = float(counts[middle]) if n % 2 else (counts[middle - 1] + counts[middle]) / 2.0
    return ShardSummary(
        n_instructions=n,
        tasks=tuple(sorted({item.task for item in instructions})),
        min_turns=counts[0],
        median_turns=median,
        mean_turns=sum(counts) / n,
        max_turns=counts[-1],
    )
