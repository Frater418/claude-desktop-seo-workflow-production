from __future__ import annotations

import hashlib
import json
from pathlib import Path


_LEGACY_REPAIR = {
    "positive-bundle.json",
    "positive-briefing.json",
    "non-ahd-b2b-bundle.json",
    "missing-reviewer-policy-bundle.json",
}


def load_fixture(fixtures: Path, name: str) -> dict:
    value = json.loads((fixtures / name).read_text(encoding="utf-8"))
    if name not in _LEGACY_REPAIR:
        return value
    briefing = value.get("briefing", value)
    if not isinstance(briefing, dict):
        return value
    briefing.setdefault("briefing_sections", _sections())
    briefing.setdefault("entity_bindings", {"about": [], "mentions": []})
    if isinstance(briefing.get("jsonld"), dict):
        graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://example.invalid/briefing#product", "@type": "Product", "name": "Verified briefing"}]}
        canonical = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        briefing["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
        ledger = value.get("claim_ledger")
        claims = ledger.get("claims", []) if isinstance(ledger, dict) else [{"claim_id": "claim-placeholder-0001"}]
        briefing["claim_bindings"] = [{"claim_id": claim["claim_id"], "graph_node_id": "https://example.invalid/briefing#product"} for claim in claims]
    return value


def _sections() -> dict[str, object]:
    return {"audience": "Editors preparing a local service page.", "search_intent": "Informational service research.", "primary_keyword": "simulated care service", "content_goal": "Produce an evidence-bound briefing.", "tone": "Clear, accurate and restrained.", "cta_guidance": "Invite a reviewed local consultation.", "internal_link_guidance": "Link to the verified service overview.", "copywriter_instructions": "Use only declared evidence and mark uncertainty.", "secondary_keywords": ["local care", "care service"], "outline": ["Introduction", "Evidence-bound service guidance"], "publication_checklist": ["Verify evidence", "Confirm reviewer approval"], "definitive_language_guidance": {"required": True, "preferred_patterns": ["Evidence indicates", "The briefing states"], "prohibited_patterns": ["Guaranteed outcome", "Always effective"], "rationale": "Definitive language must remain evidence-bound and reviewable."}}
