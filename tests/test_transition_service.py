"""Tests for the central Heartweb transition service.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from services.transition_service import process_transition, service as transition_service


ROOT = Path(__file__).resolve().parents[1]
BLOCK_FCNTL_IMPORT = (
    "import builtins; original = builtins.__import__; "
    "builtins.__import__ = lambda name, *args, **kwargs: "
    "(_ for _ in ()).throw(ModuleNotFoundError(name)) if name == 'fcntl' else original(name, *args, **kwargs); "
)


class TransitionServiceTests(unittest.TestCase):
    def setUp(self):
        self.run = {
            "run_id": "run-step1-0001",
            "tenant_id": "tenant-heartweb",
            "project_id": "project-ahd-hausbesuch",
            "step_id": "1",
            "gate_id": "GATE-1",
            "revision": 1,
            "status": "in_progress",
            "input_hash": "1" * 64,
            "idempotency_key": "idem-run-step1-0001",
            "attempt": 1,
            "created_at": "2026-08-19T05:00:00Z",
        }
        self.artifact = {
            "artifact_id": "artifact-topic-0001",
            "tenant_id": "tenant-heartweb",
            "project_id": "project-ahd-hausbesuch",
            "run_id": "run-step1-0001",
            "step_id": "1",
            "revision": 1,
            "content_sha256": "a" * 64,
        }
        self.crawl = {
            "artifact_id": "artifact-crawl-0001",
            "tenant_id": "tenant-heartweb",
            "project_id": "project-ahd-hausbesuch",
            "run_id": "run-crawl-0001",
            "step_id": "1",
            "revision": 1,
            "content_sha256": "b" * 64,
        }
        self.predecessor = {
            "step_id": "0",
            "gate_id": "GATE-0",
            "status": "released",
            "artifact_id": "artifact-step0-0001",
            "artifact_sha256": "1" * 64,
            "artifact_revision": 1,
        }
        self.context = {
            "site_status": "existing_site",
            "multilingual": False,
            "ymyl": True,
            "local": True,
            "production": False,
            "configured_tools": [],
            "available_tools": [],
            "not_applicable_decisions": {
                "qg-step1-independent-search-verification": {
                    "reason": "No independent source is configured for this controlled staging run."
                }
            },
        }
        self.gate_runs = [
            self._qgr("qg-domain-contract", self.artifact),
            self._qgr("qg-step1-crawl-snapshot", self.crawl),
        ]
        self.approval = {
            "approval_id": "approval-step1-0001",
            "tenant_id": "tenant-heartweb",
            "run_id": "run-step1-0001",
            "gate_id": "GATE-1",
            "artifact_id": "artifact-topic-0001",
            "artifact_sha256": "a" * 64,
            "artifact_revision": 1,
            "policy_version": "1.1.0",
            "reviewer_id": "reviewer-raphael",
            "decision": "approved",
            "decided_at": "2026-08-19T06:00:00Z",
            "expires_at": "2026-08-20T06:00:00Z",
        }

    def _qgr(self, gate_id: str, artifact: dict) -> dict:
        return {
            "quality_gate_run_id": f"qgr-{gate_id.removeprefix('qg-')}-0001",
            "quality_gate_id": gate_id,
            "human_gate_id": "GATE-1",
            "tenant_id": "tenant-heartweb",
            "run_id": artifact["run_id"],
            "step_id": "1",
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": artifact["content_sha256"],
            "artifact_revision": artifact["revision"],
            "registry_version": "1.1.0",
            "policy_version": "1.1.0",
            "result": "passed",
            "evidence": {
                "schema_id": "runtime", "schema_version": "1.0.0", "artifact_sha256": artifact["content_sha256"],
                "validator_result": "passed", "crawl_manifest": "crawl", "start_url": "https://example.test/",
                "tool_version": "1.0.0", "export_hashes": "a" * 64, "url_count": "1", "issues_overview": "none",
            },
            "checked_at": "2026-08-19T05:30:00Z",
            "checker_version": "test-1.0.0",
        }

    def _command(self, operation: str, status_run: dict | None = None) -> dict:
        run = status_run or self.run
        same_step = operation in {"approve", "complete", "publish", "retry", "supersede"}
        return {
            "command_id": f"command-step1-{operation.replace('_', '-')}-0001",
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "run_id": run["run_id"],
            "expected_revision": run["revision"],
            "idempotency_key": f"idem-step1-{operation.replace('_', '-')}-0001",
            "operation": operation,
            "from_step_id": "1" if same_step else "0",
            "to_step_id": "1",
            "input_hash": run["input_hash"],
            "output_hash": self.artifact["content_sha256"],
            "artifacts": [{"artifact_id": self.artifact["artifact_id"], "revision": 1, "content_sha256": "a" * 64}],
            "requested_at": "2026-08-19T07:00:00Z",
        }

    def _process(self, command: dict, run: dict, gate_runs: list[dict] | None = None, approval: dict | None = None, ledger=None):
        return process_transition(
            command,
            run,
            self.artifact,
            supporting_artifacts=[self.crawl],
            quality_gate_runs=self.gate_runs if gate_runs is None else gate_runs,
            approval=approval,
            predecessor_release=self.predecessor,
            context=self.context,
            idempotency_ledger=ledger,
        )

    def _portable_cli_command(self, request_path: Path, output_path: Path, ledger_path: Path) -> list[str]:
        return [
            sys.executable,
            "-c",
            BLOCK_FCNTL_IMPORT + "import runpy; runpy.run_module('services.transition_service.service', run_name='__main__')",
            "--request",
            str(request_path),
            "--output",
            str(output_path),
            "--ledger",
            str(ledger_path),
        ]

    def test_submit_for_gate_requires_and_accepts_machine_gates(self):
        result = self._process(self._command("submit_for_gate"), self.run)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual("awaiting_gate", result["run"]["status"])
        self.assertEqual("a" * 64, result["run"]["output_hash"])

    def test_start_requires_applicable_start_gates(self):
        run = dict(self.run, status="pending")

        result = self._process(self._command("start", run), run, gate_runs=[])

        self.assertFalse(result["ok"])
        self.assertIn("ERR_GATE_REQUIRED", {error["code"] for error in result["errors"]})

    def test_missing_machine_gate_blocks_without_mutation(self):
        command = self._command("submit_for_gate")
        result = self._process(command, self.run, gate_runs=[self.gate_runs[0]])
        self.assertFalse(result["ok"])
        self.assertEqual("in_progress", result["run"]["status"])
        self.assertIn("ERR_GATE_REQUIRED", {error["code"] for error in result["errors"]})

    def test_submit_for_gate_rejects_machine_qgr_for_an_older_artifact_revision(self):
        stale = copy.deepcopy(self.gate_runs)
        stale[0]["artifact_revision"] = 0

        result = self._process(self._command("submit_for_gate"), self.run, gate_runs=stale)

        self.assertFalse(result["ok"])
        self.assertIn("ERR_GATE_REQUIRED", {error["code"] for error in result["errors"]})

    def test_approve_validates_external_approval_and_emits_human_qgr(self):
        run = dict(self.run, status="awaiting_gate", output_hash="a" * 64)
        result = self._process(self._command("approve", run), run, approval=self.approval)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual("approved", result["run"]["status"])
        self.assertEqual("qg-gate1-artifact-approval", result["human_quality_gate_run"]["quality_gate_id"])
        self.assertEqual(1, result["human_quality_gate_run"]["artifact_revision"])
        self.assertEqual("1.1.0", result["human_quality_gate_run"]["registry_version"])
        self.assertEqual(self.approval["approval_id"], result["human_quality_gate_run"]["evidence"]["approval_id"])

    def test_expired_or_changed_approval_blocks(self):
        run = dict(self.run, status="awaiting_gate", output_hash="a" * 64)
        for approval in (
            dict(self.approval, expires_at="2026-08-19T06:30:00Z"),
            dict(self.approval, artifact_sha256="c" * 64),
        ):
            result = self._process(self._command("approve", run), run, approval=approval)
            self.assertFalse(result["ok"])
            self.assertIn("ERR_APPROVAL_STALE", {error["code"] for error in result["errors"]})

    def test_complete_requires_human_qgr_and_emits_release(self):
        run = dict(self.run, status="approved", output_hash="a" * 64)
        command = self._command("complete", run)
        human = self._qgr("qg-gate1-artifact-approval", self.artifact)
        blocked = self._process(command, run, approval=self.approval)
        self.assertFalse(blocked["ok"])
        passed = self._process(command, run, gate_runs=self.gate_runs + [human], approval=self.approval)
        self.assertTrue(passed["ok"], passed["errors"])
        self.assertEqual("completed", passed["run"]["status"])
        self.assertEqual("released", passed["release_record"]["status"])

    def test_stale_revision_and_output_hash_are_consolidated(self):
        command = self._command("submit_for_gate")
        command["expected_revision"] = 2
        command["output_hash"] = "c" * 64
        result = self._process(command, self.run)
        self.assertFalse(result["ok"])
        self.assertEqual({"ERR_STALE_REVISION", "ERR_ARTIFACT_REQUIRED"}, {error["code"] for error in result["errors"]})

    def test_idempotency_conflict_and_replay_are_distinct(self):
        command = self._command("submit_for_gate")
        first = self._process(command, self.run)
        replay = self._process(command, self.run, ledger={command["idempotency_key"]: first["command_fingerprint"]})
        conflict = self._process(command, self.run, ledger={command["idempotency_key"]: "f" * 64})
        self.assertTrue(replay["ok"])
        self.assertTrue(replay["replay"])
        self.assertFalse(conflict["ok"])
        self.assertIn("ERR_IDEMPOTENCY_CONFLICT", {error["code"] for error in conflict["errors"]})

    def test_retry_limit_is_fail_fast(self):
        run = dict(self.run, status="failed", attempt=3)
        result = self._process(self._command("retry", run), run)
        self.assertFalse(result["ok"])
        self.assertIn("ERR_RETRY_EXHAUSTED", {error["code"] for error in result["errors"]})

    def test_module_imports_when_fcntl_is_unavailable(self):
        completed = subprocess.run(
            [sys.executable, "-c", BLOCK_FCNTL_IMPORT + "import services.transition_service.service"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_durable_ledger_lock_releases_after_processing_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            lock_path = ledger_path.with_suffix(".json.lock")
            with self.assertRaises(RuntimeError):
                with transition_service.durable_ledger_lock(ledger_path):
                    raise RuntimeError("processing failed")
            self.assertFalse(lock_path.exists())
            with transition_service.durable_ledger_lock(ledger_path):
                self.assertTrue(lock_path.exists())

    def test_cli_fails_fast_when_ledger_lock_is_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            output_path = root / "result.json"
            ledger_path = root / "ledger.json"
            request_path.write_text("{}", encoding="utf-8")
            with transition_service.durable_ledger_lock(ledger_path):
                completed = subprocess.run(
                    self._portable_cli_command(request_path, output_path, ledger_path),
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertIn("ERROR_TRANSITION_LEDGER_LOCKED", completed.stderr)

    def test_cli_writes_one_atomic_result_envelope(self):
        request = {
            "command": self._command("submit_for_gate"),
            "run": self.run,
            "current_artifact": self.artifact,
            "supporting_artifacts": [self.crawl],
            "quality_gate_runs": self.gate_runs,
            "predecessor_release": self.predecessor,
            "context": self.context,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            output_path = root / "result.json"
            request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-m", "services.transition_service.service", "--request", str(request_path), "--output", str(output_path), "--ledger", str(root / "ledger.json")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(output_path.exists())
            self.assertEqual("awaiting_gate", json.loads(output_path.read_text(encoding="utf-8"))["run"]["status"])

    def test_cli_persists_identical_replay_and_rejects_conflicting_payload(self):
        request = {
            "command": self._command("submit_for_gate"), "run": self.run, "current_artifact": self.artifact,
            "supporting_artifacts": [self.crawl], "quality_gate_runs": self.gate_runs,
            "predecessor_release": self.predecessor, "context": self.context,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            output_path = root / "result.json"
            ledger_path = root / "ledger.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            command = self._portable_cli_command(request_path, output_path, ledger_path)

            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            replay = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            request["command"]["output_hash"] = "f" * 64
            request_path.write_text(json.dumps(request), encoding="utf-8")
            conflict = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)

            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(0, replay.returncode, replay.stderr)
            self.assertTrue(json.loads(replay.stdout)["replay"])
            self.assertNotEqual(0, conflict.returncode)
            self.assertIn("ERR_IDEMPOTENCY_CONFLICT", {error["code"] for error in json.loads(conflict.stdout)["errors"]})


if __name__ == "__main__":
    unittest.main()
