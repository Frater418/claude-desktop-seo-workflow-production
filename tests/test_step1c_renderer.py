from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.step1c_preflight.render import render_step1c, write_step1c


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step1c"


class Step1cRendererTests(unittest.TestCase):
    def test_renderer_is_deterministic_and_uses_customer_tokens_without_cdn(self) -> None:
        design = json.loads((FIXTURES / "non-ahd-outdoor-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "non-ahd-outdoor-template.json").read_text(encoding="utf-8"))
        first = render_step1c({"design": design, "templates": [template]})
        second = render_step1c({"design": design, "templates": [template]})
        self.assertEqual(first, second)
        self.assertIn(design["tokens"]["color_primary"], first["css"])
        self.assertIn(template["content_id"], first["html"])
        self.assertNotIn("cdn", first["html"].lower())

    def test_invalid_input_does_not_write_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "derived.json"
            with self.assertRaises(ValueError):
                write_step1c({"design": {}, "templates": []}, output)
            self.assertFalse(output.exists())

    def test_writer_derives_template_output_from_template_id(self) -> None:
        # Given: a valid template whose content identity differs from its template identity
        design = json.loads((FIXTURES / "non-ahd-outdoor-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "non-ahd-outdoor-template.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            # When: the canonical Step 1C views are written
            _, templates = write_step1c({"design": design, "templates": [template]}, Path(directory))
            # Then: the derived filename is keyed by canonical template_id
            self.assertEqual(
                Path(directory) / "v2/outputs/step1c/templates/template-outdoor-kayaks-0001.v1.html",
                templates[0],
            )
