"""Fail-fast Screaming Frog CLI adapter for Heartweb quality gates.

Autor: Raphael Rechberger
Version: 1.1.0
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Callable, Iterable
from urllib.parse import urlparse

from services.quality_gate_runner.disposition import evaluate_crawl_disposition


DEFAULT_EXPORT_TABS = (
    "Internal:All",
    "Response Codes:All",
    "Page Titles:All",
    "Meta Description:All",
    "H1:All",
    "H2:All",
    "Canonicals:All",
    "Hreflang:All",
    "Structured Data:All",
    "Links:All",
    "Security:All",
)

DEFAULT_REPORTS = (
    "Crawl Overview",
    "Issues Overview",
    "Redirects:Redirect Chains",
    "Structured Data:Validation Errors & Warnings",
)

REQUIRED_OPTIONS = (
    "--crawl",
    "--headless",
    "--output-folder",
    "--export-format",
    "--overwrite",
    "--export-tabs",
    "--save-report",
)

KNOWN_WINDOWS_PATHS = (
    Path("C:/Program Files (x86)/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe"),
    Path("C:/Program Files/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe"),
)

ID_PATTERNS = {
    "tenant_id": re.compile(r"^tenant-[a-z0-9][a-z0-9-]{2,63}$"),
    "run_id": re.compile(r"^run-[a-z0-9][a-z0-9-]{5,63}$"),
    "project_id": re.compile(r"^project-[a-z0-9][a-z0-9-]{2,63}$"),
    "deployment_id": re.compile(r"^dep-[a-z0-9][a-z0-9-]{2,63}$"),
}

ASSET_EXTENSIONS = {
    ".avif", ".css", ".gif", ".ico", ".jpeg", ".jpg", ".js", ".json", ".pdf",
    ".png", ".svg", ".webp", ".woff", ".woff2", ".xml", ".zip",
}


class QualityGateError(RuntimeError):
    """Structured, operator-actionable quality gate error."""

    def __init__(self, code: str, message: str, remediation: str):
        super().__init__(message)
        self.code = code
        self.message = message
        self.remediation = remediation

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
        }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_absolute_path(path: Path) -> bool:
    return path.is_absolute() or PureWindowsPath(str(path)).is_absolute()


def resolve_binary(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env_value = os.environ.get("SCREAMING_FROG_CLI")
    if env_value:
        candidates.append(Path(env_value))
    which_value = shutil.which("ScreamingFrogSEOSpiderCli.exe") or shutil.which("screamingfrogseospider")
    if which_value:
        candidates.append(Path(which_value))
    candidates.extend(KNOWN_WINDOWS_PATHS)

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise QualityGateError(
        "ERROR_SCREAMING_FROG_BINARY_MISSING",
        "Screaming Frog CLI binary was not found in an explicit path, environment variable, PATH or known installation path.",
        "Install Screaming Frog SEO Spider or set SCREAMING_FROG_CLI to the verified CLI binary and rerun preflight.",
    )


def parse_capabilities(help_text: str, export_text: str, report_text: str) -> dict:
    missing_options = [option for option in REQUIRED_OPTIONS if option not in help_text]
    missing_export_tabs = [tab for tab in DEFAULT_EXPORT_TABS if tab not in export_text]
    required_reports = ("Crawl Overview", "Issues Overview", "Redirects:Redirect Chains")
    missing_reports = [report for report in required_reports if report not in report_text]
    payload = "\n".join((help_text, export_text, report_text)).encode("utf-8", errors="replace")
    return {
        "valid": not missing_options and not missing_export_tabs and not missing_reports,
        "missing_options": missing_options,
        "missing_export_tabs": missing_export_tabs,
        "missing_reports": missing_reports,
        "capability_hash": _sha256_bytes(payload),
    }


def _run_help(binary: Path, topic: str | None, timeout_seconds: int) -> str:
    command = [str(binary), "--help"]
    if topic:
        command.append(topic)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_PREFLIGHT_TIMEOUT",
            f"Screaming Frog preflight timed out after {timeout_seconds} seconds.",
            "Close stale SEO Spider processes, verify the local installation and rerun preflight.",
        ) from exc
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_PREFLIGHT_FAILED",
            f"Screaming Frog preflight returned exit code {completed.returncode}.",
            "Run the CLI help command manually, repair the installation or licence state, and rerun preflight.",
        )
    return output


def preflight(binary: str | None = None, timeout_seconds: int = 60) -> dict:
    binary_path = resolve_binary(binary)
    help_text = _run_help(binary_path, None, timeout_seconds)
    export_text = _run_help(binary_path, "export-tabs", timeout_seconds)
    report_text = _run_help(binary_path, "save-report", timeout_seconds)
    capabilities = parse_capabilities(help_text, export_text, report_text)
    if not capabilities["valid"]:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_CAPABILITY_MISMATCH",
            "The installed Screaming Frog CLI does not expose every required Heartweb crawl capability.",
            "Upgrade or reconfigure Screaming Frog and verify the required options, export tabs and reports before running a crawl.",
        )
    return {
        "valid": True,
        "binary_path": str(binary_path),
        **capabilities,
    }


def _validate_url(start_url: str) -> None:
    parsed = urlparse(start_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_URL_INVALID",
            f"Start URL must be an absolute HTTP or HTTPS URL: {start_url}",
            "Provide the verified canonical site start URL including scheme and hostname.",
        )


def resolve_evidence_output_folder(evidence_root: Path, tenant_id: str, project_id: str, run_id: str) -> Path:
    for field, value in (("tenant_id", tenant_id), ("project_id", project_id), ("run_id", run_id)):
        if not ID_PATTERNS[field].fullmatch(value):
            raise QualityGateError(
                "ERROR_SCREAMING_FROG_ID_INVALID",
                f"Invalid {field}: {value}",
                "Use the stable Heartweb identifier format required by the quality evidence schema.",
            )
    root = evidence_root.resolve()
    if not root.is_dir():
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_OUTPUT_PATH_INVALID",
            f"Evidence root does not exist: {evidence_root}",
            "Create the controlled evidence root before starting a crawl.",
        )
    output = (root / "tenants" / tenant_id / "projects" / project_id / "runs" / run_id / "screaming-frog").resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_OUTPUT_PATH_INVALID",
            "Derived crawl output escapes the controlled evidence root.",
            "Remove the escaping path or symlink and rerun with the controlled evidence root.",
        ) from exc
    return output


def build_crawl_command(
    binary: Path,
    start_url: str,
    output_folder: Path,
    config_path: Path | None = None,
    overwrite: bool = False,
    export_tabs: Iterable[str] = DEFAULT_EXPORT_TABS,
    reports: Iterable[str] = DEFAULT_REPORTS,
) -> list[str]:
    _validate_url(start_url)
    if not _is_absolute_path(output_folder):
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_OUTPUT_PATH_INVALID",
            f"Output folder must be absolute: {output_folder}",
            "Provide a tenant- and run-scoped absolute output folder.",
        )
    selected_tabs = tuple(export_tabs)
    unknown_tabs = [tab for tab in selected_tabs if tab not in DEFAULT_EXPORT_TABS]
    if unknown_tabs:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_EXPORT_NOT_ALLOWED",
            f"Unverified export tabs requested: {', '.join(unknown_tabs)}",
            "Use only export tabs verified by the installed CLI or update the versioned adapter contract after evidence review.",
        )

    command = [
        str(binary),
        "--crawl",
        start_url,
        "--headless",
        "--output-folder",
        str(output_folder),
        "--export-format",
        "csv",
        "--export-tabs",
        ",".join(selected_tabs),
        "--save-report",
        ",".join(reports),
    ]
    if config_path is not None:
        if not config_path.is_file():
            raise QualityGateError(
                "ERROR_SCREAMING_FROG_CONFIG_MISSING",
                f"Screaming Frog configuration file not found: {config_path}",
                "Provide a verified versioned Screaming Frog configuration file or omit the option for the local default configuration.",
            )
        command.extend(("--config", str(config_path)))
    if overwrite:
        command.append("--overwrite")
    return command


def _normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except UnicodeDecodeError:
        with path.open("r", encoding="cp1252", newline="") as handle:
            return list(csv.DictReader(handle))


def _get_value(row: dict[str, str], *names: str) -> str:
    normalized = {_normalized_header(key): value for key, value in row.items() if key is not None}
    for name in names:
        value = normalized.get(_normalized_header(name))
        if value is not None:
            return str(value).strip()
    return ""


def _issue_count(value: str) -> int:
    try:
        return int(str(value).replace(".", "").replace(",", ".").split(".")[0] or 0)
    except ValueError:
        return 0


def summarize_exports(output_folder: Path) -> dict:
    csv_files = sorted(path for path in output_folder.rglob("*.csv") if path.is_file() and path.stat().st_size > 0)
    if not csv_files:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_EXPORTS_MISSING",
            f"No non-empty CSV exports were found in {output_folder}.",
            "Inspect the crawl log, verify export names and licence capabilities, then rerun the crawl.",
        )

    urls: set[str] = set()
    html_urls: set[str] = set()
    final_url = ""
    issue_sets = {
        "status_4xx": set(),
        "status_5xx": set(),
        "internal_html_4xx": set(),
        "resource_4xx": set(),
        "non_indexable": set(),
        "missing_titles": set(),
        "missing_titles_indexable": set(),
        "missing_meta_descriptions": set(),
        "missing_meta_descriptions_indexable": set(),
        "missing_h1": set(),
        "missing_h1_indexable": set(),
        "missing_h2_indexable": set(),
        "canonical_issues": set(),
        "canonical_issues_indexable": set(),
        "broken_internal_links": set(),
        "hreflang_issues": set(),
        "structured_data_issues": set(),
    }
    issue_counts = {
        "internal_link_issues": 0,
        "redirect_issues": 0,
        "critical_security_issues": 0,
        "security_issues": 0,
    }

    for path in csv_files:
        rows = _read_csv_rows(path)
        name = _normalized_header(path.stem)
        is_internal_export = "internalall" in name or name == "internal"
        is_issues_overview = "issuesoverview" in name
        if is_issues_overview:
            for row in rows:
                issue_name = _get_value(row, "Issue Name")
                issue_type = _get_value(row, "Issue Type").lower()
                priority = _get_value(row, "Issue Priority").lower()
                count = _issue_count(_get_value(row, "URLs"))
                if issue_name.startswith("Links:") and issue_type in {"warning", "error"}:
                    issue_counts["internal_link_issues"] += count
                if "redirect" in issue_name.lower() and any(term in issue_name.lower() for term in ("chain", "loop", "non-200")):
                    issue_counts["redirect_issues"] += count
                if issue_name.startswith("Security:") and issue_type in {"warning", "error"}:
                    issue_counts["security_issues"] += count
                    if issue_type == "error" or priority in {"high", "critical"}:
                        issue_counts["critical_security_issues"] += count

        for index, row in enumerate(rows):
            address = _get_value(row, "Address", "URL", "URI") or f"{path.name}:{index}"
            if is_internal_export and address.startswith(("http://", "https://")):
                urls.add(address)
            content_type = _get_value(row, "Content Type", "Content")
            is_html = content_type.lower().startswith("text/html")
            indexability = _get_value(row, "Indexability")
            is_indexable_html = is_internal_export and is_html and indexability.lower() == "indexable"
            status = _get_value(row, "Status Code")
            suffix = Path(urlparse(address).path).suffix.lower() if address.startswith(("http://", "https://")) else ""

            if is_internal_export and is_html and address.startswith(("http://", "https://")):
                html_urls.add(address)
            if is_internal_export and _get_value(row, "Crawl Depth") == "0" and not final_url:
                final_url = _get_value(row, "Redirect URL") or address
            if status.startswith("4"):
                issue_sets["status_4xx"].add(address)
                if suffix in ASSET_EXTENSIONS:
                    issue_sets["resource_4xx"].add(address)
                else:
                    issue_sets["internal_html_4xx"].add(address)
                    issue_sets["broken_internal_links"].add(address)
            if status.startswith("5"):
                issue_sets["status_5xx"].add(address)
            if is_internal_export and is_html and indexability and indexability.lower() != "indexable":
                issue_sets["non_indexable"].add(address)
            if is_internal_export and is_html:
                checks = (
                    ("missing_titles", "Title 1", "Page Title 1"),
                    ("missing_meta_descriptions", "Meta Description 1"),
                    ("missing_h1", "H1-1", "H1 1", "H1"),
                    ("canonical_issues", "Canonical Link Element 1", "Canonical Link Element"),
                )
                for finding_key, *headers in checks:
                    if not _get_value(row, *headers):
                        issue_sets[finding_key].add(address)
                        if is_indexable_html:
                            issue_sets[f"{finding_key}_indexable"].add(address)
                if is_indexable_html and not _get_value(row, "H2-1", "H2 1", "H2"):
                    issue_sets["missing_h2_indexable"].add(address)
            if "canonical" in name and any(term in name for term in ("missing", "multiple", "conflicting", "nonindexable", "chain")):
                issue_sets["canonical_issues"].add(address)
            if "hreflang" in name and any(term in name for term in ("missing", "non200", "inconsistent", "incorrect", "noindex", "noncanonical")):
                issue_sets["hreflang_issues"].add(address)
            if "structureddat" in name and any(term in name for term in ("error", "warning", "parse")):
                issue_sets["structured_data_issues"].add(address)

    exports = [
        {
            "relative_path": path.relative_to(output_folder).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        }
        for path in sorted(path for path in output_folder.rglob("*") if path.is_file() and path.stat().st_size > 0)
    ]
    findings = {key: len(value) for key, value in issue_sets.items()}
    findings.update(issue_counts)
    return {
        "final_url": final_url,
        "url_count": len(urls),
        "html_url_count": len(html_urls),
        "exports": exports,
        "findings": findings,
    }


def build_evidence(
    run_id: str,
    project_id: str,
    deployment_id: str,
    start_url: str,
    binary_path: str,
    capability_hash: str,
    started_at: str,
    completed_at: str,
    output_folder: Path,
    summary: dict,
    url_limit: int,
    policy_step: str = "1",
    multilingual: bool = False,
    waivers: list[dict] | None = None,
    artifact: dict | None = None,
    as_of: str | None = None,
) -> dict:
    for field, value in (("run_id", run_id), ("project_id", project_id), ("deployment_id", deployment_id)):
        if not ID_PATTERNS[field].fullmatch(value):
            raise QualityGateError(
                "ERROR_SCREAMING_FROG_ID_INVALID",
                f"Invalid {field}: {value}",
                "Use the stable Heartweb identifier format required by the quality evidence schema.",
            )
    _validate_url(start_url)
    limit_hit = summary["url_count"] >= url_limit
    disposition = evaluate_crawl_disposition(
        summary["findings"],
        policy_step,
        context={"multilingual": multilingual},
        waivers=waivers,
        artifact=artifact,
        as_of=as_of,
    )
    status = "blocked" if limit_hit or disposition["result"] == "blocked" else "passed"
    error = None
    if limit_hit:
        error = {
            "code": "ERROR_SCREAMING_FROG_URL_LIMIT_REACHED",
            "message": f"Crawl reached the configured URL limit of {url_limit}; completeness cannot be asserted.",
            "remediation": "Use a verified licensed crawl or a narrower approved scope and rerun the quality gate.",
        }
    elif disposition["result"] == "blocked":
        finding = (disposition["blocking_findings"] + disposition["waiver_required_findings"])[0]
        error = {
            "code": finding["failure_code"],
            "message": f"Crawl policy blocked finding '{finding['finding_key']}' with count {finding['count']}.",
            "remediation": "Fix the finding or provide a current revision-bound waiver where the policy permits one.",
        }
    return {
        "schema_version": "1.1.0",
        "run_id": run_id,
        "project_id": project_id,
        "deployment_id": deployment_id,
        "start_url": start_url,
        "final_url": summary.get("final_url") or start_url,
        "tool": {
            "id": "screaming-frog-cli",
            "binary_path": binary_path,
            "capability_hash": capability_hash,
        },
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "url_count": summary["url_count"],
        "html_url_count": summary["html_url_count"],
        "limit_hit": limit_hit,
        "exports": summary["exports"],
        "findings": summary["findings"],
        "policy_disposition": disposition,
        "error": error,
    }


def _validate_evidence(evidence: dict) -> None:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise QualityGateError(
            "ERROR_JSONSCHEMA_DEPENDENCY_MISSING",
            "The jsonschema dependency is required to validate crawl evidence.",
            "Install the pinned project development requirements and rerun the quality gate.",
        ) from exc
    schema_path = Path(__file__).resolve().parents[2] / "standards" / "quality" / "screaming-frog-crawl.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(evidence),
        key=lambda error: list(error.path),
    )
    if errors:
        details = "; ".join(f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors)
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_EVIDENCE_INVALID",
            f"Generated crawl evidence failed its contract: {details}",
            "Correct the adapter or source exports before accepting the crawl evidence.",
        )


def run_crawl(
    start_url: str,
    evidence_root: Path,
    tenant_id: str,
    run_id: str,
    project_id: str,
    deployment_id: str,
    binary: str | None = None,
    config_path: Path | None = None,
    url_limit: int = 500,
    timeout_seconds: int = 1800,
    policy_step: str = "1",
    multilingual: bool = False,
) -> dict:
    if url_limit < 1:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_LIMIT_INVALID",
            f"URL limit must be positive: {url_limit}",
            "Provide the verified active crawl limit for the installed licence state.",
        )
    output_folder = resolve_evidence_output_folder(evidence_root, tenant_id, project_id, run_id)
    if output_folder.exists() and any(output_folder.iterdir()):
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_OUTPUT_NOT_EMPTY",
            f"Output folder is not empty: {output_folder}",
            "Use a new immutable run identifier after preserving previous evidence.",
        )
    capabilities = preflight(binary=binary)
    output_folder.mkdir(parents=True, exist_ok=True)
    binary_path = Path(capabilities["binary_path"])
    command = build_crawl_command(
        binary=binary_path,
        start_url=start_url,
        output_folder=output_folder,
        config_path=config_path,
    )
    started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_CRAWL_TIMEOUT",
            f"Crawl timed out after {timeout_seconds} seconds.",
            "Inspect site access and crawl scope, then resume with an approved timeout and configuration.",
        ) from exc
    if completed.returncode != 0:
        diagnostic = "\n".join(part for part in (completed.stdout, completed.stderr) if part)[-4000:]
        raise QualityGateError(
            "ERROR_SCREAMING_FROG_CRAWL_FAILED",
            f"Crawl returned exit code {completed.returncode}. Diagnostic: {diagnostic}",
            "Inspect the diagnostic, configuration, licence and site response, then rerun in the same controlled scope.",
        )
    completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    summary = summarize_exports(output_folder)
    evidence = build_evidence(
        run_id=run_id,
        project_id=project_id,
        deployment_id=deployment_id,
        start_url=start_url,
        binary_path=str(binary_path),
        capability_hash=capabilities["capability_hash"],
        started_at=started_at,
        completed_at=completed_at,
        output_folder=output_folder,
        summary=summary,
        url_limit=url_limit,
        policy_step=policy_step,
        multilingual=multilingual,
    )
    _validate_evidence(evidence)
    evidence_path = output_folder / "crawl-evidence.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if evidence["status"] != "passed":
        raise QualityGateError(
            evidence["error"]["code"],
            evidence["error"]["message"],
            evidence["error"]["remediation"],
        )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Heartweb Screaming Frog quality gate runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--binary")

    crawl_parser = subparsers.add_parser("crawl")
    crawl_parser.add_argument("--start-url", required=True)
    crawl_parser.add_argument("--evidence-root", required=True)
    crawl_parser.add_argument("--tenant-id", required=True)
    crawl_parser.add_argument("--run-id", required=True)
    crawl_parser.add_argument("--project-id", required=True)
    crawl_parser.add_argument("--deployment-id", required=True)
    crawl_parser.add_argument("--binary")
    crawl_parser.add_argument("--config")
    crawl_parser.add_argument("--url-limit", type=int, default=500)
    crawl_parser.add_argument("--timeout-seconds", type=int, default=1800)
    crawl_parser.add_argument("--policy-step", choices=["1", "4b"], default="1")
    crawl_parser.add_argument("--multilingual", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "preflight":
            result = preflight(binary=args.binary)
        else:
            result = run_crawl(
                start_url=args.start_url,
                evidence_root=Path(args.evidence_root),
                tenant_id=args.tenant_id,
                run_id=args.run_id,
                project_id=args.project_id,
                deployment_id=args.deployment_id,
                binary=args.binary,
                config_path=Path(args.config) if args.config else None,
                url_limit=args.url_limit,
                timeout_seconds=args.timeout_seconds,
                policy_step=args.policy_step,
                multilingual=args.multilingual,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except QualityGateError as exc:
        print(json.dumps({"status": "failed", "error": exc.to_dict()}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
