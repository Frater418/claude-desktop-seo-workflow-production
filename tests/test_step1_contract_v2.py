"""Step 1 V2 contract and lineage tests.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from services.step1_preflight.validator import validate_step1_files, validate_step1_preflight


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step1"
CLUSTER_FIELDS = {
    "cluster_id",
    "name",
    "content_type",
    "hypothesized_intent",
    "information_gain_score",
    "conversational_query_patterns",
    "geo_engine_targets",
    "regional_scope",
    "source_evidence_ids",
    "status",
}


def _load_json(name: str) -> dict:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if name == "positive-inventory.json":
        payload.update(
            {
                "step_id": "1",
                "revision": 1,
                "source_artifact_ids": ["artifact-step0-0001"],
                "evidence_ids": [
                    "evidence-source-0001",
                    "evidence-competitor-0001",
                    "evidence-existing-url-0001",
                    "evidence-crawl-0001",
                ],
                "candidate_status": "awaiting_gate",
            }
        )
    return payload


def _canonical_inventory(inventory: dict | None = None) -> bytes:
    if inventory is None:
        inventory = _load_json("positive-inventory.json")
    return json.dumps(inventory, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")


def _quality_gate(
    run_id: str,
    gate_run_id: str,
    quality_gate_id: str,
    human_gate_id: str,
    artifact_id: str,
    artifact_sha256: str,
    step_id: str,
) -> dict:
    return {
        "quality_gate_run_id": gate_run_id,
        "quality_gate_id": quality_gate_id,
        "human_gate_id": human_gate_id,
        "tenant_id": "tenant-heartweb",
        "run_id": run_id,
        "step_id": step_id,
        "artifact_id": artifact_id,
        "artifact_sha256": artifact_sha256,
        "registry_version": "1.1.0",
        "policy_version": "1.0.0",
        "result": "passed",
        "evidence": {
            "schema_id": "step1", "schema_version": "1.0.0", "artifact_sha256": artifact_sha256,
            "validator_result": "passed", "crawl_manifest": "crawl", "start_url": "https://example.test/",
            "tool_version": "1.0.0", "export_hashes": "a" * 64, "url_count": "1", "issues_overview": "none",
        },
        "findings": [],
        "checked_at": "2026-08-19T12:02:00Z",
        "checker_version": "step1-v2-tests",
    }


def _valid_bundle(inventory: dict | None = None) -> dict:
    bundle = _load_json("positive-bundle.json")
    bundle["project"] = json.loads(
        (ROOT / "tests" / "fixtures" / "domain" / "real-customer-matrix" / "regional-care.json").read_text(encoding="utf-8")
    )
    bundle["as_of"] = bundle.pop("evaluation_at", "2026-08-19T12:05:00Z")
    bundle["approval"] = None
    bundle["waivers"] = []
    bundle["gate_context"] = {
        "site_status": "existing_site",
        "multilingual": False,
        "ymyl": True,
        "local": True,
        "production": False,
        "configured_tools": [],
        "available_tools": ["jsonschema", "screaming-frog-cli"],
        "not_applicable_decisions": {
            "qg-step1-independent-search-verification": {
                "reason": "No independent source is configured for this controlled fixture."
            }
        },
    }

    source = _canonical_inventory(inventory)
    inventory_data = json.loads(source)
    inventory_hash = hashlib.sha256(source).hexdigest()
    bundle["inventory_bytes"] = source.decode("ascii")
    bundle["artifact"].update(
        {
            "artifact_id": inventory_data["artifact_id"],
            "run_id": inventory_data["run_id"],
            "project_id": inventory_data["project_id"],
            "step_id": "1",
            "revision": bundle["run"]["revision"],
            "content_sha256": inventory_hash,
            "parent_artifact_ids": [bundle["source_artifact"]["artifact_id"]],
            "storage_key": f"tenants/tenant-heartweb/projects/{inventory_data['project_id']}/runs/{inventory_data['run_id']}/artifacts/{inventory_data['artifact_id']}/topic-inventory.v1.json",
        }
    )
    bundle["run"].update(
        {
            "run_id": inventory_data["run_id"],
            "project_id": inventory_data["project_id"],
            "step_id": "1",
            "gate_id": "GATE-1",
            "status": "awaiting_gate",
            "input_hash": bundle["source_artifact"]["content_sha256"],
            "output_hash": inventory_hash,
        }
    )

    crawl_hash = "d" * 64
    crawl_run_id = "run-crawl-0001"
    crawl_artifact_id = "artifact-crawl-0001"
    snapshot = copy.deepcopy(bundle["crawl_snapshots"][0])
    snapshot.update(
        {
            "schema_version": "1.1.0",
            "run_id": crawl_run_id,
            "project_id": inventory_data["project_id"],
            "deployment_id": inventory_data["deployment_id"],
            "final_url": snapshot["start_url"],
            "status": "passed",
            "limit_hit": False,
            "findings": {
                "status_4xx": 0,
                "status_5xx": 0,
                "internal_html_4xx": 0,
                "resource_4xx": 0,
                "non_indexable": 0,
                "missing_titles": 0,
                "missing_titles_indexable": 0,
                "missing_meta_descriptions": 0,
                "missing_meta_descriptions_indexable": 0,
                "missing_h1": 0,
                "missing_h1_indexable": 0,
                "missing_h2_indexable": 0,
                "canonical_issues": 0,
                "canonical_issues_indexable": 0,
                "internal_link_issues": 0,
                "redirect_issues": 0,
                "broken_internal_links": 0,
                "hreflang_issues": 0,
                "structured_data_issues": 0,
                "critical_security_issues": 0,
                "security_issues": 0,
            },
            "policy_disposition": {
                "policy_id": "heartweb-crawl-disposition",
                "policy_version": "1.0.0",
                "step_id": "1",
                "result": "passed",
                "advisory_findings": [],
                "waiver_required_findings": [],
                "blocking_findings": [],
                "waived_findings": [],
                "waiver_ids": [],
            },
        }
    )
    bundle["crawl_snapshots"] = [snapshot]
    bundle["crawl_snapshot_hashes"] = {crawl_run_id: crawl_hash}
    bundle["crawl_artifacts"] = [
        {
            "artifact_id": crawl_artifact_id,
            "tenant_id": "tenant-heartweb",
            "project_id": inventory_data["project_id"],
            "run_id": crawl_run_id,
            "step_id": "1",
            "revision": 1,
            "input_hash": bundle["source_artifact"]["content_sha256"],
            "content_sha256": crawl_hash,
            "parent_artifact_ids": [bundle["source_artifact"]["artifact_id"]],
            "contract_version": "1.0.0",
            "producer_version": "screaming-frog-test",
            "storage_key": f"tenants/tenant-heartweb/projects/{inventory_data['project_id']}/runs/{crawl_run_id}/artifacts/{crawl_artifact_id}/crawl-evidence.json",
            "created_at": "2026-08-19T12:01:00Z",
        }
    ]
    for record in bundle["evidence_records"]:
        if record["evidence_id"] == "evidence-crawl-0001":
            record["content_sha256"] = crawl_hash

    source_artifact = bundle["source_artifact"]
    gate0 = _quality_gate(
        source_artifact["run_id"],
        "qgr-step0-domain-0001",
        "qg-domain-contract",
        "GATE-0",
        source_artifact["artifact_id"],
        source_artifact["content_sha256"],
        "0",
    )
    crawl_gate = _quality_gate(
        crawl_run_id,
        "qgr-step1-crawl-0001",
        "qg-step1-crawl-snapshot",
        "GATE-1",
        crawl_artifact_id,
        crawl_hash,
        "1",
    )
    inventory_gate = _quality_gate(
        inventory_data["run_id"],
        "qgr-step1-contract-0001",
        "qg-domain-contract",
        "GATE-1",
        inventory_data["artifact_id"],
        inventory_hash,
        "1",
    )
    bundle["quality_gates"] = [gate0, crawl_gate, inventory_gate]

    bundle["transition"].update(
        {
            "tenant_id": "tenant-heartweb",
            "project_id": inventory_data["project_id"],
            "run_id": inventory_data["run_id"],
            "from_step_id": "0",
            "to_step_id": "1",
            "expected_revision": bundle["run"]["revision"],
            "input_hash": source_artifact["content_sha256"],
            "output_hash": inventory_hash,
            "operation": "submit_for_gate",
            "predecessor_release": {
                "step_id": "0",
                "gate_id": "GATE-0",
                "status": "released",
                "artifact_id": source_artifact["artifact_id"],
                "artifact_sha256": source_artifact["content_sha256"],
                "artifact_revision": source_artifact["revision"],
            },
            "artifacts": [
                {
                    "artifact_id": inventory_data["artifact_id"],
                    "revision": bundle["artifact"]["revision"],
                    "content_sha256": inventory_hash,
                }
            ],
            "quality_gate": {
                "quality_gate_run_id": inventory_gate["quality_gate_run_id"],
                "result": "passed",
                "artifact_id": inventory_data["artifact_id"],
                "artifact_sha256": inventory_hash,
            },
        }
    )
    bundle["transition"].pop("approval", None)
    return bundle


class Step1ContractV2Tests(unittest.TestCase):
    def test_positive_inventory_validates_and_cluster_contract_is_complete(self):
        schema = json.loads((ROOT / "standards" / "outputs" / "step-1-topic-inventory.schema.json").read_text(encoding="utf-8"))
        inventory = _load_json("positive-inventory.json")
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(inventory))
        self.assertEqual([], errors, [error.message for error in errors])
        self.assertEqual(CLUSTER_FIELDS, set(schema["$defs"]["cluster"]["required"]))

    def test_preflight_passes_canonical_awaiting_gate_inventory(self):
        result = validate_step1_preflight(_valid_bundle())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual([], result["errors"])

    def test_independent_crawl_run_id_is_accepted(self):
        bundle = _valid_bundle()
        self.assertNotEqual(bundle["run"]["run_id"], bundle["crawl_snapshots"][0]["run_id"])
        self.assertTrue(validate_step1_preflight(bundle)["valid"])

    def test_source_and_current_artifacts_cannot_be_conflated(self):
        bundle = _valid_bundle()
        bundle["source_artifact"] = copy.deepcopy(bundle["artifact"])
        result = validate_step1_preflight(bundle)
        self.assertIn("ERROR_STEP1_ARTIFACT_LINKAGE_INVALID", {error["code"] for error in result["errors"]})

    def test_missing_crawl_evidence_is_rejected(self):
        bundle = _valid_bundle()
        bundle["crawl_snapshots"] = []
        bundle["crawl_artifacts"] = []
        bundle["crawl_snapshot_hashes"] = {}
        bundle["quality_gates"] = [gate for gate in bundle["quality_gates"] if gate["quality_gate_id"] != "qg-step1-crawl-snapshot"]
        result = validate_step1_preflight(bundle)
        self.assertIn("ERROR_STEP1_CRAWL_EVIDENCE_INVALID", {error["code"] for error in result["errors"]})

    def test_changed_inventory_artifact_hash_is_rejected(self):
        bundle = _valid_bundle()
        bundle["artifact"]["content_sha256"] = "f" * 64
        result = validate_step1_preflight(bundle)
        self.assertIn("ERROR_STEP1_ARTIFACT_HASH_MISMATCH", {error["code"] for error in result["errors"]})

    def test_wrong_deployment_is_rejected(self):
        inventory = _load_json("positive-inventory.json")
        inventory["deployment_id"] = "dep-unknown-market"
        result = validate_step1_preflight(_valid_bundle(inventory))
        self.assertIn("ERROR_STEP1_DEPLOYMENT_INVALID", {error["code"] for error in result["errors"]})

    def test_resource_404_requires_revision_bound_waiver(self):
        bundle = _valid_bundle()
        snapshot = bundle["crawl_snapshots"][0]
        snapshot["status"] = "blocked"
        snapshot["findings"]["status_4xx"] = 1
        snapshot["findings"]["resource_4xx"] = 1
        snapshot["policy_disposition"] = {
            "policy_id": "heartweb-crawl-disposition",
            "policy_version": "1.0.0",
            "step_id": "1",
            "result": "blocked",
            "advisory_findings": [],
            "waiver_required_findings": [{
                "finding_key": "resource_4xx",
                "count": 1,
                "allowed_count": 0,
                "failure_code": "ERROR_CRAWL_RESOURCE_4XX",
                "disposition": "waiver_required",
            }],
            "blocking_findings": [],
            "waived_findings": [],
            "waiver_ids": [],
        }
        snapshot["error"] = {
            "code": "ERROR_CRAWL_RESOURCE_4XX",
            "message": "One missing image resource requires an explicit Step 1 waiver.",
            "remediation": "Fix the resource or provide a current revision-bound waiver.",
        }
        blocked = validate_step1_preflight(bundle)
        self.assertFalse(blocked["valid"])

        crawl_artifact = bundle["crawl_artifacts"][0]
        waiver = {
            "waiver_id": "waiver-resource-0001",
            "tenant_id": "tenant-heartweb",
            "project_id": bundle["project"]["project_id"],
            "quality_gate_id": "qg-step1-crawl-snapshot",
            "artifact_id": crawl_artifact["artifact_id"],
            "artifact_sha256": crawl_artifact["content_sha256"],
            "policy_id": "heartweb-crawl-disposition",
            "policy_version": "1.0.0",
            "step_ids": ["1"],
            "finding_keys": ["resource_4xx"],
            "reason": "The missing image is unrelated to topic discovery and remains blocking before production.",
            "approver_id": "reviewer-raphael",
            "approved_at": "2026-08-19T12:03:00Z",
            "expires_at": "2026-08-20T12:03:00Z",
        }
        bundle["waivers"] = [waiver]
        crawl_gate = next(gate for gate in bundle["quality_gates"] if gate["quality_gate_id"] == "qg-step1-crawl-snapshot")
        crawl_gate["waiver_ids"] = [waiver["waiver_id"]]
        passed = validate_step1_preflight(bundle)
        self.assertTrue(passed["valid"], passed["errors"])

    def test_too_few_clusters_is_rejected(self):
        inventory = _load_json("positive-inventory.json")
        inventory["pillars"][0]["cluster_candidates"] = inventory["pillars"][0]["cluster_candidates"][:7]
        result = validate_step1_preflight(_valid_bundle(inventory))
        self.assertIn("ERROR_STEP1_INVENTORY_INVALID", {error["code"] for error in result["errors"]})

    def test_premature_completion_is_rejected(self):
        bundle = _valid_bundle()
        bundle["run"]["status"] = "completed"
        bundle["transition"]["operation"] = "complete"
        result = validate_step1_preflight(bundle)
        self.assertIn("ERROR_STEP1_TRANSITION_INVALID", {error["code"] for error in result["errors"]})

    def test_noncanonical_inventory_bytes_are_rejected(self):
        bundle = _valid_bundle()
        bundle["inventory_bytes"] = json.dumps(json.loads(bundle["inventory_bytes"]), indent=2)
        result = validate_step1_preflight(bundle)
        self.assertIn("ERROR_STEP1_INVENTORY_NOT_CANONICAL", {error["code"] for error in result["errors"]})

    def test_prompt_created_gate1_approval_is_rejected(self):
        bundle = _valid_bundle()
        bundle["approval"] = copy.deepcopy(bundle["gate0_approval"])
        bundle["approval"].update(
            {
                "approval_id": "approval-gate1-invalid",
                "run_id": bundle["run"]["run_id"],
                "gate_id": "GATE-1",
                "artifact_id": bundle["artifact"]["artifact_id"],
                "artifact_sha256": bundle["artifact"]["content_sha256"],
            }
        )
        result = validate_step1_preflight(bundle)
        self.assertIn("ERROR_GATE1_APPROVAL_INVALID", {error["code"] for error in result["errors"]})

    def test_errors_are_deduplicated_sorted_and_actionable(self):
        bundle = _valid_bundle()
        bundle["crawl_snapshots"] = []
        bundle["crawl_artifacts"] = []
        bundle["crawl_snapshot_hashes"] = {}
        inventory = json.loads(bundle["inventory_bytes"])
        inventory["deployment_id"] = "dep-unknown-market"
        bundle = _valid_bundle(inventory)
        bundle["crawl_snapshots"] = []
        bundle["crawl_artifacts"] = []
        bundle["crawl_snapshot_hashes"] = {}
        result = validate_step1_preflight(bundle)
        keys = [(error["code"], tuple(str(item) for item in error["path"]), error["message"]) for error in result["errors"]]
        self.assertEqual(sorted(set(keys)), keys)
        self.assertTrue(all(error["remediation"] for error in result["errors"]))

    def test_cli_accepts_persisted_canonical_file(self):
        bundle = _valid_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = root / "bundle.json"
            storage_root = root / "storage"
            inventory_path = storage_root / bundle["artifact"]["storage_key"]
            bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
            inventory_path.parent.mkdir(parents=True)
            inventory_path.write_text(bundle["inventory_bytes"], encoding="ascii")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "services.step1_preflight.validator",
                    "--bundle",
                    str(bundle_path),
                    "--inventory",
                    str(inventory_path),
                    "--storage-root",
                    str(storage_root),
                    "--json-out",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(json.loads(completed.stdout)["valid"])

    def test_cli_rejects_persisted_byte_mismatch(self):
        bundle = _valid_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = root / "bundle.json"
            storage_root = root / "storage"
            inventory_path = storage_root / bundle["artifact"]["storage_key"]
            bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
            inventory_path.parent.mkdir(parents=True)
            inventory_path.write_text(bundle["inventory_bytes"] + "\n", encoding="ascii")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "services.step1_preflight.validator",
                    "--bundle",
                    str(bundle_path),
                    "--inventory",
                    str(inventory_path),
                    "--storage-root",
                    str(storage_root),
                    "--json-out",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, completed.returncode)
            result = json.loads(completed.stdout)
            self.assertIn("ERROR_STEP1_STORED_ARTIFACT_MISMATCH", {error["code"] for error in result["errors"]})

    def test_persisted_artifact_rejects_same_name_copy_outside_storage_root(self):
        bundle = _valid_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            storage_root = root / "storage"
            canonical_path = storage_root / bundle["artifact"]["storage_key"]
            copied_path = root / "copied" / canonical_path.name
            bundle_path = root / "bundle.json"
            canonical_path.parent.mkdir(parents=True)
            copied_path.parent.mkdir()
            canonical_path.write_text(bundle["inventory_bytes"], encoding="ascii")
            copied_path.write_text(bundle["inventory_bytes"], encoding="ascii")
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

            result = validate_step1_files(bundle_path, copied_path, storage_root=storage_root)

            self.assertFalse(result["valid"])
            self.assertIn("ERROR_STEP1_STORED_ARTIFACT_MISMATCH", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
