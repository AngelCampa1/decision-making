"""The deploy workflow is the only thing that can publish, so its shape is load-bearing.

There is no cloud gate to catch a mistake in here, and the failure mode is quiet
in the way this repository keeps paying for: a workflow pointing at the wrong
directory deploys an empty site and reports success.

These are structural assertions only -- that the trigger is `main`, that the
artifact is the built tree, that nothing third-party runs, and that the writer
of the provenance record and its reader agree on the field names. Whether the
site is *correct* is still answered by fetching it, which is what `de deployed`
and step 9 of the work order are for.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals import deployed as dep

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/deploy-site.yml"
WRITER = ROOT / ".github/scripts/write_deployment.py"

SHA = "f01d325cf1c2199d4f69e845efa9d806c4e805eb"


class _Served:
    """A stand-in for what `urlopen` hands back, as a context manager."""

    def __init__(self, payload: str) -> None:
        self._payload = payload.encode("utf-8")

    def __enter__(self) -> _Served:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self, amount: int | None = None) -> bytes:
        return self._payload[:amount]


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _steps(workflow: dict[str, Any], job: str) -> list[dict[str, Any]]:
    return list(workflow["jobs"][job]["steps"])


def _using(workflow: dict[str, Any], job: str, action: str) -> list[dict[str, Any]]:
    return [s for s in _steps(workflow, job) if str(s.get("uses", "")).startswith(action)]


def _triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    """The `on:` block.

    YAML 1.1 reads a bare ``on`` as the boolean ``True``, which is why this is
    not simply ``workflow["on"]``.
    """
    return workflow[True] if True in workflow else workflow["on"]


class TestTrigger:
    def test_it_publishes_only_from_main(self, workflow: dict[str, Any]) -> None:
        """The whole point. Publishing used to take whatever local HEAD was, and
        on 2026-08-19 that published a work-in-progress commit from a branch."""
        assert _triggers(workflow)["push"]["branches"] == ["main"]

    def test_it_can_be_run_by_hand(self, workflow: dict[str, Any]) -> None:
        """Needed for the switchover, and for a re-deploy after a rollback."""
        assert "workflow_dispatch" in _triggers(workflow)

    def test_a_dispatch_from_a_branch_builds_without_publishing(
        self, workflow: dict[str, Any]
    ) -> None:
        """What makes it safe to prove this workflow before the Pages source is
        switched over, and safe to test a change to it afterwards."""
        assert workflow["jobs"]["deploy"]["if"] == "github.ref == 'refs/heads/main'"


class TestSafety:
    def test_it_asks_for_the_permissions_pages_deployment_needs(
        self, workflow: dict[str, Any]
    ) -> None:
        assert workflow["permissions"]["pages"] == "write"
        assert workflow["permissions"]["id-token"] == "write"
        assert workflow["permissions"]["contents"] == "read"

    def test_two_pushes_cannot_race_to_publish(self, workflow: dict[str, Any]) -> None:
        assert workflow["concurrency"]["group"].startswith("pages")

    def test_a_branch_test_cannot_cancel_a_real_deployment(self, workflow: dict[str, Any]) -> None:
        """The group is keyed on the ref. With one fixed group, a third run
        joining cancels the queued one, so a build-only dispatch from a branch
        could drop an accepted `main` deployment."""
        assert "github.ref" in workflow["concurrency"]["group"]

    def test_a_deploy_is_never_cancelled_halfway(self, workflow: dict[str, Any]) -> None:
        """Aborting mid-upload is how a Pages deployment gets wedged. Queue the
        later run instead; the later commit winning is the right answer."""
        assert workflow["concurrency"]["cancel-in-progress"] is False

    def test_nothing_third_party_runs(self, workflow: dict[str, Any]) -> None:
        """First-party actions only. A deploy step is the one place here where
        somebody else's code would run with write access to what the world
        sees."""
        used = [
            str(step["uses"])
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        ]
        assert used, "no actions are used at all, so this test is checking nothing"
        assert all(u.startswith("actions/") for u in used), used


class TestArtifact:
    def test_it_uploads_the_built_tree(self, workflow: dict[str, Any]) -> None:
        """`site/dist` is what `astro build` writes. Pointing this anywhere else
        deploys an empty site and goes green doing it."""
        upload = _using(workflow, "build", "actions/upload-pages-artifact")
        assert len(upload) == 1
        assert upload[0]["with"]["path"] == "site/dist"

    def test_hidden_files_are_included(self, workflow: dict[str, Any]) -> None:
        """The action tars with `--exclude=.[^/]*` by default, which drops
        `dist/.nojekyll`. Nothing breaks without it under Actions-sourced Pages,
        but the published tree would stop being byte-identical to the local
        one."""
        assert (
            _using(workflow, "build", "actions/upload-pages-artifact")[0]["with"][
                "include-hidden-files"
            ]
            == "true"
        )

    def test_the_base_path_stays_a_property_of_the_repository(
        self, workflow: dict[str, Any]
    ) -> None:
        """`configure-pages` takes no `static_site_generator` here. That input
        accepts only nuxt, next, gatsby and sveltekit, and `site`/`base` are
        already committed in `site/astro.config.mjs`. Injecting them from the
        runner is how the deployed base path and the config come to disagree."""
        configure = _using(workflow, "build", "actions/configure-pages")
        assert len(configure) == 1
        assert "with" not in configure[0]

    def test_the_deploy_job_waits_for_the_build(self, workflow: dict[str, Any]) -> None:
        deploy = workflow["jobs"]["deploy"]
        assert deploy["needs"] == "build"
        assert _using(workflow, "deploy", "actions/deploy-pages")


class TestTheBuildActuallyRuns:
    """Every one of these could be deleted from the workflow and the rest of
    this file would stay green, which is the failure mode these close: the
    artifact step only ever checked a path string."""

    def test_the_site_is_built(self, workflow: dict[str, Any]) -> None:
        runs = [str(s.get("run", "")) for s in _steps(workflow, "build")]
        assert any("npm run build" in r for r in runs)

    def test_dependencies_are_installed_from_the_lockfile(self, workflow: dict[str, Any]) -> None:
        """`npm ci`, not `npm install`. The lockfile is the pinned input."""
        runs = [str(s.get("run", "")) for s in _steps(workflow, "build")]
        assert any(r.strip() == "npm ci" for r in runs)

    @pytest.mark.parametrize("command", ["npm ci", "npm run build"])
    def test_npm_runs_in_the_site_project(self, workflow: dict[str, Any], command: str) -> None:
        """Without this the commands run at the repository root, where there is
        no `package.json` at all."""
        step = next(s for s in _steps(workflow, "build") if command in str(s.get("run", "")))
        assert step.get("working-directory") == "site"

    def test_the_build_happens_before_the_upload(self, workflow: dict[str, Any]) -> None:
        """Ordering, which nothing else here asserts. An upload placed before
        the build publishes whatever `dist/` was lying around."""
        steps = _steps(workflow, "build")
        built = next(i for i, s in enumerate(steps) if "npm run build" in str(s.get("run", "")))
        uploaded = next(
            i
            for i, s in enumerate(steps)
            if str(s.get("uses", "")).startswith("actions/upload-pages-artifact")
        )
        assert built < uploaded


class TestProvenanceWriter:
    """A writer in `.github/scripts/` and a reader in `evals/src/` is exactly the
    shape of drift `site/inputs.json` exists to prevent for the build. These
    tests are the equivalent for the deployment record."""

    @staticmethod
    def _payload(monkeypatch: pytest.MonkeyPatch, cwd: Path) -> dict[str, object]:
        for key, value in {
            "GITHUB_SHA": SHA,
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ID": "42",
            "GITHUB_RUN_ATTEMPT": "1",
            "RUN_URL": "https://github.com/o/r/actions/runs/42",
        }.items():
            monkeypatch.setenv(key, value)
        monkeypatch.chdir(cwd)

        spec = importlib.util.spec_from_file_location("write_deployment", WRITER)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.payload()  # type: ignore[no-any-return]

    def test_the_writer_is_invoked_by_the_workflow(self, workflow: dict[str, Any]) -> None:
        scripts = "\n".join(str(s.get("run", "")) for s in _steps(workflow, "build"))
        assert ".github/scripts/write_deployment.py" in scripts

    def test_it_runs_from_the_repository_root(self, workflow: dict[str, Any]) -> None:
        """The script resolves `site/build-manifest.json` and `site/dist/`
        relative to the working directory. Both neighbouring steps carry
        `working-directory: site`, so copying one onto this step is a plausible
        edit -- and it would write the record to `site/site/dist/`, leaving the
        published artifact with no provenance at all."""
        step = next(
            s for s in _steps(workflow, "build") if "write_deployment.py" in str(s.get("run", ""))
        )
        assert "working-directory" not in step

    def test_it_runs_before_the_upload(self, workflow: dict[str, Any]) -> None:
        """Written after it, the record never reaches the artifact."""
        steps = _steps(workflow, "build")
        wrote = next(
            i for i, s in enumerate(steps) if "write_deployment.py" in str(s.get("run", ""))
        )
        uploaded = next(
            i
            for i, s in enumerate(steps)
            if str(s.get("uses", "")).startswith("actions/upload-pages-artifact")
        )
        assert wrote < uploaded

    def test_what_it_writes_is_what_the_reader_reads(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The contract, asserted end to end rather than by eye."""
        (tmp_path / "site").mkdir()
        (tmp_path / dep.MANIFEST_PATH).write_text("{}", encoding="utf-8")
        record = self._payload(monkeypatch, tmp_path)

        assert record["commit"] == SHA
        # Both sides hash the manifest the same way, which is what makes the
        # recorded digest worth anything to a human reading it. No verdict is
        # taken from it; see `deployed.manifest_digest`.
        assert record["build_manifest_sha256"] == dep.manifest_digest(tmp_path)

        # The reader must accept the writer's own output verbatim, and read the
        # commit back out of it. This is the contract, end to end.
        served = json.dumps(record)
        monkeypatch.setattr(
            dep.urllib.request, "urlopen", lambda url, timeout=None: _Served(served)
        )
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: SHA)
        assert dep.check_deployed(tmp_path, "http://x").status == dep.CURRENT

    def test_an_absent_manifest_is_recorded_as_absent_not_as_zero(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A fabricated digest would read as a fact."""
        assert self._payload(monkeypatch, tmp_path)["build_manifest_sha256"] is None

    def test_it_writes_into_dist_and_never_into_public(self) -> None:
        """`site/public/**` is a hashed input of `site/build-manifest.json`, so
        writing there would make every deployment disagree with the committed
        manifest and the gate would fire on its own output."""
        source = WRITER.read_text(encoding="utf-8")
        assert 'Path("site/dist/deploy-provenance.json")' in source
        assert "site/public/deploy-provenance.json" not in source
