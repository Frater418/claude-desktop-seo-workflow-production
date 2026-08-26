from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from services.provider_gateway.core import canonical_request_sha256
from tests.test_preflight_common import _predecessor, _project


ROOT = Path(__file__).resolve().parents[2]


def load_pq0_2_fixture() -> dict[str, object]:
    fixture = json.loads((ROOT / "tests/fixtures/step2/pq0-2-canonical-candidate.json").read_text(encoding="utf-8"))
    for row in fixture["candidate"]["pillars"][0]["rows"]:
        row["cpc_usd"]["reason"] = "not_returned_by_provider"
    pq0_2_provider_records(fixture["candidate"])
    return fixture


def _gateway_fixture() -> dict[str, object]:
    return json.loads((ROOT / "tests/fixtures/provider_gateway/pq0-2-local-normalized-keyword.json").read_text(encoding="utf-8"))


def pq0_2_provider_records(candidate: dict[str, object]) -> list[dict[str, object]]:
    gateway = _gateway_fixture()
    records = []
    rows = [row for pillar in candidate["pillars"] for row in pillar["rows"]]
    for number, row in enumerate(rows, start=1):
        record = {"evidence_id": row["evidence_id"], "request": deepcopy(gateway["request"]), "response": deepcopy(gateway["response"])}
        for side in (record["request"], record["response"]):
            side.update({field: candidate[field] for field in ("run_id", "project_id", "deployment_id", "source_artifact_ids", "language", "geo")})
        request_id = f"request-pq2-{number:04d}"
        raw_response = {"fixture_label": f"local-deterministic-only-{number:04d}", "keyword_metrics": [{"keyword": row["keyword"], "search_volume": row["search_volume"], "difficulty": row["difficulty"]}]}
        raw_response_hash = hashlib.sha256(json.dumps(raw_response, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
        record["request"].update({"request_id": request_id, "idempotency_key": f"idem-pq2-{number:04d}", "evidence_ids": [row["evidence_id"]], "decision_records": [{"decision_id": f"decision-pq2-{number:04d}", "outcome": "research", "evidence_ids": [row["evidence_id"]]}]})
        record["request"]["request_sha256"] = canonical_request_sha256(record["request"])
        record["response"].update({"response_id": f"response-pq2-{number:04d}", "request_id": request_id, "provider_job_id": f"job-pq2-{number:04d}", "raw_response": raw_response, "raw_response_sha256": raw_response_hash, "evidence_ids": [row["evidence_id"]], "decision_records": [{"decision_id": f"decision-pq2-{number:04d}", "outcome": "research", "evidence_ids": [row["evidence_id"]]}]})
        row["raw_response_sha256"] = raw_response_hash
        records.append(record)
    return records


def pq0_2_operational_bundle() -> dict[str, object]:
    candidate = load_pq0_2_fixture()["candidate"]
    candidate.update({"project_id": "project-national-b2b", "deployment_id": "dep-national-b2b-de", "source_artifact_ids": ["artifact-predecessor-0001"], "language": "de", "geo": {"country_code": "DE", "provider_location_code": 276}})
    artifact, release = _predecessor("1c", "GATE-1C")
    return {"candidate": candidate, "approved_pillar_ids": [pillar["pillar_id"] for pillar in candidate["pillars"]], "project": _project(), "predecessor_artifact": artifact, "predecessor_release": release, "provider_evidence_records": pq0_2_provider_records(candidate)}
