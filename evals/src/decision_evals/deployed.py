"""Whether the site the world can see is a build of the current ``main``.

Every other check in this repository is offline. This one is not, and that is
the point of it. :mod:`decision_evals.site` proves the committed build matches
the tree; it says so itself, and it says what it cannot reach -- a green gate
beside a build that never left the machine is exactly as green as a deployed
one. So the last link in the chain was carried by whoever remembered.

On 2026-08-19 it was not remembered, twice in one morning. A build of
``91f2313`` -- a work-in-progress commit on a feature branch, never on ``main``
-- was published and caught by hand nine minutes later. Separately the published
branch sat 43 minutes and one commit behind ``main`` with nothing to say so.
Neither is possible now: ``.github/workflows/deploy-site.yml`` publishes on push
to ``main``, and nothing else can publish at all.

That workflow is the fix. This module is the *evidence*, and the two are not the
same thing. A workflow can be green while the site is stale -- a run can be
dropped by the concurrency group, the Pages source can be pointed elsewhere, a
deployment can be rolled back in the web UI. So the deploy writes
``deploy-provenance.json`` into the published tree, and this reads it back
**over HTTPS from the live URL**, which is the only reading that asks what
visitors actually get. Fetching the branch, or the artifact, or the local
``dist/`` would each answer a question nobody was asking: the failure already on
record here is precisely a case where the local build was correct, the push
succeeded, and the host served something else for six days.

**Not part of ``de check``, deliberately.** That gate is offline and
deterministic by design, and a step that reaches the network is neither -- it
would fail on a plane and turn a refusal into a coin toss. ``de deployed`` is a
separate command, run when the answer is wanted. Importing this module does not
make anything online; only calling it does.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Where the published site lives. The project-pages URL is unchanged by
#: publishing from Actions rather than from a branch.
SITE_URL: Final = "https://angelcampa1.github.io/decision-making-skills/"

#: Written into ``site/dist/`` by the deploy workflow, after the build and never
#: into ``site/public/`` -- that directory is a hashed input in
#: ``site/inputs.json``, so a file written there would put the built tree in
#: disagreement with the committed manifest.
PROVENANCE_URL: Final = SITE_URL + "deploy-provenance.json"

#: The committed record of what the last local build was built from. Hashed the
#: same way here and in the workflow, so the two digests are comparable.
MANIFEST_PATH: Final = "site/build-manifest.json"

#: The branch that is allowed to be published. There is only one.
REMOTE_REF: Final = "refs/heads/main"

#: Seconds. Long enough for a cold CDN edge, short enough that an unreachable
#: host is an answer rather than a hang.
TIMEOUT: Final = 10.0

#: Seconds allowed to ``git``. ``ls-remote`` talks to the network too, so the
#: promise above has to cover it: without this, an unreachable or
#: auth-challenging remote blocks forever, and on Windows the credential helper
#: can raise a GUI prompt that never returns to a process nobody is watching.
GIT_TIMEOUT: Final = 20.0

#: A body larger than this is not the file that was asked for. The record is
#: well under a kilobyte.
MAX_BYTES: Final = 64_000

#: A full commit SHA, and nothing else. This is what stops a Pages 404 page, a
#: CDN interstitial or a truncated body from being read as an answer -- each of
#: those can parse as JSON and carry a plausible-looking string.
_FULL_SHA: Final = re.compile(r"[0-9a-f]{40}")

CURRENT: Final = "current"
BEHIND: Final = "behind"
UNREACHABLE: Final = "unreachable"


class UnreachableError(Exception):
    """The live site, or the remote, could not be asked.

    Kept distinct from *behind* because the two license different actions. A
    stale site needs a deploy; an unreachable one needs a person to find out
    why, and reporting it as drift would send them to fix the wrong thing.
    """


@dataclass(frozen=True)
class DeployState:
    """What the live site is, and the sentence a reader gets."""

    status: str
    detail: str

    def __str__(self) -> str:
        return self.detail

    @property
    def exit_code(self) -> int:
        """0 current, 1 drifted, 2 could not be determined.

        Three, not two: a script that treats "could not ask" as "up to date"
        recreates the failure this module exists to remove, one level up.
        """
        if self.status == CURRENT:
            return 0
        if self.status == BEHIND:
            return 1
        return 2


def _git(repo_root: Path, args: list[str]) -> str | None:
    """``git`` stdout, or ``None`` when git could not answer.

    ``None`` covers every way of not getting an answer -- git missing, a
    non-zero exit, a hang -- because none of them licenses a verdict about the
    live site. ``GIT_TERMINAL_PROMPT=0`` turns an authentication challenge into
    a failure instead of a prompt nobody is at the keyboard to see.
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def fetch_provenance(url: str = PROVENANCE_URL, timeout: float = TIMEOUT) -> dict[str, object]:
    """The provenance record the live site is serving.

    :raises UnreachableError: the host did not answer, or answered with something
        that is not a JSON object.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = response.read(MAX_BYTES).decode("utf-8")
    except OSError as exc:
        raise UnreachableError(f"could not fetch {url}: {exc}") from exc

    try:
        record = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise UnreachableError(f"{url} is not JSON: {exc}") from exc

    if not isinstance(record, dict):
        raise UnreachableError(f"{url} is JSON but not an object")
    return record


def remote_head(repo_root: Path, ref: str = REMOTE_REF) -> str:
    """The tip of ``main`` on the remote.

    Asked of the remote rather than of a local ref on purpose. A local
    ``origin/main`` is only as fresh as the last fetch, and a check that
    silently compares against a stale copy is the same class of bug, one level
    up, as the one this command reports.

    :raises UnreachableError: the remote could not be reached, or has no such ref.
    """
    out = _git(repo_root, ["ls-remote", "origin", ref])
    if not out:
        raise UnreachableError(f"could not read {ref} from origin")
    return out.split()[0]


def manifest_digest(repo_root: Path) -> str | None:
    """SHA-256 of the committed build manifest, or ``None`` if it is absent.

    Line endings are normalised first, matching ``decision_evals.site._digest``,
    so a Windows and a Linux checkout agree. The workflow that writes this
    digest runs on Linux and the command that reads it usually does not.

    **No verdict is derived from this.** The deploy records the same digest into
    ``deploy-provenance.json``, where it is worth having when a human is working
    out what happened, and it is read by the test that holds the writer and this
    module to the same field names. But comparing it here would be one of two
    useless things. Against the *working tree* it fires whenever the checkout is
    not sitting exactly on the deployed commit, which is nearly always, and it
    did in every branch this was tried on. Against the manifest *in the deployed
    commit* it can never disagree, because that is the file the workflow hashed
    -- an estimator with no non-zero outcome, which this repository has a
    standing rule against shipping. The commit SHA already determines the tree.
    """
    manifest = repo_root / MANIFEST_PATH
    if not manifest.is_file():
        return None
    return hashlib.sha256(manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _distance(repo_root: Path, deployed_sha: str, head: str) -> str:
    """How far behind, in commits, when local history can actually say.

    Ancestry is checked first, and that is not ceremony. ``rev-list --count
    A..B`` answers "commits on B not on A", which equals "how far behind" only
    when A is an ancestor of B. If ``main`` were force-pushed backwards the
    deployed commit would be a *descendant* of the new tip, the count would come
    back ``0``, and this would have reported "0 commit(s) behind" beside a
    verdict of *behind* -- a self-contradiction covering up a live site that is
    ahead of the branch.
    """
    if _git(repo_root, ["merge-base", "--is-ancestor", deployed_sha, head]) is None:
        return (
            "and the deployed commit is not an ancestor of it, so the two have "
            "diverged or it is not in this checkout"
        )
    count = _git(repo_root, ["rev-list", "--count", f"{deployed_sha}..{head}"])
    if count is None:
        return "and the distance cannot be counted in this checkout"
    return f"and the live site is {count} commit(s) behind"


def check_deployed(
    repo_root: Path,
    url: str = PROVENANCE_URL,
    timeout: float = TIMEOUT,
) -> DeployState:
    """Compare what the live site says it is against the tip of ``main``."""
    try:
        record = fetch_provenance(url, timeout)
        head = remote_head(repo_root)
    except UnreachableError as exc:
        return DeployState(UNREACHABLE, str(exc))

    commit = record.get("commit")
    if not isinstance(commit, str) or not _FULL_SHA.fullmatch(commit):
        return DeployState(
            UNREACHABLE,
            f"{url} carries no usable `commit`, so what is deployed cannot be established",
        )

    if commit != head:
        return DeployState(
            BEHIND,
            f"the live site is a build of {commit[:7]}, origin/main is at "
            f"{head[:7]}, {_distance(repo_root, commit, head)}",
        )

    return DeployState(CURRENT, f"the live site is a build of {commit[:7]}, which is origin/main")
