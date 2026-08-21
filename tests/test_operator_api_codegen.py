from __future__ import annotations

import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from fastapi.routing import APIRoute
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from scripts import generate_operator_api_contracts as generator
from scripts.generate_operator_api_contracts import generate_artifacts
from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistry


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "standards" / "api" / "operator-api.openapi.json"
TYPES = ROOT / "apps" / "operator-console" / "src" / "generated" / "api-types.ts"


class OperatorApiCodegenTests(unittest.TestCase):
    def test_generator_emits_the_exact_fastapi_document_and_types(self) -> None:
        # Given: the isolated, server-owned registry required for a contract snapshot.
        app = create_app(WorkspaceRegistry(()), ROOT, AppConfig(ROOT, allow_unready=True))

        # When: the generator renders both committed artifacts without touching a customer workspace.
        openapi, types = generate_artifacts(ROOT)

        # Then: the snapshot is exact deterministic FastAPI output and the types derive only from it.
        self.assertEqual(app.openapi(), json.loads(openapi))
        self.assertTrue(openapi.isascii())
        self.assertTrue(openapi.endswith("\n"))
        self.assertEqual(openapi, json.dumps(json.loads(openapi), ensure_ascii=True, indent=2, sort_keys=True) + "\n")
        self.assertNotIn(str(ROOT), openapi)
        self.assertNotIn("fixture", openapi.casefold())
        self.assertIn("DO NOT EDIT", types)
        self.assertIn("OpenAPI SHA-256:", types)
        self.assertNotIn(" any", types)
        self.assertNotIn("@ts-ignore", types)

    def test_snapshot_covers_every_route_and_operation_once_with_real_models(self) -> None:
        # Given: the sole committed contract artifact.
        document = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        client = TestClient(create_app(WorkspaceRegistry(()), ROOT, AppConfig(ROOT, allow_unready=True)))

        # When: FastAPI's live route table is compared with the generated operation map.
        live = client.get("/openapi.json").json()
        document_routes = {
            (method.upper(), path, operation["operationId"])
            for path, path_item in document["paths"].items()
            for method, operation in path_item.items()
            if method in {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
        }
        live_routes = {
            (method.upper(), path, operation["operationId"])
            for path, path_item in live["paths"].items()
            for method, operation in path_item.items()
            if method in {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
        }
        application_routes = {
            (method, route.path, route.operation_id)
            for route in client.app.routes
            if isinstance(route, APIRoute) and route.include_in_schema
            for method in route.methods
        }

        # Then: each actual route appears exactly once and all command/error shapes are represented.
        self.assertEqual(document_routes, live_routes)
        self.assertEqual(document_routes, application_routes)
        self.assertEqual(len(document_routes), len({operation_id for _, _, operation_id in document_routes}))
        command_schema = document["components"]["schemas"]["CommandRequest"]
        self.assertEqual(
            ["start", "request-revision", "request-input", "create-defect", "escalate", "request-waiver", "submit-for-gate", "approve", "complete", "reject", "resolve", "resume"],
            command_schema["properties"]["command"]["enum"],
        )
        types = TYPES.read_text(encoding="utf-8")
        self.assertIn("ApiOperationMap", types)
        for path_item in document["paths"].values():
            for operation in path_item.values():
                if not isinstance(operation, dict) or "operationId" not in operation:
                    continue
                self.assertIn(json.dumps(operation["operationId"]), types)
                for status, response in operation["responses"].items():
                    self.assertIn(f'readonly "{status}":', types)
                    for media in response.get("content", {}).values():
                        reference = media.get("schema", {}).get("$ref")
                        if reference is not None:
                            self.assertIn(f"export type {reference.rsplit('/', 1)[1]} =", types)

    def test_check_rejects_any_drift_in_either_committed_artifact(self) -> None:
        # Given: the deterministic generator command.
        command = [sys.executable, "scripts/generate_operator_api_contracts.py", "--check"]

        # When: it evaluates the committed snapshot and TypeScript output in memory.
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)

        # Then: both artifacts match exactly without a package manager or network call.
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            expected = ("snapshot\n", "types\n", "registry\n")
            for relative, content in ((generator.SNAPSHOT_RELATIVE, expected[0]), (generator.TYPES_RELATIVE, expected[1]), (generator.PROMPT_REGISTRY_RELATIVE, expected[2])):
                target = temporary_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            with patch.object(generator, "ROOT", temporary_root), patch.object(generator, "generate_artifacts", return_value=expected[:2]), patch.object(generator, "generate_prompt_registry", return_value=expected[2]):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(0, generator.main(["--check"]))
                for relative, content in ((generator.SNAPSHOT_RELATIVE, expected[0]), (generator.TYPES_RELATIVE, expected[1]), (generator.PROMPT_REGISTRY_RELATIVE, expected[2])):
                    (temporary_root / relative).write_text("drift\n", encoding="utf-8")
                    with redirect_stderr(io.StringIO()):
                        self.assertEqual(1, generator.main(["--check"]))
                    (temporary_root / relative).write_text(content, encoding="utf-8")
