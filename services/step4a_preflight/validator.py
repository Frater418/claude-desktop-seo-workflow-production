from __future__ import annotations

import json
import hashlib
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.jsonld_validation import JsonLdValidatorAdapterError, validate_local_jsonld_text
from services.preflight_common import validate_lineage
from services.step4a_preflight.content_validation import validate_content_semantics
from services.step4a_preflight.entity_validation import validate_entity_bindings


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _errors(schema_name: str, value: object, code: str, root: Path) -> list[dict[str, object]]:
    schema = json.loads((root / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
    return [{"code": code, "message": error.message, "path": list(error.absolute_path)} for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)]


def _graph_node_ids(graph: dict[str, object]) -> set[str]:
    nodes = graph.get("@graph")
    return {node["@id"] for node in nodes if isinstance(nodes, list) and isinstance(node, dict) and isinstance(node.get("@id"), str)}


def validate_step4a_candidate(bundle: dict[str, object], root: Path | None = None) -> dict[str, object]:
    root = root or _root()
    briefing = bundle.get("briefing")
    ledger = bundle.get("claim_ledger")
    errors = _errors("step-4a-briefing.schema.json", briefing, "ERROR_STEP4A_BRIEFING_INVALID", root)
    errors.extend(_errors("claim-ledger.schema.json", ledger, "ERROR_STEP4A_CLAIM_LEDGER_INVALID", root))
    if isinstance(briefing, dict) and isinstance(ledger, dict):
        errors.extend(validate_content_semantics(briefing, ledger))
        errors.extend(validate_entity_bindings(briefing))
        if briefing.get("claim_ledger_artifact_id") != ledger.get("artifact_id"):
            errors.append({"code": "ERROR_STEP4A_CLAIM_LINKAGE_INVALID", "message": "Briefing must reference its claim ledger.", "path": ["briefing", "claim_ledger_artifact_id"]})
        for claim in ledger.get("claims", []):
            if claim.get("claim_type") in {"medical", "financial", "legal"} and (not claim.get("evidence_ids") or not claim.get("reviewer_policy")):
                errors.append({"code": "ERROR_STEP4A_YMYL_CLAIM_INVALID", "message": "YMYL claims require evidence and reviewer policy.", "path": ["claim_ledger", "claims"]})
        if any(item.get("source") != "provider_gateway" for item in briefing.get("serp_evidence", [])):
            errors.append({"code": "ERROR_STEP4A_SERP_BOUNDARY_INVALID", "message": "SERP evidence must originate at the provider gateway.", "path": ["briefing", "serp_evidence"]})
        jsonld = briefing.get("jsonld")
        if isinstance(jsonld, dict) and isinstance(jsonld.get("graph"), dict):
            graph = json.dumps(jsonld["graph"], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            if jsonld.get("graph_hash") != hashlib.sha256(graph.encode("utf-8")).hexdigest():
                errors.append({"code": "ERROR_STEP4A_JSONLD_HASH_MISMATCH", "message": "JSON-LD graph hash must bind canonical graph bytes.", "path": ["briefing", "jsonld", "graph_hash"]})
            try:
                validation = validate_local_jsonld_text(
                    f'<script type="application/ld+json">{graph}</script>',
                    strict_geo=jsonld.get("level") == "enhanced",
                    root=root,
                )
            except JsonLdValidatorAdapterError as exc:
                errors.append({"code": exc.code, "message": str(exc), "path": ["briefing", "jsonld", "graph"]})
            else:
                if not validation["valid"]:
                    errors.append({"code": "ERROR_STEP4A_JSONLD_INVALID", "message": "JSON-LD graph fails local validation levels.", "path": ["briefing", "jsonld", "graph"]})
            bindings = briefing.get("claim_bindings")
            claims = ledger.get("claims")
            if isinstance(bindings, list) and isinstance(claims, list):
                claim_ids = {claim.get("claim_id") for claim in claims if isinstance(claim, dict)}
                binding_ids = [binding.get("claim_id") for binding in bindings if isinstance(binding, dict)]
                node_ids = _graph_node_ids(jsonld["graph"])
                if len(binding_ids) != len(bindings) or set(binding_ids) != claim_ids or len(binding_ids) != len(set(binding_ids)) or any(binding.get("graph_node_id") not in node_ids for binding in bindings if isinstance(binding, dict)):
                    errors.append({"code": "ERROR_STEP4A_CLAIM_LINKAGE_INVALID", "message": "Every ledger claim must bind exactly once to an existing JSON-LD graph node.", "path": ["briefing", "claim_bindings"]})
    return {"valid": not errors, "errors": errors}


def validate_step4a_preflight(bundle: dict[str, object], root: Path | None = None) -> dict[str, object]:
    root = root or _root()
    result = validate_step4a_candidate(bundle, root)
    result["errors"].extend(validate_lineage({**bundle, "candidate": bundle.get("briefing")}, "4a", "3", "GATE-3", root, "step-4a-briefing.schema.json"))
    result["valid"] = not result["errors"]
    return result
