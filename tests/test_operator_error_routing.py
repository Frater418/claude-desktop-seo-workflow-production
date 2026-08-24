from __future__ import annotations

import ast
import copy
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.delivery.record_normalization import DeliveryInventoryError
from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from services.operator_routing.router import (
    CANONICAL_RUNTIME_ERROR_CODES,
    ErrorRoutingPolicyError,
    load_policy,
    route_error,
    validate_policy,
)
from services.transition_service.service import durable_ledger_lock, main as transition_main
from tests.support.delivery_api import PROJECT, TENANT, delivery_base, delivery_request, seed_workspace


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ERROR_CODE = re.compile(r"^(?:ERR|ERROR)_[A-Z0-9_]+$")


def emitted_runtime_error_codes() -> set[str]:
    emitted_codes: set[str] = set()
    for source_path in sorted((ROOT / "services").rglob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        emitters = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and _returns_code_payload(node)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                emitted_codes.update(_literal_error_codes(node.exc))
            elif isinstance(node, ast.Call) and _call_name(node) in emitters:
                emitted_codes.update(_literal_error_codes(node))
            elif isinstance(node, ast.Call) and _call_name(node) == "append":
                emitted_codes.update(_literal_error_codes(node))
            elif isinstance(node, ast.Dict) and _is_literal_code_payload(node):
                emitted_codes.update(_literal_error_codes(node))
    return emitted_codes


def _returns_code_payload(function: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Return)
        and node.value is not None
        and any(_is_code_payload(item) for item in ast.walk(node.value) if isinstance(item, ast.Dict))
        for node in ast.walk(function)
    )


def _is_literal_code_payload(node: ast.Dict) -> bool:
    return any(
        isinstance(key, ast.Constant)
        and key.value == "code"
        and isinstance(value, ast.Constant)
        and isinstance(value.value, str)
        and RUNTIME_ERROR_CODE.fullmatch(value.value)
        for key, value in zip(node.keys, node.values, strict=True)
    )


def _is_code_payload(node: ast.Dict) -> bool:
    return any(
        isinstance(key, ast.Constant) and key.value == "code"
        for key in node.keys
    )


def _call_name(node: ast.Call) -> str | None:
    match node.func:
        case ast.Name(id=name):
            return name
        case ast.Attribute(attr=name):
            return name
        case _:
            return None


