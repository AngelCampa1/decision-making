"""What the live site says about where it came from.

Written into ``site/dist/`` after the build and before the upload, so it exists
only in a tree that was actually deployed. ``de site`` on a machine cannot
produce it, and that is the point: a file only the deployer can write is the
only kind that can prove a deployment happened.

**Not ``site/public/``.** That directory is a hashed input of
``site/build-manifest.json`` (``site/inputs.json``, the ``site`` array), so
writing there would make every deployment disagree with the committed manifest,
and the staleness gate would start firing on its own output. A gate that fires
on its own output is a gate somebody turns off.

The field names are the contract with ``decision_evals.deployed``.
``tests/unit/test_workflow.py`` asserts the two agree. This file must not
import the package: the runner installs Node, never Python dependencies, so
only the standard library is available here.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

MANIFEST = Path("site/build-manifest.json")
BUILT = Path("site/dist")
TARGET = BUILT / "deploy-provenance.json"

#: What a real Astro build always leaves at the root of ``dist/``. Its absence
#: is the difference between "the build produced a site" and "the build exited
#: 0", and those are not the same thing.
INDEX = BUILT / "index.html"


def manifest_digest() -> str | None:
    """SHA-256 of the committed manifest, line endings normalised.

    The same normalisation as ``decision_evals.site._digest``, so this Linux
    runner and a Windows checkout agree. ``None`` rather than a fabricated
    value when the file is absent: an absent manifest is a fact, and a zero
    digest would read as one.
    """
    if not MANIFEST.is_file():
        return None
    return hashlib.sha256(MANIFEST.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def payload() -> dict[str, object]:
    """The record the live site will serve."""
    return {
        "generated_by": ".github/workflows/deploy-site.yml",
        "note": (
            "Written by the deploying workflow, never by `de site`. Records the "
            "commit this published tree was built from, so `de deployed` can "
            "refuse a live site that is behind origin/main."
        ),
        "commit": os.environ["GITHUB_SHA"],
        "ref": os.environ["GITHUB_REF"],
        "run_id": os.environ["GITHUB_RUN_ID"],
        "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "run_url": os.environ["RUN_URL"],
        "built_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "build_manifest_sha256": manifest_digest(),
    }


def main() -> None:
    """Write the record, or refuse and fail the run.

    **It must never create ``site/dist/``.** An earlier version opened with
    ``TARGET.parent.mkdir(parents=True, exist_ok=True)``, and that one line
    meant that if ``npm run build`` ever exited 0 without producing a site -- a
    moved ``outDir``, an empty content collection, a build that wrote somewhere
    else -- this script manufactured the directory, the artifact upload
    published a tree containing one JSON file, ``deploy-pages`` went green, and
    ``de deployed`` read that file back and reported the live site current.
    Every signal agreeing, and a 404 for every visitor.

    That is the failure ``tests/unit/test_workflow.py`` opens by naming, and the
    command built to catch it could not have returned a non-zero value for it --
    which this repository has a standing rule against shipping. The refusal
    belongs here, at the last point that can still tell the difference.
    """
    if not INDEX.is_file():
        raise SystemExit(
            f"{INDEX} does not exist, so the build produced no site to publish. "
            "Refusing to write the deployment record: it would make an empty "
            "artifact indistinguishable from a successful deploy."
        )
    TARGET.write_text(
        json.dumps(payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(TARGET.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
