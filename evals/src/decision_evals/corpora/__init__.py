"""Third-party corpora, vendored by hash rather than authored here.

Authoring is the activity in this repository with the worst record: three
corpora built, three discarded, and 21 of 21 scored failures traced to the
answer key rather than the model. Where a published instrument exists, it is
used, and the payload is pinned to an upstream commit and a SHA-256 so that
"we ran the published corpus" stays a checkable statement.
"""

from decision_evals.corpora.lost_in_conversation import (
    CORPUS_PATH,
    LOCK_PATH,
    TASKS,
    UNIX_ONLY_TASKS,
    CorpusError,
    ShardedInstruction,
    ShardSummary,
    VendorLock,
    load_corpus,
    load_lock,
    parse_corpus,
    sha256_of,
    shard_summary,
    verify,
)

__all__ = [
    "CORPUS_PATH",
    "LOCK_PATH",
    "TASKS",
    "UNIX_ONLY_TASKS",
    "CorpusError",
    "ShardSummary",
    "ShardedInstruction",
    "VendorLock",
    "load_corpus",
    "load_lock",
    "parse_corpus",
    "sha256_of",
    "shard_summary",
    "verify",
]
