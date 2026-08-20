from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PureWindowsPath

from jsonschema import Draft202012Validator, FormatChecker

from services.quality_gate_runner.disposition import evaluate_crawl_disposition, load_policy


IDENTITY_PATTERNS = {
    "tenant_id": re.compile(r"^tenant-[a-z0-9][a-z0-9-]{2,63}$"),
    "project_id": re.compile(r"^project-[a-z0-9][a-z0-9-]{2,63}$"),
    "run_id": re.compile(r"^run-[a-z0-9][a-z0-9-]{5,63}$"),
}


class WaiverResolutionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _path_error(message: str) -> WaiverResolutionError:
    return WaiverResolutionError("ERROR_CRAWL_WAIVER_EVIDENCE_INVALID", message)


def _resolve_controlled_root(value: str) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise _path_error(f"Controlled resolution root does not exist: {value}")
    return root


def _validate_identities(tenant_id: str, project_id: str, run_id: str) -> None:
    for field, value in (("tenant_id", tenant_id), ("project_id", project_id), ("run_id", run_id)):
        if not IDENTITY_PATTERNS[field].fullmatch(value):
            raise _path_error(f"Invalid {field}: {value}")


def _resolve_controlled_input(root: Path, value: str, option: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or PureWindowsPath(value).is_absolute() or ".." in candidate.parts:
        raise _path_error(f"{option} must be a relative path beneath the controlled resolution root.")
    try:
        resolved = (root / candidate).resolve(strict=True)
    except FileNotFoundError as exc:
        raise _path_error(f"{option} does not exist beneath the controlled resolution root.") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise _path_error(f"{option} escapes the controlled resolution root.") from exc
    if not resolved.is_file():
        raise _path_error(f"{option} must resolve to a file beneath the controlled resolution root.")
    return resolved


def _derive_resolution_output(root: Path, tenant_id: str, project_id: str, run_id: str) -> Path:
    output = (
        root / "tenants" / tenant_id / "projects" / project_id / "runs" / run_id / "waiver-resolution.json"
    ).resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise _path_error("Derived waiver resolution output escapes the controlled resolution root.") from exc
    return output


def _validate_cli_identity(
    crawl_evidence: dict,
    crawl_artifact: dict,
    waiver: dict,
    tenant_id: str,
    project_id: str,
    run_id: str,
) -> None:
    expected = {"tenant_id": tenant_id, "project_id": project_id, "run_id": run_id}
    values = (
        (crawl_evidence, ("project_id", "run_id")),
        (crawl_artifact, ("tenant_id", "project_id", "run_id")),
        (waiver, ("tenant_id", "project_id")),
    )
    if any(source.get(field) != expected[field] for source, fields in values for field in fields):
        raise _path_error("Crawl evidence, artifact and waiver identities must match the controlled output scope.")


def _write_resolution_output(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(result, ensure_ascii=True, indent=2) + "\n")
    except FileExistsError as exc:
        raise _path_error(f"Derived waiver resolution output already exists: {path}") from exc


def _validate_contract(value: dict, schema_name: str, code: str) -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / "standards" / schema_name).read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    if errors:
        raise WaiverResolutionError(code, f"Contract validation failed: {errors[0].message}")


