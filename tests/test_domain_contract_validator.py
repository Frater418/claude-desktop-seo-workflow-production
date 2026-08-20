"""Tests for the runtime-neutral Foundation domain validator.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from services.domain_contract.validator import DomainContractError, assert_project_valid, validate_project


class DomainContractValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.fixture_dir = cls.root / "tests" / "fixtures" / "domain"

    def load(self, relative: str) -> dict:
        return json.loads((self.fixture_dir / relative).read_text(encoding="utf-8"))

    def test_all_real_customer_fixtures_validate(self):
        fixtures = sorted((self.fixture_dir / "real-customer-matrix").glob("*.json"))
        self.assertEqual(10, len(fixtures))
        for path in fixtures:
            with self.subTest(path=path.name):
                result = validate_project(json.loads(path.read_text(encoding="utf-8")), root=self.root)
                self.assertTrue(result["valid"], result["errors"])

    def test_geo_mismatch_returns_stable_code(self):
        result = validate_project(self.load("negative-geo-mismatch.json"), root=self.root)
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_DOMAIN_GEO_MISMATCH", {error["code"] for error in result["errors"]})

    def test_missing_locale_returns_stable_code(self):
        result = validate_project(self.load("negative-missing-locale.json"), root=self.root)
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_DOMAIN_LOCALE_REQUIRED", result["errors"][0]["code"])

    def test_unverified_local_presence_returns_stable_code(self):
        result = validate_project(self.load("negative-unverified-local-presence.json"), root=self.root)
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_DOMAIN_LOCAL_PRESENCE_UNVERIFIED", {error["code"] for error in result["errors"]})

    def test_missing_ymyl_evidence_returns_stable_code(self):
        result = validate_project(self.load("negative-missing-ymyl-evidence.json"), root=self.root)
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_COMPLIANCE_YMYL_EVIDENCE_REQUIRED", result["errors"][0]["code"])

    def test_assert_raises_structured_error(self):
        with self.assertRaises(DomainContractError) as ctx:
            assert_project_valid(self.load("negative-missing-locale.json"), root=self.root)
        self.assertEqual("ERROR_DOMAIN_LOCALE_REQUIRED", ctx.exception.code)
        self.assertTrue(ctx.exception.remediation)


if __name__ == "__main__":
    unittest.main()
