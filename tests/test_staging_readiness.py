from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from services.staging_readiness import LocalStagingReadinessError, local_staging_readiness


ROOT = Path(__file__).resolve().parents[1]


class LocalStagingReadinessTests(unittest.TestCase):
    def test_accepts_typed_page_and_labels_all_four_reports_as_local_simulations(self) -> None:
        page = json.loads((ROOT / "tests/fixtures/step4b/non-ahd-product-bundle.json").read_text(encoding="utf-8"))["page_spec"]
        page.pop("content_sha256", None)
        page["jsonld"].pop("graph_hash", None)

        normalized, reports = local_staging_readiness(page, ROOT)

        self.assertEqual({"crawl", "lighthouse", "axe", "visual"}, {report["tool"] for report in reports})
        self.assertTrue(all(report["classification"] == "local_simulated" for report in reports))
        self.assertTrue(all("not executed" in report["source"] or "no external crawler" in report["source"] for report in reports))
        self.assertRegex(normalized["content_sha256"], r"^[a-f0-9]{64}$")
        self.assertRegex(normalized["jsonld"]["graph_hash"], r"^[a-f0-9]{64}$")

    def test_rejects_invalid_section_contract_before_emitting_reports(self) -> None:
        page = json.loads((ROOT / "tests/fixtures/step4b/non-ahd-product-bundle.json").read_text(encoding="utf-8"))["page_spec"]
        page["sections"] = deepcopy(page["sections"][:-1])

        with self.assertRaises(LocalStagingReadinessError) as error:
            local_staging_readiness(page, ROOT)

        self.assertEqual("ERROR_LOCAL_STAGING_READINESS_FAILED", error.exception.code)


if __name__ == "__main__":
    unittest.main()
