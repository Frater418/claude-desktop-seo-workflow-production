#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests" / "run_full_suite.py"
CHILD_ENVIRONMENT_FLAG = "HEARTWEB_FULL_SUITE_RUNNER_REGRESSION_CHILD"


@unittest.skipIf(os.environ.get(CHILD_ENVIRONMENT_FLAG), "prevents recursive full-suite execution")
class FullSuiteRunnerTests(unittest.TestCase):
    def test_contract_discovery_runs_required_modules_with_nonzero_count(self) -> None:
        environment = os.environ.copy()
        environment[CHILD_ENVIRONMENT_FLAG] = "1"
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--unittest-phase", "contracts"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            env=environment,
            text=True,
        )
        output = completed.stdout + completed.stderr

        self.assertEqual(0, completed.returncode, output)
        count_match = re.search(r"\[PHASE PASSED\] Contract unittest discovery: (\d+) tests", output)
        self.assertIsNotNone(count_match, output)
        self.assertGreater(int(count_match.group(1)), 0)
        self.assertIn("test_operator_records", output)
        self.assertIn("test_integration_contracts", output)


if __name__ == "__main__":
    unittest.main()
