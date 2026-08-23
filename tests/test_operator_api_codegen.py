from __future__ import annotations

import json
import io
import hashlib
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
    def test_prompt_registry_refreshes_source_hashes_without_changing_other_entry_fields(self) -> None:
        # Given: a registry entry with stale hashes and source files containing exact bytes.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt_path = "prompts/example.xml.md"
            contract_path = "standards/contracts/example.json"
            prompt_bytes = b"<prompt>exact bytes</prompt>\n"
            contract_bytes = b'{"type":"object"}\n'
            (root / prompt_path).parent.mkdir(parents=True)
            (root / prompt_path).write_bytes(prompt_bytes)
            (root / contract_path).parent.mkdir(parents=True)
            (root / contract_path).write_bytes(contract_bytes)
            entry = {
                "prompt_id": "example",
                "prompt_path": prompt_path,
                "prompt_sha256": "stale-prompt",
                "owner": "operator",
                "output_contracts": [
                    {
                        "contract_path": contract_path,
                        "contract_sha256": "stale-contract",
                        "kind": "artifact",
                    }
                ],
            }
            registry_path = root / generator.PROMPT_REGISTRY_RELATIVE
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(json.dumps({"entries": [entry], "version": "1.0"}), encoding="utf-8")

            # When: the registry is regenerated from its registered sources.
            generated = json.loads(generator.generate_prompt_registry(root))

            # Then: only the source-derived digest fields change.
            expected = {
                **entry,
                "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
                "output_contracts": [
                    {
                        **entry["output_contracts"][0],
                        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
                    }
                ],
            }
            self.assertEqual({"entries": [expected], "version": "1.0"}, generated)

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

    def test_delivery_operations_emit_typed_models_parameters_statuses_and_download_metadata(self) -> None:
        # Given: the generated OpenAPI document and TypeScript contract.
        document = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        paths = document["paths"]
        types = TYPES.read_text(encoding="utf-8")
        prefix = "/v1/tenants/{tenant_id}/projects/{project_id}/delivery"

        # When: the five local delivery operations are selected from the contract.
        preview = paths[f"{prefix}/preview"]["get"]
        create = paths[f"{prefix}/exports"]["post"]
        history = paths[f"{prefix}/exports"]["get"]
        record = paths[f"{prefix}/exports/{{export_id}}"]["get"]
        download = paths[f"{prefix}/exports/{{export_id}}/download"]["get"]

        # Then: each operation has its public model, transport metadata, and generated client entry.
        self.assertEqual(
            {
                "previewDelivery",
                "createDeliveryExport",
                "listDeliveryExports",
                "getDeliveryExport",
                "downloadDeliveryExport",
            },
            {operation["operationId"] for operation in (preview, create, history, record, download)},
        )
        scope = next(parameter for parameter in preview["parameters"] if parameter["name"] == "scope")
        self.assertEqual("query", scope["in"])
        self.assertEqual("#/components/schemas/DeliveryScope", scope["schema"]["$ref"])
        self.assertEqual("#/components/schemas/DeliveryCreateRequest", create["requestBody"]["content"]["application/json"]["schema"]["$ref"])
        expected_statuses = {
            "preview": ({"200", "404", "422", "503"}, preview),
            "create": ({"200", "201", "404", "409", "422", "503"}, create),
            "history": ({"200", "404", "503"}, history),
            "record": ({"200", "404", "422", "503"}, record),
            "download": ({"200", "404", "422", "503"}, download),
        }
        for operation, (statuses, definition) in expected_statuses.items():
            with self.subTest(operation=operation):
                self.assertEqual(statuses, set(definition["responses"]))
                for status in statuses - {"200", "201"}:
                    self.assertEqual(
                        "#/components/schemas/ErrorEnvelope",
                        definition["responses"][status]["content"]["application/json"]["schema"]["$ref"],
                    )
        for status in ("200", "201"):
            self.assertEqual("#/components/schemas/DeliveryExportResult", create["responses"][status]["content"]["application/json"]["schema"]["$ref"])
        self.assertEqual("#/components/schemas/DeliveryExportHistoryResponse", history["responses"]["200"]["content"]["application/json"]["schema"]["$ref"])
        self.assertEqual("#/components/schemas/DeliveryPackageRecord", record["responses"]["200"]["content"]["application/json"]["schema"]["$ref"])
        zip_response = download["responses"]["200"]
        self.assertEqual("string", zip_response["content"]["application/zip"]["schema"]["type"])
        self.assertEqual("binary", zip_response["content"]["application/zip"]["schema"]["format"])
        self.assertEqual({"Content-Disposition", "ETag"}, set(zip_response["headers"]))
        create_schema = document["components"]["schemas"]["DeliveryCreateRequest"]
        self.assertFalse(create_schema["additionalProperties"])
        self.assertEqual(
            {"delivery_export_result_id", "delivery_package_id", "export_id", "export_request", "notion_import_request", "package_revision", "role_package_requests"},
            set(create_schema["properties"]),
        )
        self.assertEqual("#/components/schemas/DeliveryExportRequest", create_schema["properties"]["export_request"]["$ref"])
        self.assertEqual("#/components/schemas/DeliveryNotionRequest", create_schema["properties"]["notion_import_request"]["$ref"])
        self.assertEqual("#/components/schemas/DeliveryRolePackageRequest", create_schema["properties"]["role_package_requests"]["items"]["$ref"])
        self.assertEqual(["checkpoint", "final"], document["components"]["schemas"]["DeliveryScope"]["enum"])
        self.assertEqual(["copywriter", "developer", "project_management", "reviewer"], document["components"]["schemas"]["DeliveryRole"]["enum"])
        self.assertEqual(["not_started", "in_progress", "blocked", "done"], document["components"]["schemas"]["DeliveryImplementationTask"]["properties"]["status"]["enum"])
        self.assertEqual(["created", "replayed"], document["components"]["schemas"]["DeliveryExportResult"]["properties"]["replay_state"]["enum"])
        self.assertIn('export type DeliveryScope = "checkpoint" | "final";', types)
        self.assertIn('export type DeliveryRole = "copywriter" | "developer" | "project_management" | "reviewer";', types)
        self.assertIn('export type DeliveryCreateRequest =', types)
        self.assertIn('readonly "status" : "not_started" | "in_progress" | "blocked" | "done";', types)
        self.assertIn('readonly "replay_state" : "created" | "replayed";', types)
        self.assertIn('readonly "downloadDeliveryExport":', types)
        self.assertIn('readonly "201": DeliveryExportResult;', types)
        self.assertIn('readonly "200": Blob;', types)
        self.assertIn('readonly parameters: { readonly path:', types)
        self.assertIn('readonly query: { readonly "scope": DeliveryScope;', types)

    def test_generated_download_contract_has_a_separate_typed_response_header_map(self) -> None:
        types = TYPES.read_text(encoding="utf-8")

        self.assertIn('readonly responseHeaders: { readonly "200": { readonly "Content-Disposition": string; readonly "ETag": string; }; };', types)

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
