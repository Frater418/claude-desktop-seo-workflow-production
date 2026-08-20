"""Deterministic Step 1 V2 submission preflight.

Autor: Raphael Rechberger
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path, PureWindowsPath

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from services.domain_contract.validator import validate_project
from services.quality_gate_registry import evaluate_gate_runs, load_registry
from services.quality_gate_runner.disposition import evaluate_crawl_disposition


JSONSCHEMA_VERSION = "4.26.0"
RUNTIME_SCHEMA_NAMES = (
    "run-envelope.schema.json",
    "artifact-record.schema.json",
    "approval-record.schema.json",
    "quality-gate-run.schema.json",
    "evidence-record.schema.json",
    "transition-command.schema.json",
    "waiver-record.schema.json",
)

REMEDIATIONS = {
    "ERROR_GATE0_RELEASE_INVALID": "Restore the current released Gate 0 quality run and approval bound to the Step 0 artifact.",
    "ERROR_GATE1_APPROVAL_INVALID": "Remove prompt-created approval data and obtain external Gate 1 approval after submission.",
    "ERROR_STEP1_ARTIFACT_HASH_MISMATCH": "Rebuild the Step 1 artifact, run and transition hashes from the exact canonical inventory bytes.",
    "ERROR_STEP1_ARTIFACT_LINKAGE_INVALID": "Bind the distinct immutable Step 0 source artifact as a parent of the Step 1 artifact.",
    "ERROR_STEP1_CRAWL_EVIDENCE_INVALID": "Provide passed Screaming Frog evidence, artifact and quality-gate records for the current deployment.",
    "ERROR_STEP1_DEPLOYMENT_INVALID": "Use a deployment declared by the validated Project V2 contract.",
    "ERROR_STEP1_EVIDENCE_REFERENCE_INVALID": "Add the missing evidence record or remove the unresolvable evidence reference.",
    "ERROR_STEP1_INVENTORY_INVALID": "Correct the inventory to the closed Step 1 output contract.",
    "ERROR_STEP1_INVENTORY_NOT_CANONICAL": "Serialize inventory JSON with sorted keys, compact separators and ASCII escaping before hashing.",
    "ERROR_STEP1_QUALITY_GATE_INVALID": "Run the required quality gate and bind it to the correct artifact ID and SHA-256.",
    "ERROR_STEP1_SITE_APPLICABILITY_INVALID": "Declare an existing site with crawl evidence or a non-existing site with an explicit no-crawl decision.",
    "ERROR_STEP1_STORED_ARTIFACT_MISMATCH": "Use the canonical file named by the artifact storage key and rebuild every dependent hash from those exact bytes.",
    "ERROR_STEP1_TRANSITION_INVALID": "Submit only an awaiting_gate Step 1 transition bound to the current run, input and output hashes.",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validators(root: Path) -> dict[str, Draft202012Validator]:
    runtime_dir = root / "standards" / "runtime"
    schemas = {name: _load_json(runtime_dir / name) for name in RUNTIME_SCHEMA_NAMES}
    inventory = _load_json(root / "standards" / "outputs" / "step-1-topic-inventory.schema.json")
    crawl = _load_json(root / "standards" / "quality" / "screaming-frog-crawl.schema.json")
    registry = Registry()
    for schema in (*schemas.values(), inventory, crawl):
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    checker = FormatChecker()
    return {
        "inventory": Draft202012Validator(inventory, registry=registry, format_checker=checker),
        "run": Draft202012Validator(schemas["run-envelope.schema.json"], registry=registry, format_checker=checker),
        "artifact": Draft202012Validator(schemas["artifact-record.schema.json"], registry=registry, format_checker=checker),
        "approval": Draft202012Validator(schemas["approval-record.schema.json"], registry=registry, format_checker=checker),
        "quality_gate": Draft202012Validator(schemas["quality-gate-run.schema.json"], registry=registry, format_checker=checker),
        "evidence": Draft202012Validator(schemas["evidence-record.schema.json"], registry=registry, format_checker=checker),
        "transition": Draft202012Validator(schemas["transition-command.schema.json"], registry=registry, format_checker=checker),
        "waiver": Draft202012Validator(schemas["waiver-record.schema.json"], registry=registry, format_checker=checker),
        "crawl": Draft202012Validator(crawl, registry=registry, format_checker=checker),
    }


def _error(code: str, message: str, path: list[str | int], remediation: str | None = None) -> dict:
    return {
        "code": code,
        "message": message,
        "path": path,
        "remediation": remediation or REMEDIATIONS.get(code, "Correct the identified Step 1 contract field and rerun preflight."),
    }


def _sorted_unique(errors: list[dict]) -> list[dict]:
    unique: dict[tuple, dict] = {}
    for error in errors:
        key = (error["code"], tuple(str(item) for item in error["path"]), error["message"])
        unique[key] = error
    return [unique[key] for key in sorted(unique)]


def _schema_errors(validator: Draft202012Validator, value, code: str, path: list[str | int]) -> list[dict]:
    return [
        _error(code, error.message, path + list(error.absolute_path))
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    ]


def _canonical_inventory(raw: str) -> tuple[dict | None, bytes | None, list[dict]]:
    try:
        source = raw.encode("ascii")
        inventory = json.loads(source)
    except (UnicodeEncodeError, json.JSONDecodeError):
        return None, None, [_error("ERROR_STEP1_INVENTORY_INVALID", "Inventory source must be ASCII JSON.", ["inventory_bytes"])]
    if not isinstance(inventory, dict):
        return None, None, [_error("ERROR_STEP1_INVENTORY_INVALID", "Inventory source must contain a JSON object.", ["inventory_bytes"])]
    canonical = json.dumps(inventory, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
    errors = [] if source == canonical else [
        _error("ERROR_STEP1_INVENTORY_NOT_CANONICAL", "Inventory source is not canonical JSON.", ["inventory_bytes"])
    ]
    return inventory, source, errors


def _bound(value: dict | None, fields: dict) -> bool:
    return isinstance(value, dict) and all(value.get(key) == expected for key, expected in fields.items())


def _matching(records: list[dict], fields: dict) -> dict | None:
    return next((record for record in records if _bound(record, fields)), None)


def _timestamp(value: str | None) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _all_evidence_ids(inventory: dict) -> set[str]:
    identifiers = set(
        inventory["source_evidence_ids"]
        + inventory["competitor_evidence_ids"]
        + inventory["existing_url_evidence_ids"]
        + inventory["crawl_snapshot_evidence_ids"]
    )
    for pillar in inventory["pillars"]:
        identifiers.update(pillar["source_evidence_ids"])
        for cluster in pillar["cluster_candidates"]:
            identifiers.update(cluster["source_evidence_ids"])
    for hypothesis in inventory["hypotheses"]:
        identifiers.update(hypothesis["evidence_ids"])
    for gap in inventory["gaps"]:
        identifiers.update(gap.get("evidence_ids", []))
    for decision in inventory["decision_records"]:
        identifiers.update(decision["evidence_ids"])
    return identifiers


def _structural_errors(bundle: dict, validators: dict[str, Draft202012Validator]) -> tuple[dict | None, bytes | None, list[dict]]:
    errors: list[dict] = []
    raw = bundle.get("inventory_bytes")
    inventory, source, canonical_errors = _canonical_inventory(raw) if isinstance(raw, str) else (
        None,
        None,
        [_error("ERROR_STEP1_INVENTORY_INVALID", "Inventory source is required.", ["inventory_bytes"])],
    )
    errors.extend(canonical_errors)
    if inventory is not None:
        errors.extend(_schema_errors(validators["inventory"], inventory, "ERROR_STEP1_INVENTORY_INVALID", ["inventory"]))

    singles = (
        ("run", "run", "ERROR_STEP1_RUN_INVALID"),
        ("source_artifact", "artifact", "ERROR_STEP1_ARTIFACT_LINKAGE_INVALID"),
        ("artifact", "artifact", "ERROR_STEP1_ARTIFACT_HASH_MISMATCH"),
        ("gate0_approval", "approval", "ERROR_GATE0_RELEASE_INVALID"),
        ("transition", "transition", "ERROR_STEP1_TRANSITION_INVALID"),
    )
    for key, validator_name, code in singles:
        errors.extend(_schema_errors(validators[validator_name], bundle.get(key), code, [key]))

    collections = (
        ("quality_gates", "quality_gate", "ERROR_STEP1_QUALITY_GATE_INVALID"),
        ("evidence_records", "evidence", "ERROR_STEP1_EVIDENCE_REFERENCE_INVALID"),
        ("crawl_snapshots", "crawl", "ERROR_STEP1_CRAWL_EVIDENCE_INVALID"),
        ("crawl_artifacts", "artifact", "ERROR_STEP1_CRAWL_EVIDENCE_INVALID"),
        ("waivers", "waiver", "ERROR_STEP1_CRAWL_EVIDENCE_INVALID"),
    )
    for key, validator_name, code in collections:
        records = bundle.get(key)
        if not isinstance(records, list):
            errors.append(_error(code, f"{key} must be an array.", [key]))
            continue
        for index, record in enumerate(records):
            errors.extend(_schema_errors(validators[validator_name], record, code, [key, index]))

    if bundle.get("approval") is not None:
        errors.extend(_schema_errors(validators["approval"], bundle["approval"], "ERROR_GATE1_APPROVAL_INVALID", ["approval"]))
    if not isinstance(bundle.get("crawl_snapshot_hashes"), dict):
        errors.append(_error("ERROR_STEP1_CRAWL_EVIDENCE_INVALID", "crawl_snapshot_hashes must be an object.", ["crawl_snapshot_hashes"]))
    if not isinstance(bundle.get("gate_context"), dict):
        errors.append(_error("ERROR_GATE_APPLICABILITY_UNDECIDED", "gate_context must explicitly declare applicability and configured-source decisions.", ["gate_context"]))
    return inventory, source, errors


def validate_step1_preflight(bundle: dict, root: Path | None = None) -> dict:
    """Validate one Step 1 awaiting-gate submission and return all errors."""
    if not isinstance(bundle, dict):
        errors = [_error("ERROR_STEP1_INPUT_INVALID", "Preflight input must be an object.", [])]
        return {"valid": False, "errors": errors}

    root = root or _root()
    validators = _validators(root)
    inventory, source, errors = _structural_errors(bundle, validators)
    if version("jsonschema") != JSONSCHEMA_VERSION:
        errors.append(_error("ERROR_JSONSCHEMA_VERSION", f"Step 1 requires jsonschema {JSONSCHEMA_VERSION}.", ["jsonschema"]))

    project = bundle.get("project")
    if not isinstance(project, dict):
        errors.append(_error("ERROR_DOMAIN_CONTRACT_INVALID", "Project V2 is required.", ["project"]))
    else:
        for item in validate_project(project, root=root)["errors"]:
            errors.append(_error(item["code"], item["message"], item["path"], item.get("remediation")))

    if errors or inventory is None or source is None or not isinstance(project, dict):
        final = _sorted_unique(errors)
        return {"valid": False, "errors": final}

    run = bundle["run"]
    source_artifact = bundle["source_artifact"]
    artifact = bundle["artifact"]
    transition = bundle["transition"]
    quality_gates = bundle["quality_gates"]
    evidence_records = bundle["evidence_records"]
    crawl_snapshots = bundle["crawl_snapshots"]
    crawl_artifacts = bundle["crawl_artifacts"]
    waivers = bundle["waivers"]
    gate_context = bundle["gate_context"]
    crawl_snapshot_hashes = bundle["crawl_snapshot_hashes"]
    tenant_id = project["tenant"]["tenant_id"]
    project_id = project["project_id"]
    inventory_hash = hashlib.sha256(source).hexdigest()

    if not _bound(run, {"tenant_id": tenant_id, "project_id": project_id, "step_id": "1", "gate_id": "GATE-1"}):
        errors.append(_error("ERROR_STEP1_RUN_INVALID", "Run must bind the current tenant, project, Step 1 and GATE-1.", ["run"]))
    if not _bound(inventory, {"artifact_id": artifact["artifact_id"], "run_id": run["run_id"], "project_id": project_id}):
        errors.append(_error("ERROR_STEP1_IDENTITY_MISMATCH", "Inventory must bind the current artifact, run and project.", ["inventory"]))

    deployment_ids = {deployment["deployment_id"] for deployment in project["market_deployments"]}
    if inventory["deployment_id"] not in deployment_ids:
        errors.append(_error("ERROR_STEP1_DEPLOYMENT_INVALID", "Inventory deployment is not declared by Project V2.", ["inventory", "deployment_id"]))

    if source_artifact["artifact_id"] == artifact["artifact_id"] or not _bound(
        source_artifact,
        {"tenant_id": tenant_id, "project_id": project_id, "step_id": "0"},
    ):
        errors.append(_error("ERROR_STEP1_ARTIFACT_LINKAGE_INVALID", "Source artifact must be a distinct immutable Step 0 artifact.", ["source_artifact"]))
    if not _bound(
        artifact,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run["run_id"],
            "step_id": "1",
            "revision": run["revision"],
            "content_sha256": inventory_hash,
        },
    ) or source_artifact["artifact_id"] not in artifact["parent_artifact_ids"]:
        errors.append(_error("ERROR_STEP1_ARTIFACT_HASH_MISMATCH", "Step 1 artifact must bind canonical bytes, run revision and Step 0 parent.", ["artifact"]))
    if run.get("output_hash") != inventory_hash or transition.get("output_hash") != inventory_hash:
        errors.append(_error("ERROR_STEP1_ARTIFACT_HASH_MISMATCH", "Run and transition output hashes must bind canonical inventory bytes.", ["run", "output_hash"]))

    gate0_approval = bundle["gate0_approval"]
    as_of = _timestamp(bundle.get("as_of"))
    approval_current = (
        as_of is not None
        and _timestamp(gate0_approval.get("decided_at")) is not None
        and _timestamp(gate0_approval.get("expires_at")) is not None
        and _timestamp(gate0_approval["decided_at"]) <= as_of < _timestamp(gate0_approval["expires_at"])
    )
    gate0_quality = _matching(
        quality_gates,
        {
            "quality_gate_id": "qg-domain-contract",
            "human_gate_id": "GATE-0",
            "tenant_id": tenant_id,
            "run_id": source_artifact["run_id"],
            "step_id": "0",
            "artifact_id": source_artifact["artifact_id"],
            "artifact_sha256": source_artifact["content_sha256"],
            "result": "passed",
        },
    )
    predecessor = transition.get("predecessor_release")
    release_bound = _bound(
        predecessor,
        {
            "step_id": "0",
            "gate_id": "GATE-0",
            "status": "released",
            "artifact_id": source_artifact["artifact_id"],
            "artifact_sha256": source_artifact["content_sha256"],
            "artifact_revision": source_artifact["revision"],
        },
    )
    approval_bound = _bound(
        gate0_approval,
        {
            "tenant_id": tenant_id,
            "run_id": source_artifact["run_id"],
            "gate_id": "GATE-0",
            "artifact_id": source_artifact["artifact_id"],
            "artifact_sha256": source_artifact["content_sha256"],
            "artifact_revision": source_artifact["revision"],
            "decision": "approved",
        },
    )
    if (
        gate0_quality is None
        or not release_bound
        or not approval_bound
        or not approval_current
        or gate0_quality["policy_version"] != gate0_approval["policy_version"]
        or run["input_hash"] != source_artifact["content_sha256"]
    ):
        errors.append(_error("ERROR_GATE0_RELEASE_INVALID", "Gate 0 quality run, release, approval and Step 1 input must bind the same source artifact.", ["gate0_approval"]))

    evidence_by_id = {record["evidence_id"]: record for record in evidence_records}
    for evidence_id in sorted(_all_evidence_ids(inventory) - set(evidence_by_id)):
        errors.append(_error("ERROR_STEP1_EVIDENCE_REFERENCE_INVALID", f"Missing evidence record: {evidence_id}", ["inventory", evidence_id]))
    for record in evidence_records:
        if not _bound(record, {"tenant_id": tenant_id, "project_id": project_id}):
            errors.append(_error("ERROR_STEP1_EVIDENCE_REFERENCE_INVALID", "Evidence must bind the current tenant and project.", ["evidence_records", record["evidence_id"]]))

    site = inventory["site_applicability"]
    decision_ids = {decision["decision_id"] for decision in inventory["decision_records"]}
    if site["site_status"] == "non_existing_site":
        if site.get("no_crawl_decision_id") not in decision_ids or inventory["crawl_snapshot_evidence_ids"]:
            errors.append(_error("ERROR_STEP1_SITE_APPLICABILITY_INVALID", "Non-existing site requires a valid no-crawl decision and no crawl references.", ["inventory", "site_applicability"]))
    else:
        for evidence_id in inventory["crawl_snapshot_evidence_ids"]:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                continue
            content_hash = evidence["content_sha256"]
            crawl_artifact = next(
                (
                    item
                    for item in crawl_artifacts
                    if _bound(
                        item,
                        {
                            "tenant_id": tenant_id,
                            "project_id": project_id,
                            "step_id": "1",
                            "content_sha256": content_hash,
                        },
                    )
                ),
                None,
            )
            snapshot = next(
                (
                    item
                    for item in crawl_snapshots
                    if crawl_artifact is not None
                    and _bound(
                        item,
                        {
                            "run_id": crawl_artifact["run_id"],
                            "project_id": project_id,
                            "deployment_id": inventory["deployment_id"],
                        },
                    )
                ),
                None,
            )
            snapshot_hash = crawl_snapshot_hashes.get(snapshot["run_id"]) if snapshot is not None else None
            crawl_gate = _matching(
                quality_gates,
                {
                    "quality_gate_id": "qg-step1-crawl-snapshot",
                    "human_gate_id": "GATE-1",
                    "tenant_id": tenant_id,
                    "run_id": crawl_artifact["run_id"] if crawl_artifact else "",
                    "step_id": "1",
                    "artifact_id": crawl_artifact["artifact_id"] if crawl_artifact else "",
                    "artifact_sha256": content_hash,
                    "result": "passed",
                },
            )
            resolved_disposition = (
                evaluate_crawl_disposition(
                    snapshot["findings"],
                    "1",
                    context={"multilingual": bool(gate_context.get("multilingual", False))},
                    waivers=waivers,
                    artifact=crawl_artifact,
                    as_of=bundle.get("as_of"),
                )
                if snapshot is not None and crawl_artifact is not None
                else None
            )
            if (
                crawl_artifact is None
                or snapshot is None
                or snapshot_hash != content_hash
                or snapshot["limit_hit"]
                or snapshot["url_count"] < 1
                or snapshot["html_url_count"] < 1
                or not snapshot["exports"]
                or crawl_gate is None
                or resolved_disposition is None
                or resolved_disposition["result"] == "blocked"
                or sorted(crawl_gate.get("waiver_ids", [])) != sorted(resolved_disposition["waiver_ids"])
            ):
                errors.append(_error("ERROR_STEP1_CRAWL_EVIDENCE_INVALID", f"Invalid crawl evidence lineage for {evidence_id}.", ["crawl_snapshot_evidence_ids", evidence_id]))
        if not inventory["crawl_snapshot_evidence_ids"]:
            errors.append(_error("ERROR_STEP1_CRAWL_EVIDENCE_INVALID", "Existing site requires at least one crawl evidence reference.", ["crawl_snapshot_evidence_ids"]))

    inventory_gate = _matching(
        quality_gates,
        {
            "quality_gate_id": "qg-domain-contract",
            "human_gate_id": "GATE-1",
            "tenant_id": tenant_id,
            "run_id": run["run_id"],
            "step_id": "1",
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": inventory_hash,
            "result": "passed",
        },
    )
    if inventory_gate is None:
        errors.append(_error("ERROR_STEP1_QUALITY_GATE_INVALID", "Step 1 inventory contract quality gate is missing or stale.", ["quality_gates"]))

    registry_result = evaluate_gate_runs(
        load_registry(root),
        "1",
        "submit_for_gate",
        gate_context,
        tenant_id,
        run["run_id"],
        "GATE-1",
        artifact,
        [source_artifact, *crawl_artifacts],
        quality_gates,
    )
    for gate_error in registry_result["errors"]:
        errors.append(
            _error(
                gate_error["code"],
                f"{gate_error['gate_id']}: {gate_error['message']}",
                ["quality_gates", gate_error["gate_id"]],
                gate_error["remediation"],
            )
        )

    if not _bound(
        transition,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run["run_id"],
            "from_step_id": "0",
            "to_step_id": "1",
            "expected_revision": run["revision"],
            "input_hash": source_artifact["content_sha256"],
            "output_hash": inventory_hash,
            "operation": "submit_for_gate",
        },
    ):
        errors.append(_error("ERROR_STEP1_TRANSITION_INVALID", "Transition must be a current Step 1 submit_for_gate command.", ["transition"]))
    transition_gate = transition.get("quality_gate")
    if inventory_gate is not None and not _bound(
        transition_gate,
        {
            "quality_gate_run_id": inventory_gate["quality_gate_run_id"],
            "result": "passed",
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": inventory_hash,
        },
    ):
        errors.append(_error("ERROR_STEP1_TRANSITION_INVALID", "Transition quality gate must bind the current inventory quality-gate run.", ["transition", "quality_gate"]))
    if run["status"] != "awaiting_gate":
        errors.append(_error("ERROR_STEP1_TRANSITION_INVALID", "Step 1 submission may only set run status awaiting_gate.", ["run", "status"]))
    if bundle.get("approval") is not None:
        errors.append(_error("ERROR_GATE1_APPROVAL_INVALID", "Prompt 1 must not create or embed Gate 1 approval.", ["approval"]))

    final = _sorted_unique(errors)
    return {"valid": not final, "errors": final}


def _canonical_artifact_path(storage_root: Path, storage_key: str) -> Path | None:
    declared = Path(storage_key)
    if not storage_key or declared.is_absolute() or PureWindowsPath(storage_key).is_absolute() or ".." in declared.parts:
        return None
    resolved_root = storage_root.resolve()
    resolved_artifact = (resolved_root / declared).resolve()
    try:
        resolved_artifact.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved_artifact


def validate_step1_files(
    bundle_path: Path,
    inventory_path: Path,
    root: Path | None = None,
    storage_root: Path | None = None,
) -> dict:
    """Validate the persisted inventory bytes and their complete submission bundle."""
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        error = _error("ERROR_STEP1_INPUT_INVALID", f"Invalid bundle file: {exc}", ["bundle"])
        return {"valid": False, "errors": [error]}
    errors: list[dict] = []
    artifact = bundle.get("artifact") if isinstance(bundle, dict) else None
    storage_key = artifact.get("storage_key", "") if isinstance(artifact, dict) else ""
    canonical_path = _canonical_artifact_path(storage_root, storage_key) if storage_root is not None else None
    supplied_path = inventory_path.resolve()
    if canonical_path is None or supplied_path != canonical_path:
        errors.append(
            _error(
                "ERROR_STEP1_STORED_ARTIFACT_MISMATCH",
                "Inventory path must equal the canonical artifact storage-key location beneath the controlled storage root.",
                ["artifact", "storage_key"],
            )
        )
        return {"valid": False, "errors": _sorted_unique(errors)}
    try:
        stored_bytes = canonical_path.read_bytes()
        stored_text = stored_bytes.decode("ascii")
    except (FileNotFoundError, UnicodeDecodeError) as exc:
        error = _error("ERROR_STEP1_STORED_ARTIFACT_MISMATCH", f"Invalid canonical inventory file: {exc}", ["inventory_file"])
        return {"valid": False, "errors": [error]}
    if bundle.get("inventory_bytes") != stored_text:
        errors.append(
            _error(
                "ERROR_STEP1_STORED_ARTIFACT_MISMATCH",
                "Bundle inventory bytes differ from the persisted canonical file.",
                ["inventory_bytes"],
            )
        )
    if isinstance(artifact, dict) and artifact.get("content_sha256") != hashlib.sha256(stored_bytes).hexdigest():
        errors.append(
            _error(
                "ERROR_STEP1_STORED_ARTIFACT_MISMATCH",
                "Persisted canonical file hash differs from the artifact record.",
                ["artifact", "content_sha256"],
            )
        )

    bundle["inventory_bytes"] = stored_text
    result = validate_step1_preflight(bundle, root=root)
    result["errors"] = _sorted_unique(errors + result["errors"])
    result["valid"] = not result["errors"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Heartweb Step 1 persisted-artifact preflight")
    parser.add_argument("--bundle", required=True, help="Path to the Step 1 submission bundle JSON")
    parser.add_argument("--inventory", required=True, help="Path to the canonical Step 1 inventory JSON")
    parser.add_argument("--storage-root", required=True, help="Controlled root that contains artifact storage keys")
    parser.add_argument("--json-out", action="store_true")
    args = parser.parse_args()
    result = validate_step1_files(Path(args.bundle), Path(args.inventory), storage_root=Path(args.storage_root))
    if args.json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["valid"]:
        print("[BESTANDEN] Step 1 persisted-artifact preflight")
    else:
        print(f"[NICHT BESTANDEN] {len(result['errors'])} Step-1-Fehler", file=sys.stderr)
        for error in result["errors"]:
            print(f"  - {error['code']}: {error['message']}", file=sys.stderr)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
