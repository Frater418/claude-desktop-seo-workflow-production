"""Versioned crawl disposition and waiver evaluation.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


DISPOSITIONS = {"pass": 0, "advisory": 1, "waiver_required": 2, "block": 3}


def load_policy(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[2]
    return json.loads((root / "standards" / "quality" / "crawl-disposition-policy.json").read_text(encoding="utf-8"))


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _valid_waiver(waiver: dict, finding_key: str, step_id: str, policy: dict, artifact: dict, as_of: str) -> bool:
    try:
        return (
            waiver["quality_gate_id"] == "qg-step1-crawl-snapshot"
            and waiver["artifact_id"] == artifact["artifact_id"]
            and waiver["artifact_sha256"] == artifact["content_sha256"]
            and waiver["policy_id"] == policy["policy_id"]
            and waiver["policy_version"] == policy["version"]
            and step_id in waiver["step_ids"]
            and finding_key in waiver["finding_keys"]
            and _timestamp(waiver["approved_at"]) <= _timestamp(as_of) < _timestamp(waiver["expires_at"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def evaluate_crawl_disposition(
    findings: dict,
    step_id: str,
    policy: dict | None = None,
    context: dict | None = None,
    waivers: list[dict] | None = None,
    artifact: dict | None = None,
    as_of: str | None = None,
) -> dict:
    """Return deterministic pass, advisory, waiver or block disposition."""
    if step_id not in {"1", "4b"}:
        raise ValueError(f"Unsupported crawl policy step: {step_id}")
    policy = policy or load_policy()
    context = context or {}
    waivers = waivers or []
    result = {
        "policy_id": policy["policy_id"],
        "policy_version": policy["version"],
        "step_id": step_id,
        "result": "passed",
        "advisory_findings": [],
        "waiver_required_findings": [],
        "blocking_findings": [],
        "waived_findings": [],
        "waiver_ids": [],
    }
    for rule in policy["rules"]:
        if rule["applicability"] == "when_multilingual" and not context.get("multilingual", False):
            continue
        count = int(findings.get(rule["finding_key"], 0) or 0)
        if count <= rule["allowed_count"]:
            continue
        disposition = rule[f"step{step_id}_disposition"]
        record = {
            "finding_key": rule["finding_key"],
            "count": count,
            "allowed_count": rule["allowed_count"],
            "failure_code": rule["failure_code"],
            "disposition": disposition,
        }
        if disposition == "advisory":
            result["advisory_findings"].append(record)
        elif disposition == "block":
            result["blocking_findings"].append(record)
        elif disposition == "waiver_required":
            matching = None
            if artifact is not None and as_of is not None:
                matching = next(
                    (
                        waiver
                        for waiver in waivers
                        if _valid_waiver(waiver, rule["finding_key"], step_id, policy, artifact, as_of)
                    ),
                    None,
                )
            if matching is None:
                result["waiver_required_findings"].append(record)
            else:
                result["waived_findings"].append(record)
                result["waiver_ids"].append(matching["waiver_id"])

    if result["blocking_findings"] or result["waiver_required_findings"]:
        result["result"] = "blocked"
    elif result["advisory_findings"] or result["waived_findings"]:
        result["result"] = "passed_with_warnings"
    result["waiver_ids"] = sorted(set(result["waiver_ids"]))
    return result
