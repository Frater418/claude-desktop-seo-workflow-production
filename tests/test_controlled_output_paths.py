from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.preflight_common.output_paths import OutputPathError, resolve_step_output


class ControlledOutputPathTests(unittest.TestCase):
    def test_derives_step4b_path_inside_workspace_when_identifier_is_safe(self) -> None:
        # Given: an empty controlled customer workspace and a valid artifact identity
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            # When: the Step 4B renderer resolves its destination
            output = resolve_step_output(workspace, "4b", "artifact-solar-page-001")
            # Then: only the versioned page path is returned
            self.assertEqual(
                workspace / "v2/outputs/step4b/pages/artifact-solar-page-001.v1.html",
                output,
            )

    def test_rejects_escaping_identifier_when_resolving_output(self) -> None:
        # Given: a controlled workspace and an escaping artifact identity
        with tempfile.TemporaryDirectory() as temporary_directory:
            # When: an unsafe output identity is submitted
            with self.assertRaises(OutputPathError) as raised:
                resolve_step_output(Path(temporary_directory), "4b", "../escape")
            # Then: the stable controlled-path code identifies the rejection
            self.assertEqual("ERROR_OUTPUT_IDENTIFIER_INVALID", raised.exception.code)

    def test_rejects_missing_workspace_root_with_stable_code(self) -> None:
        # Given: a workspace root that does not exist
        missing_root = Path(tempfile.gettempdir()) / "heartweb-missing-controlled-root"
        # When: a renderer resolves its derived output
        with self.assertRaises(OutputPathError) as raised:
            resolve_step_output(missing_root, "3")
        # Then: the caller receives the routed root failure
        self.assertEqual("ERROR_OUTPUT_ROOT_INVALID", raised.exception.code)
