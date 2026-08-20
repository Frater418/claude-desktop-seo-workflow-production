from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Step4AImportPortabilityTests(unittest.TestCase):
    def test_step4a_import_does_not_depend_on_external_mcp_package_shape(self) -> None:
        script = """
import sys
import types
fake_mcp = types.ModuleType('mcp')
fake_mcp.__path__ = []
sys.modules['mcp'] = fake_mcp
from services.step4a_preflight.validator import validate_step4a_preflight
print(validate_step4a_preflight.__name__)
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("validate_step4a_preflight", result.stdout.strip())

    def test_missing_local_validator_has_stable_error_code(self) -> None:
        from services.jsonld_validation import JsonLdValidatorAdapterError, validate_local_jsonld_text

        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(JsonLdValidatorAdapterError) as caught:
                validate_local_jsonld_text(
                    "{}",
                    root=Path(temporary_directory),
                )
        self.assertEqual("ERROR_JSONLD_VALIDATOR_UNAVAILABLE", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