def resolve_post_crawl_waiver(
    crawl_evidence: dict,
    raw_evidence_hash: str,
    crawl_artifact: dict,
    waiver: dict,
    evaluation_at: str,
) -> dict:
    _validate_contract(crawl_evidence, "quality/screaming-frog-crawl.schema.json", "ERROR_CRAWL_WAIVER_EVIDENCE_INVALID")
    _validate_contract(waiver, "runtime/waiver-record.schema.json", "ERROR_CRAWL_WAIVER_INVALID")
    if crawl_artifact.get("content_sha256") != raw_evidence_hash:
        raise WaiverResolutionError("ERROR_CRAWL_WAIVER_EVIDENCE_HASH_MISMATCH", "Immutable crawl evidence hash does not bind the crawl artifact.")
    if crawl_evidence.get("run_id") != crawl_artifact.get("run_id") or crawl_evidence.get("project_id") != crawl_artifact.get("project_id"):
        raise WaiverResolutionError("ERROR_CRAWL_WAIVER_ARTIFACT_BINDING_INVALID", "Crawl evidence does not bind the supplied crawl artifact.")
    policy = load_policy()
    disposition = evaluate_crawl_disposition(
        crawl_evidence.get("findings", {}),
        "1",
        policy=policy,
        waivers=[waiver],
        artifact=crawl_artifact,
        as_of=evaluation_at,
    )
    if disposition["result"] == "blocked":
        raise WaiverResolutionError("ERROR_CRAWL_WAIVER_DISALLOWED", "The waiver is expired, mismatched, or not permitted by the active crawl policy.")
    suffix = hashlib.sha256(f"{raw_evidence_hash}:{waiver['waiver_id']}".encode("ascii")).hexdigest()[:16]
    quality_gate_run = {
        "quality_gate_run_id": f"qgr-waiver-{suffix}",
        "quality_gate_id": "qg-step1-crawl-snapshot",
        "human_gate_id": "GATE-1",
        "tenant_id": crawl_artifact["tenant_id"],
        "run_id": crawl_artifact["run_id"],
        "step_id": "1",
        "artifact_id": crawl_artifact["artifact_id"],
        "artifact_sha256": raw_evidence_hash,
        "registry_version": "1.1.0",
        "policy_version": policy["version"],
        "result": "passed",
        "evidence": {
            "crawl_manifest": raw_evidence_hash,
            "start_url": str(crawl_evidence.get("start_url", "resolved-post-crawl")),
            "tool_version": str(crawl_evidence.get("schema_version", "1.1.0")),
            "export_hashes": raw_evidence_hash,
            "url_count": str(crawl_evidence.get("url_count", 0)),
            "issues_overview": "resolved-by-revision-bound-waiver",
        },
        "waiver_ids": disposition["waiver_ids"],
        "findings": [],
        "checked_at": evaluation_at,
        "checker_version": "heartweb-crawl-waiver-resolution-1.0.0",
    }
    return {"resolved_disposition": disposition, "quality_gate_run": quality_gate_run}


def main() -> int:
    parser = argparse.ArgumentParser(description="Heartweb immutable post-crawl waiver resolution")
    parser.add_argument("--resolution-root", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--crawl-evidence", required=True)
    parser.add_argument("--crawl-artifact", required=True)
    parser.add_argument("--waiver", required=True)
    parser.add_argument("--evaluation-at", required=True)
    args = parser.parse_args()
    try:
        root = _resolve_controlled_root(args.resolution_root)
        _validate_identities(args.tenant_id, args.project_id, args.run_id)
        evidence_path = _resolve_controlled_input(root, args.crawl_evidence, "--crawl-evidence")
        artifact_path = _resolve_controlled_input(root, args.crawl_artifact, "--crawl-artifact")
        waiver_path = _resolve_controlled_input(root, args.waiver, "--waiver")
        output_path = _derive_resolution_output(root, args.tenant_id, args.project_id, args.run_id)
        if output_path in {evidence_path, artifact_path, waiver_path}:
            raise _path_error("Derived waiver resolution output must be distinct from every input file.")
        if output_path.exists():
            raise _path_error(f"Derived waiver resolution output already exists: {output_path}")
        raw_evidence = evidence_path.read_bytes()
        crawl_evidence = json.loads(raw_evidence)
        crawl_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        waiver = json.loads(waiver_path.read_text(encoding="utf-8"))
        _validate_cli_identity(crawl_evidence, crawl_artifact, waiver, args.tenant_id, args.project_id, args.run_id)
        result = resolve_post_crawl_waiver(
            crawl_evidence,
            hashlib.sha256(raw_evidence).hexdigest(),
            crawl_artifact,
            waiver,
            args.evaluation_at,
        )
        _write_resolution_output(output_path, result)
    except WaiverResolutionError as exc:
        print(json.dumps({"status": "failed", "error": {"code": exc.code, "message": str(exc)}}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
