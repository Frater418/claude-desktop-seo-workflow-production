from __future__ import annotations

import hashlib
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from pydantic import JsonValue, ValidationError

from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.runtime import LocalFixtureProvider


ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime(2026, 8, 20, tzinfo=UTC)


def registry() -> dict[str, JsonValue]:
    return json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))


def output(contract_id: str, content: bytes = b"candidate output", *, tenant_id: str = "tenant-1", parent_revision: int = 2) -> ProviderOutput:
    return ProviderOutput(
        contract_id=contract_id,
        content_bytes=content,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_type="application/json",
        tenant_id=tenant_id,
        project_id="project-1",
        run_id="run-1",
        step_id="1c",
        idempotency_key="idempotency-1",
        parent_revision=parent_revision,
        target_revision=3,
        created_at=CREATED_AT,
    )


def output_set(*, primary: ProviderOutput, supporting: tuple[ProviderOutput, ...] = ()) -> ProviderOutputSet:
    return ProviderOutputSet.from_registry(registry(), primary=primary, supporting=supporting)


class ProviderOutputTests(unittest.TestCase):
    def test_accepts_multi_output_step_with_exact_contracts_and_base64_bytes(self) -> None:
        # Given: the official two-contract registry entry and exact output bytes
        contract_ids = contract_ids_for("1c")
        primary = output(contract_ids[0])
        supporting = output(contract_ids[1], b'{"template":true}')
        # When: the provider returns both declared outputs
        result = output_set(primary=primary, supporting=(supporting,))
        # Then: the closed set preserves exact bytes with safe JSON encoding
        self.assertEqual((primary, supporting), result.outputs)
        self.assertEqual("Y2FuZGlkYXRlIG91dHB1dA==", result.primary.model_dump(mode="json")["content_bytes"])

    def test_rejects_unknown_duplicate_or_missing_declared_contracts(self) -> None:
        # Given: output declarations that disagree with the selected registry entry
        contract_ids = contract_ids_for("1c")
        cases = (
            (output("https://heartweb.example/schema/unknown.json"), (output(contract_ids[1]),)),
            (output(contract_ids[0]), (output(contract_ids[0]),)),
            (output(contract_ids[0]), ()),
        )
        # When: each invalid declaration is bound to the registry
        for primary, supporting in cases:
            with self.subTest(primary=primary.contract_id, supporting=len(supporting)):
                # Then: each required output contract is present exactly once
                with self.assertRaises(ValidationError):
                    output_set(primary=primary, supporting=supporting)

    def test_rejects_tampering_cross_identity_stale_revision_and_bad_content_type(self) -> None:
        # Given: outputs with one contract-level defect each
        contract_ids = contract_ids_for("1c")
        wrong_hash = output(contract_ids[0]).model_copy(update={"content_sha256": "0" * 64})
        cross_identity = output(contract_ids[1], tenant_id="tenant-other")
        malformed_content_type = output(contract_ids[1]).model_copy(update={"content_type": "not a media type"})
        cases = (wrong_hash, cross_identity, malformed_content_type)
        # When: each output is combined with the valid primary output
        for invalid in cases:
            with self.subTest(contract_id=invalid.contract_id, tenant_id=invalid.tenant_id, revision=invalid.parent_revision):
                # Then: validation fails at the closed provider-output boundary
                with self.assertRaises(ValidationError):
                    output_set(primary=output(contract_ids[0]), supporting=(invalid,))
        with self.assertRaises(ValidationError):
            output(contract_ids[1], parent_revision=1)
        with self.assertRaises(ValidationError):
            output(contract_ids[1], parent_revision=0)

    def test_fixture_provider_returns_the_typed_output_set(self) -> None:
        # Given: a validated provider output set
        contract_id = contract_ids_for("0")[0]
        result = output_set(primary=output(contract_id).model_copy(update={"step_id": "0"}))
        provider = LocalFixtureProvider("fixture-1", result)
        # When: its approved fixture is requested
        actual = provider.output("fixture-1", provider.fixture_sha256)
        # Then: callers receive the typed set rather than bare bytes
        self.assertIs(result, actual)

    def test_fixture_authorization_hashes_supporting_outputs(self) -> None:
        contract_ids = contract_ids_for("1c")
        primary = output(contract_ids[0])
        first = LocalFixtureProvider("fixture-1", output_set(primary=primary, supporting=(output(contract_ids[1], b'{"template":"first"}'),)))
        second = LocalFixtureProvider("fixture-1", output_set(primary=primary, supporting=(output(contract_ids[1], b'{"template":"second"}'),)))

        self.assertNotEqual(first.fixture_sha256, second.fixture_sha256)
        with self.assertRaisesRegex(RuntimeError, "ERROR_LOCAL_FIXTURE_UNAVAILABLE"):
            first.output("fixture-1", second.fixture_sha256)


def contract_ids_for(step_id: str) -> tuple[str, ...]:
    entries = registry()["entries"]
    assert isinstance(entries, list)
    entry = next(entry for entry in entries if isinstance(entry, dict) and entry["step_id"] == step_id)
    contracts = entry["output_contracts"]
    assert isinstance(contracts, list)
    return tuple(contract["contract_id"] for contract in contracts if isinstance(contract, dict))


if __name__ == "__main__":
    unittest.main()
