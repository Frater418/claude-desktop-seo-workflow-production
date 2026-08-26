from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from services.operator_api.step_agent_results import bind_deterministic_output_fields
from tests.support.step4a_fixtures import load_fixture as load_step4a_fixture


ROOT = Path(__file__).resolve().parents[1]
STEP4A_BRIEFING = "https://heartweb.example/schema/outputs/step-4a-briefing.schema.json"
STEP4B_PAGE = "https://heartweb.example/schema/outputs/step-4b-page-spec.schema.json"
STEP4B_STAGING = "https://heartweb.example/schema/outputs/staging-evidence.schema.json"


def _load(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _hash(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class StepAgentDeterministicHashTests(unittest.TestCase):
    def test_step4a_core_binds_graph_hash_without_mutating_raw_agent_result(self) -> None:
        briefing = load_step4a_fixture(ROOT / "tests/fixtures/step4a", "positive-bundle.json")["briefing"]
        briefing["jsonld"]["graph_hash"] = "f" * 64
        outputs = [{"contract_id": STEP4A_BRIEFING, "content": briefing}]

        normalized = bind_deterministic_output_fields("4a", outputs)

        self.assertEqual(_hash(briefing["jsonld"]["graph"]), normalized[0]["content"]["jsonld"]["graph_hash"])
        self.assertEqual("f" * 64, outputs[0]["content"]["jsonld"]["graph_hash"])

    def test_step4b_core_binds_graph_page_staging_and_check_hashes(self) -> None:
        bundle = _load("tests/fixtures/step4b/non-ahd-product-bundle.json")
        page = copy.deepcopy(bundle["page_spec"])
        staging = copy.deepcopy(bundle["staging_evidence"])
        page["jsonld"]["graph_hash"] = "f" * 64
        page["content_sha256"] = "f" * 64
        staging["content_sha256"] = "f" * 64
        staging["staging_sha256"] = "f" * 64
        for check in staging["checks"]:
            check["content_sha256"] = "f" * 64

        normalized = bind_deterministic_output_fields(
            "4b",
            [
                {"contract_id": STEP4B_PAGE, "content": page},
                {"contract_id": STEP4B_STAGING, "content": staging},
            ],
        )
        normalized_page = normalized[0]["content"]
        normalized_staging = normalized[1]["content"]

        expected_graph_hash = _hash(page["jsonld"]["graph"])
        page_without_content_hash = copy.deepcopy(page)
        page_without_content_hash["jsonld"]["graph_hash"] = expected_graph_hash
        page_without_content_hash.pop("content_sha256", None)
        expected_content_hash = _hash(page_without_content_hash)
        staging_without_hash = copy.deepcopy(staging)
        staging_without_hash["content_sha256"] = expected_content_hash
        staging_without_hash.pop("staging_sha256", None)
        for check in staging_without_hash["checks"]:
            check["content_sha256"] = expected_content_hash

        self.assertEqual(expected_graph_hash, normalized_page["jsonld"]["graph_hash"])
        self.assertEqual(expected_content_hash, normalized_page["content_sha256"])
        self.assertEqual(expected_content_hash, normalized_staging["content_sha256"])
        self.assertTrue(all(check["content_sha256"] == expected_content_hash for check in normalized_staging["checks"]))
        self.assertEqual(_hash(staging_without_hash), normalized_staging["staging_sha256"])
        self.assertEqual("f" * 64, page["content_sha256"])
        self.assertEqual("f" * 64, staging["staging_sha256"])


if __name__ == "__main__":
    unittest.main()