def _literal_error_codes(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    return {
        value.value
        for value in ast.walk(node)
        if isinstance(value, ast.Constant)
        and isinstance(value.value, str)
        and RUNTIME_ERROR_CODE.fullmatch(value.value)
    }


class OperatorErrorRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy(ROOT)

    def test_every_canonical_runtime_code_has_one_route_and_owner(self) -> None:
        result = validate_policy(self.policy)

        self.assertTrue(result.valid, result.errors)
        for code in result.canonical_codes:
            route = route_error(code, self.policy)
            self.assertTrue(route.route)
            self.assertTrue(route.owner_type)

    def test_every_emitted_runtime_error_code_is_canonical_and_routed(self) -> None:
        emitted_codes = emitted_runtime_error_codes()

        self.assertTrue(emitted_codes)
        self.assertEqual(set(), emitted_codes.difference(CANONICAL_RUNTIME_ERROR_CODES))
        for code in sorted(emitted_codes):
            route = route_error(code, self.policy)
            self.assertTrue(route.route)
            self.assertTrue(route.owner_type)

    def test_context_builder_codes_have_exactly_one_canonical_route(self) -> None:
        codes = (
            "ERROR_CONTEXT_SCHEMA_INVALID", "ERROR_CONTEXT_IDENTITY_MISMATCH", "ERROR_CONTEXT_SOURCE_INVALID",
            "ERROR_CONTEXT_PROMPT_BINDING_INVALID", "ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID", "ERROR_CONTEXT_PREDECESSOR_INVALID",
            "ERROR_CONTEXT_REVISION_BINDING_INVALID", "ERROR_CONTEXT_TRUST_POLICY_INVALID", "ERROR_CONTEXT_PACKAGE_HASH_MISMATCH",
            "ERROR_LLM_REQUEST_INVALID", "ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT", "ERROR_LLM_RESULT_INVALID",
            "ERROR_TECHNICAL_SESSION_POLICY_DENIED",
        )

        for code in codes:
            self.assertEqual(1, sum(mapping["code"] == code for mapping in self.policy["mappings"]))
            self.assertEqual(code, route_error(code, self.policy).code)

    def test_duplicate_mapping_fails_deterministically(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["mappings"].append(copy.deepcopy(policy["mappings"][0]))

        result = validate_policy(policy)

        self.assertFalse(result.valid)
        self.assertIn("ERROR_OPERATOR_ROUTING_DUPLICATE", result.errors)

    def test_missing_canonical_mapping_fails_deterministically(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["mappings"] = policy["mappings"][1:]

        result = validate_policy(policy)

        self.assertFalse(result.valid)
        self.assertIn("ERROR_OPERATOR_ROUTING_MISSING", result.errors)

    def test_unknown_runtime_code_is_rejected(self) -> None:
        with self.assertRaises(ErrorRoutingPolicyError) as context:
            route_error("ERROR_NOT_A_RUNTIME_CODE", self.policy)

        self.assertEqual("ERROR_OPERATOR_ROUTING_UNKNOWN_CODE", context.exception.code)

    def test_policy_addition_cannot_redefine_inventory_and_is_rejected_as_unknown(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["mappings"].append(
            {
                "code": "ERROR_NOT_IN_CANONICAL_RUNTIME_INVENTORY",
                "route": "workflow_defect",
                "owner_type": "workflow_maintainer",
            }
        )

        result = validate_policy(policy)

        self.assertEqual(tuple(sorted(CANONICAL_RUNTIME_ERROR_CODES)), result.canonical_codes)
        self.assertFalse(result.valid)
        self.assertIn("ERROR_OPERATOR_ROUTING_UNKNOWN_MAPPING", result.errors)

    def test_policy_document_validates_against_its_schema(self) -> None:
        from jsonschema import Draft202012Validator

        schema = json.loads(
            (ROOT / "standards" / "operator" / "error-routing-policy.schema.json").read_text(encoding="utf-8")
        )

        errors = list(Draft202012Validator(schema).iter_errors(self.policy))

        self.assertEqual([], errors)

    def test_real_transition_ledger_contention_is_routed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ledger_path = Path(temporary_directory) / "transition-ledger.json"
            request_path = Path(temporary_directory) / "request.json"
            request_path.write_text("{}", encoding="utf-8")
            with durable_ledger_lock(ledger_path):
                stderr = io.StringIO()
                arguments = [
                    "transition_service.py",
                    "--request", str(request_path),
                    "--output", str(Path(temporary_directory) / "result.json"),
                    "--ledger", str(ledger_path),
                ]
                with patch.object(sys, "argv", arguments):
                    with contextlib.redirect_stderr(stderr):
                        return_code = transition_main()

        contention_code = stderr.getvalue().split(":", maxsplit=1)[0]
        route = route_error(contention_code, self.policy)

        self.assertEqual(2, return_code)
        self.assertEqual("ERROR_TRANSITION_LEDGER_LOCKED", contention_code)
        self.assertEqual("retryable_technical", route.route)
        self.assertEqual("workflow_maintainer", route.owner_type)

    def test_delivery_inventory_errors_from_each_composition_seam_are_stable_422_responses(self) -> None:
        seams = (
            ("inventory", "collect_inventory", "DELIVERY_SOURCE_RECORD_MALFORMED"),
            ("role", "build_role_package", "ROLE_PACKAGE_EMPTY"),
            ("notion", "build_notion_import_pack", "NOTION_RELATION_DANGLING"),
            ("archive", "build_archive", "DELIVERY_ARCHIVE_EMPTY"),
            ("semantic", "validate_delivery_contracts", "DELIVERY_PACKAGE_SCOPE_INVALID"),
        )
        for seam, target, code in seams:
            with self.subTest(seam=seam), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
                client = TestClient(create_app(registry, ROOT, AppConfig(ROOT)), raise_server_exceptions=False)
                with patch(f"services.operator_api.delivery_composer.{target}", side_effect=DeliveryInventoryError(code, "stable semantic failure")):
                    response = client.post(f"{delivery_base()}/exports", json=delivery_request())

                self.assertEqual(422, response.status_code)
                self.assertEqual(code, response.json()["code"])


if __name__ == "__main__":
    unittest.main()
