from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.quality_gate_runner.waiver_resolution import (
    WaiverResolutionError,
    main,
    resolve_post_crawl_waiver,
)


def create_directory_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            shell=False,
        )
        return
    link.symlink_to(target, target_is_directory=True)


def remove_directory_link(link: Path) -> None:
    if os.name == "nt":
        link.rmdir()
        return
    link.unlink()


class CrawlWaiverResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifact = {
            "artifact_id": "artifact-crawl-0001", "content_sha256": "a" * 64,
            "tenant_id": "tenant-heartweb", "project_id": "project-example", "run_id": "run-crawl-0001",
        }
        finding_keys = (
            "status_4xx", "status_5xx", "internal_html_4xx", "resource_4xx", "non_indexable", "missing_titles",
            "missing_titles_indexable", "missing_meta_descriptions", "missing_meta_descriptions_indexable", "missing_h1",
            "missing_h1_indexable", "missing_h2_indexable", "canonical_issues", "canonical_issues_indexable",
            "internal_link_issues", "redirect_issues", "broken_internal_links", "hreflang_issues", "structured_data_issues",
            "critical_security_issues", "security_issues",
        )
        self.evidence = {
            "schema_version": "1.1.0", "run_id": "run-crawl-0001", "project_id": "project-example", "deployment_id": "dep-example-de",
            "start_url": "https://example.test/", "final_url": "https://example.test/", "tool": {"id": "screaming-frog-cli", "binary_path": "sf-cli", "capability_hash": "a" * 64},
            "status": "blocked", "started_at": "2026-08-19T00:00:00Z", "completed_at": "2026-08-19T00:01:00Z", "url_count": 1, "html_url_count": 1,
            "limit_hit": False, "exports": [{"relative_path": "internal.csv", "bytes": 1, "sha256": "a" * 64}],
            "findings": dict.fromkeys(finding_keys, 0),
            "policy_disposition": {"policy_id": "heartweb-crawl-disposition", "policy_version": "1.0.0", "step_id": "1", "result": "blocked", "advisory_findings": [], "waiver_required_findings": [], "blocking_findings": [], "waived_findings": [], "waiver_ids": []},
        }
        self.evidence["findings"]["resource_4xx"] = 1
        self.waiver = {
            "waiver_id": "waiver-resource-0001", "tenant_id": "tenant-heartweb", "project_id": "project-example", "quality_gate_id": "qg-step1-crawl-snapshot",
            "artifact_id": self.artifact["artifact_id"], "artifact_sha256": self.artifact["content_sha256"],
            "policy_id": "heartweb-crawl-disposition", "policy_version": "1.0.0", "step_ids": ["1"],
            "finding_keys": ["resource_4xx"], "reason": "This resource is unrelated to Step 1 topic discovery and is tracked for repair.", "approver_id": "reviewer-raphael", "approved_at": "2026-08-19T00:00:00Z", "expires_at": "2026-08-20T00:00:00Z",
        }

    def test_valid_waiver_emits_bound_quality_gate_run(self) -> None:
        result = resolve_post_crawl_waiver(self.evidence, "a" * 64, self.artifact, self.waiver, "2026-08-19T12:00:00Z")

        self.assertEqual("passed_with_warnings", result["resolved_disposition"]["result"])
        self.assertEqual(self.artifact["content_sha256"], result["quality_gate_run"]["artifact_sha256"])
        self.assertEqual([self.waiver["waiver_id"]], result["quality_gate_run"]["waiver_ids"])

    def test_expired_hash_mismatched_and_disallowed_waivers_are_rejected(self) -> None:
        expired = dict(self.waiver, expires_at="2026-08-19T01:00:00Z")
        mismatched = dict(self.waiver, artifact_sha256="b" * 64)
        disallowed = dict(self.waiver, step_ids=["4b"])

        for waiver in (expired, mismatched, disallowed):
            with self.assertRaises(WaiverResolutionError):
                resolve_post_crawl_waiver(self.evidence, "a" * 64, self.artifact, waiver, "2026-08-19T12:00:00Z")

    def _write_cli_inputs(self, root: Path) -> tuple[Path, Path, Path]:
        inputs = root / "inputs"
        inputs.mkdir()
        evidence_path = inputs / "crawl-evidence.json"
        evidence_bytes = json.dumps(self.evidence, ensure_ascii=True).encode("utf-8")
        evidence_path.write_bytes(evidence_bytes)
        artifact = dict(self.artifact, content_sha256=hashlib.sha256(evidence_bytes).hexdigest())
        waiver = dict(self.waiver, artifact_sha256=artifact["content_sha256"])
        artifact_path = inputs / "crawl-artifact.json"
        waiver_path = inputs / "waiver.json"
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=True), encoding="utf-8")
        waiver_path.write_text(json.dumps(waiver, ensure_ascii=True), encoding="utf-8")
        return evidence_path, artifact_path, waiver_path

    def _invoke_cli(
        self,
        root: Path,
        evidence_path: str,
        artifact_path: str,
        waiver_path: str,
        tenant_id: str = "tenant-heartweb",
        project_id: str = "project-example",
        run_id: str = "run-crawl-0001",
    ) -> tuple[int, str, str]:
        arguments = [
            "waiver_resolution.py",
            "--resolution-root", str(root),
            "--tenant-id", tenant_id,
            "--project-id", project_id,
            "--run-id", run_id,
            "--crawl-evidence", evidence_path,
            "--crawl-artifact", artifact_path,
            "--waiver", waiver_path,
            "--evaluation-at", "2026-08-19T12:00:00Z",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "argv", arguments):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                return main(), stdout.getvalue(), stderr.getvalue()

    @staticmethod
    def _derived_output(root: Path) -> Path:
        return (
            root / "tenants" / "tenant-heartweb" / "projects" / "project-example"
            / "runs" / "run-crawl-0001" / "waiver-resolution.json"
        )

    def test_cli_writes_resolution_to_controlled_run_scoped_path_without_mutating_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence_path, artifact_path, waiver_path = self._write_cli_inputs(root)
            raw_evidence = evidence_path.read_bytes()

            return_code, stdout, stderr = self._invoke_cli(
                root,
                str(evidence_path.relative_to(root)),
                str(artifact_path.relative_to(root)),
                str(waiver_path.relative_to(root)),
            )

            output_path = self._derived_output(root)
            self.assertEqual(0, return_code)
            self.assertTrue(stdout)
            self.assertEqual("", stderr)
            self.assertTrue(output_path.is_file())
            self.assertNotEqual(output_path.resolve(), evidence_path.resolve())
            self.assertNotEqual(output_path.resolve(), artifact_path.resolve())
            self.assertNotEqual(output_path.resolve(), waiver_path.resolve())
            self.assertEqual(raw_evidence, evidence_path.read_bytes())

    def test_cli_rejects_derived_output_collision_with_crawl_evidence_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence_path, artifact_path, waiver_path = self._write_cli_inputs(root)
            output_path = self._derived_output(root)
            output_path.parent.mkdir(parents=True)
            output_path.write_bytes(evidence_path.read_bytes())

            return_code, _, stderr = self._invoke_cli(
                root,
                str(output_path.relative_to(root)),
                str(artifact_path.relative_to(root)),
                str(waiver_path.relative_to(root)),
            )

            self.assertEqual(1, return_code)
            self.assertIn("ERROR_CRAWL_WAIVER_EVIDENCE_INVALID", stderr)
            self.assertEqual(evidence_path.read_bytes(), output_path.read_bytes())

    def test_cli_rejects_traversal_and_absolute_input_paths_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence_path, artifact_path, waiver_path = self._write_cli_inputs(root)
            outside_path = root.parent / "outside-crawl-evidence.json"
            outside_path.write_bytes(evidence_path.read_bytes())

            for unsafe_path in ("../outside-crawl-evidence.json", str(outside_path)):
                with self.subTest(unsafe_path=unsafe_path):
                    return_code, _, stderr = self._invoke_cli(
                        root,
                        unsafe_path,
                        str(artifact_path.relative_to(root)),
                        str(waiver_path.relative_to(root)),
                    )

                    self.assertEqual(1, return_code)
                    self.assertIn("ERROR_CRAWL_WAIVER_EVIDENCE_INVALID", stderr)
                    self.assertFalse((root / "tenants").exists())

    def test_cli_rejects_input_symlink_escape_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            root = workspace / "resolution-root"
            outside = workspace / "outside-waiver-inputs"
            root.mkdir()
            outside.mkdir()
            evidence_path, artifact_path, waiver_path = self._write_cli_inputs(outside)
            input_link = root / "inputs"
            create_directory_link(input_link, outside)

            try:
                return_code, _, stderr = self._invoke_cli(
                    root,
                    "inputs/crawl-evidence.json",
                    str(artifact_path),
                    str(waiver_path),
                )
            finally:
                remove_directory_link(input_link)

            self.assertEqual(1, return_code)
            self.assertIn("ERROR_CRAWL_WAIVER_EVIDENCE_INVALID", stderr)
            self.assertFalse((root / "tenants").exists())
            self.assertTrue(outside.is_dir())
            self.assertTrue(evidence_path.is_file())

    def test_cli_rejects_preexisting_derived_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence_path, artifact_path, waiver_path = self._write_cli_inputs(root)
            arguments = (
                str(evidence_path.relative_to(root)),
                str(artifact_path.relative_to(root)),
                str(waiver_path.relative_to(root)),
            )

            first_return_code, _, _ = self._invoke_cli(root, *arguments)
            second_return_code, _, stderr = self._invoke_cli(root, *arguments)

            self.assertEqual(0, first_return_code)
            self.assertEqual(1, second_return_code)
            self.assertIn("ERROR_CRAWL_WAIVER_EVIDENCE_INVALID", stderr)

    def test_cli_rejects_invalid_identity_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence_path, artifact_path, waiver_path = self._write_cli_inputs(root)
            paths = (
                str(evidence_path.relative_to(root)),
                str(artifact_path.relative_to(root)),
                str(waiver_path.relative_to(root)),
            )
            invalid_identities = (
                {"tenant_id": "../tenant-heartweb"},
                {"project_id": "project/escape"},
                {"run_id": "run-unsafe"},
            )

            for overrides in invalid_identities:
                with self.subTest(overrides=overrides):
                    return_code, _, stderr = self._invoke_cli(root, *paths, **overrides)

                    self.assertEqual(1, return_code)
                    self.assertIn("ERROR_CRAWL_WAIVER_EVIDENCE_INVALID", stderr)
                    self.assertFalse((root / "tenants").exists())


if __name__ == "__main__":
    unittest.main()
