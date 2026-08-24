from __future__ import annotations

from pathlib import Path
import unittest

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistry


ROOT = Path(__file__).resolve().parents[1]
_PREFIX = "/v1/tenants/{tenant_id}/projects/{project_id}/delivery"


class DeliveryOpenApiTests(unittest.TestCase):
    def test_openapi_generation_is_repeatable_after_delivery_override(self) -> None:
        app = create_app(WorkspaceRegistry(()), ROOT, AppConfig(ROOT, allow_unready=True))

        documents = (app.openapi(), app.openapi(), app.openapi())

        self.assertEqual(documents[0], documents[1])
        self.assertEqual(documents[1], documents[2])
        paths = documents[0]["paths"]
        self.assertNotIn("422", paths[f"{_PREFIX}/exports"]["get"]["responses"])
        for path in (f"{_PREFIX}/preview", f"{_PREFIX}/exports/{{export_id}}", f"{_PREFIX}/exports/{{export_id}}/download"):
            self.assertIn("422", paths[path]["get"]["responses"])
        self.assertIn("422", paths[f"{_PREFIX}/exports"]["post"]["responses"])


if __name__ == "__main__":
    unittest.main()
