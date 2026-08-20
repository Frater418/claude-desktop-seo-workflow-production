"""Strict fail-fast tests for the capacity matrix solver.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
import importlib.util
import unittest
from pathlib import Path


def _load_solver_module():
    path = Path(__file__).resolve().parents[1] / "mcp" / "tools" / "capacity_matrix_solver.py"
    spec = importlib.util.spec_from_file_location("heartweb_capacity_matrix_solver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


solver = _load_solver_module()
CapacityValidationError = solver.CapacityValidationError
solve_capacity_plan = solver.solve_capacity_plan


class CapacityMatrixSolverStrictTests(unittest.TestCase):
    def test_empty_input_is_rejected(self):
        with self.assertRaises(CapacityValidationError) as ctx:
            solve_capacity_plan([])
        self.assertEqual("ERROR_SOLVER_EMPTY_INPUT", ctx.exception.code)

    def test_missing_search_volume_is_rejected(self):
        item = self.valid_item()
        item.pop("Suchvolumen")
        with self.assertRaises(CapacityValidationError) as ctx:
            solve_capacity_plan([item])
        self.assertEqual("ERROR_SOLVER_REQUIRED_FIELD_MISSING", ctx.exception.code)
        self.assertEqual("search_volume", ctx.exception.field)

    def test_unknown_content_type_is_rejected(self):
        item = self.valid_item()
        item["Content_Type"] = "Unknown-Type"
        with self.assertRaises(CapacityValidationError) as ctx:
            solve_capacity_plan([item])
        self.assertEqual("ERROR_SOLVER_CONTENT_TYPE_UNKNOWN", ctx.exception.code)

    def test_zero_metrics_are_valid_when_explicit(self):
        item = self.valid_item()
        item["Suchvolumen"] = 0
        item["Difficulty"] = 0
        result = solve_capacity_plan([item], hours_min=1.0, hours_max=15.0)
        self.assertEqual(1, sum(len(week["items"]) for week in result["weeks"]))

    def test_invalid_capacity_band_is_rejected(self):
        with self.assertRaises(CapacityValidationError) as ctx:
            solve_capacity_plan([self.valid_item()], hours_min=16.0, hours_max=15.0)
        self.assertEqual("ERROR_SOLVER_CAPACITY_INVALID", ctx.exception.code)

    def test_existing_full_fixture_remains_supported(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_cluster_keywords.json"
        items = json.loads(fixture.read_text(encoding="utf-8"))
        result = solve_capacity_plan(items)
        self.assertGreater(sum(len(week["items"]) for week in result["weeks"]), 0)

    @staticmethod
    def valid_item() -> dict:
        return {
            "Pillar_Thema": "Ambulante Pflege",
            "Kategorie": "Lokal",
            "Cluster_Thema": "Pflegedienst Muenchen",
            "Content_Type": "Landingpage",
            "Ziel_Keyword": "pflegedienst muenchen",
            "Suchvolumen": 100,
            "Difficulty": 10,
            "Is_Mandatory_Location": True,
        }


if __name__ == "__main__":
    unittest.main()
