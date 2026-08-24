from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.hermes_runs_client import HermesRunResult, HermesRunUsage, HermesRunsError
from services.operator_api.hermes_runtime_provider import HermesRuntimeDispatch, HermesRuntimeOutput, HermesRuntimeProvider
from services.operator_api.models import JsonValue
from services.operator_api.recovery_inventory import RecoveryInventory
from services.operator_api.runtime import LocalRuntimeService, RuntimeProviderError
from tests.test_local_runtime import ROOT, RUN, TENANT, PROJECT, _profile, _request, _seed, _validator


def _hermes_profile() -> dict[str, JsonValue]:
    profile = _profile()
    profile["provider_capability_ref"] = {
        "provider_id": "provider-hermes",
        "provider_kind": "gateway",
        "capability_id": "capability-hermes-runs",
    }
    profile["model_policy"] = {
        "allowed_model_ids": ["gpt-5.6-sol"],
        "default_model_id": "gpt-5.6-sol",
    }
    return profile


def _result(output: str, model: str = "gpt-5.6-sol", last_event: str = "run.completed") -> HermesRunResult:
    return HermesRunResult(
        run_id="hermes-run-0001",
        session_id="llm-request-runtime-0-0001",
        model=model,
        last_event=last_event,
        output=output,
        usage=HermesRunUsage(input_tokens=11, output_tokens=7, total_tokens=18),
        created_at=1_787_097_600,
        updated_at=1_787_097_601,
    )


def _registry() -> dict[str, JsonValue]:
    return json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))


def _provider_request(contracts: list[dict[str, str]] | None = None) -> dict[str, JsonValue]:
    return {
        "llm_run_request_id": "llm-request-runtime-0-0001",
        "provider_id": "provider-hermes",
        "model_id": "gpt-5.6-sol",
        "tenant_id": TENANT,
        "project_id": PROJECT,
        "run_id": RUN,
        "step_id": "0",
        "idempotency_key": "idempotency-runtime-0-0001",
        "output_contracts": contracts or [{"contract_id": "https://heartweb.example/schema/manifest.schema.json"}],
    }


def _source_bytes() -> dict[str, bytes]:
    return {
        "prompt:0": b"<official>prompt</official>",
        "output-contract:0/1": b'{"contract":"manifest"}',
        "runtime:intake/intake-runtime-0001": b'{"accepted":true}',
    }


def _source_package(source_bytes: dict[str, bytes]) -> dict[str, JsonValue]:
    return {
        "context_package_id": "context-runtime-0-0001",
        "step_id": "0",
        "prompt": {"prompt_sha256": hashlib.sha256(source_bytes["prompt:0"]).hexdigest()},
        "output_contracts": [{"contract_sha256": hashlib.sha256(source_bytes["output-contract:0/1"]).hexdigest()}],
        "sources": [{
            "logical_ref": "runtime:intake/intake-runtime-0001",
            "content_sha256": hashlib.sha256(source_bytes["runtime:intake/intake-runtime-0001"]).hexdigest(),
        }],
    }


@dataclass(frozen=True, slots=True)
class BoundHermesClient:
    expected_input: str
    expected_instructions: str
    expected_session_id: str
    result: HermesRunResult

    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult:
        if (input_text, instructions, session_id) != (
            self.expected_input,
            self.expected_instructions,
            self.expected_session_id,
        ):
            raise AssertionError("Hermes dispatch did not preserve the runtime binding.")
        return self.result


@dataclass(frozen=True, slots=True)
class FailingHermesClient:
    error: HermesRunsError

    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult:
        raise self.error


@dataclass(frozen=True, slots=True)
class StaticHermesClient:
    result: HermesRunResult

    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult:
        return self.result


@dataclass(frozen=True, slots=True)
class FailIfCalledHermesClient:
    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult:
        raise AssertionError("The Hermes client must not execute for an invalid source envelope.")


@dataclass(slots=True)
class RecordingHermesClient:
    result: HermesRunResult
    inputs: list[str]

    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult:
        self.inputs.append(input_text)
        return self.result


@dataclass(frozen=True, slots=True)
class IdentityMismatchHermesProvider:
    client: StaticHermesClient

    def execute(self, dispatch: HermesRuntimeDispatch) -> HermesRuntimeOutput:
        output = HermesRuntimeProvider(self.client).execute(dispatch)
        primary = output.output_set.primary.model_copy(update={"tenant_id": "tenant-mismatch"})
        return replace(output, output_set=output.output_set.model_copy(update={"primary": primary}))


class HermesRuntimeProviderTests(unittest.TestCase):
    def test_binds_exact_accepted_step_zero_sources_into_canonical_input(self) -> None:
        source_bytes = _source_bytes()
        package = _source_package(source_bytes)
        request = _provider_request()
        expected_input = json.dumps({
            "context_package": package,
            "sources": [
                {"logical_ref": logical_ref, "sha256": hashlib.sha256(content).hexdigest(), "content": content.decode("utf-8")}
                for logical_ref, content in sorted(source_bytes.items())
            ],
        }, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        provider = HermesRuntimeProvider(BoundHermesClient(
            expected_input,
            "<official>prompt</official>\n\nReturn exactly one JSON object and no other text.",
            request["llm_run_request_id"],
            _result("{}"),
        ))

        output = provider.execute(HermesRuntimeDispatch(
            package, request, _hermes_profile(), "<official>prompt</official>", _registry(), 1, source_bytes,
        ))

        self.assertEqual(b"{}", output.output_bytes)

    def test_rejects_invalid_source_envelope_before_client_execution(self) -> None:
        source_bytes = _source_bytes()
        package = _source_package(source_bytes)
        invalid_cases = (
            ("mutation", {**source_bytes, "prompt:0": b"changed"}),
            ("missing", {key: value for key, value in source_bytes.items() if key != "prompt:0"}),
            ("renamed", {**{key: value for key, value in source_bytes.items() if key != "prompt:0"}, "prompt:renamed": source_bytes["prompt:0"]}),
            ("extra", {**source_bytes, "runtime:workspace/unrelated": b"must not enter"}),
            ("undecodable", {**source_bytes, "prompt:0": b"\xff"}),
            ("non-bytes", {**source_bytes, "prompt:0": "not bytes"}),
        )
        for name, invalid_source_bytes in invalid_cases:
            with self.subTest(case=name):
                with self.assertRaises(HermesRunsError) as raised:
                    HermesRuntimeProvider(FailIfCalledHermesClient()).execute(HermesRuntimeDispatch(
                        package, _provider_request(), _hermes_profile(), "<official>prompt</official>", _registry(), 1, invalid_source_bytes,
                    ))
                self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_rejects_malformed_or_conflicting_package_source_bindings_before_client_execution(self) -> None:
        source_bytes = _source_bytes()
        package = _source_package(source_bytes)
        source = package["sources"][0]
        cases = (
            ("missing-prompt-hash", {**package, "prompt": {}}),
            ("duplicate-source-ref", {**package, "sources": [source, source]}),
            ("conflicting-source-ref", {**package, "sources": [{"logical_ref": "prompt:0", "content_sha256": "0" * 64}]}),
        )
        for name, invalid_package in cases:
            with self.subTest(case=name):
                with self.assertRaises(HermesRunsError) as raised:
                    HermesRuntimeProvider(FailIfCalledHermesClient()).execute(HermesRuntimeDispatch(
                        invalid_package, _provider_request(), _hermes_profile(), "<official>prompt</official>", _registry(), 1, source_bytes,
                    ))
                self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_real_step_zero_dispatches_only_the_validated_source_mapping(self) -> None:
        content = (ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _seed(workspace, "0")
            (workspace / "unrelated.txt").write_bytes(b"must not enter")
            client = RecordingHermesClient(_result(content), [])
            service = LocalRuntimeService("real", None, RecoveryInventory(repository._registry), HermesRuntimeProvider(client))

            prepared = service.prepare_step(repository, ROOT, _validator(), _hermes_profile(), _request("0"))

            envelope = json.loads(client.inputs[0])
            source_entries = envelope["sources"]
            expected_sources = {
                "prompt:0": (ROOT / "prompts/0-kickoff.xml.md").read_bytes(),
                "output-contract:0/1": (ROOT / "standards/manifest.schema.json").read_bytes(),
                "runtime:intake/intake-runtime-0001": repository.source_bytes(TENANT, PROJECT, "intake"),
            }
            self.assertEqual(prepared.context_package, envelope["context_package"])
            self.assertEqual(sorted(expected_sources), [entry["logical_ref"] for entry in source_entries])
            self.assertEqual(
                [{"logical_ref": logical_ref, "sha256": hashlib.sha256(content).hexdigest(), "content": content.decode("utf-8")} for logical_ref, content in sorted(expected_sources.items())],
                source_entries,
            )

    def test_rejects_incompatible_capability_before_client_execution(self) -> None:
        profile = _hermes_profile()
        profile["provider_capability_ref"] = {
            "provider_id": "provider-other",
            "provider_kind": "gateway",
            "capability_id": "capability-hermes-runs",
        }
        request = _provider_request()
        client = BoundHermesClient("forbidden", "forbidden", "forbidden", _result("{}"))
        provider = HermesRuntimeProvider(client)

        with self.assertRaises(HermesRunsError) as raised:
            provider.execute(HermesRuntimeDispatch({}, request, profile, "prompt", _registry(), 1, _source_bytes()))
        self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_rejects_invalid_or_ambiguous_json_without_returning_output(self) -> None:
        request = _provider_request(
            [
                {"contract_id": "https://heartweb.example/schema/manifest.schema.json"},
                {"contract_id": "https://heartweb.example/schema/outputs/step-1-topic-inventory.schema.json"},
            ]
        )
        provider = HermesRuntimeProvider(BoundHermesClient("{}", "prompt\n\nReturn exactly one JSON object and no other text.", request["llm_run_request_id"], _result("not json")))

        with self.assertRaises(HermesRunsError) as raised:
            provider.execute(HermesRuntimeDispatch({}, request, _hermes_profile(), "prompt", _registry(), 1, _source_bytes()))
        self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

        request = _provider_request()
        for output in ("[]", "true", "before {}"):
            with self.subTest(output=output):
                source_bytes = _source_bytes()
                provider = HermesRuntimeProvider(StaticHermesClient(_result(output)))
                with self.assertRaises(HermesRunsError) as raised:
                    provider.execute(HermesRuntimeDispatch(_source_package(source_bytes), request, _hermes_profile(), "<official>prompt</official>", _registry(), 1, source_bytes))
                self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_rejects_model_mismatch_and_translates_safe_backend_errors(self) -> None:
        request = _provider_request()
        source_bytes = _source_bytes()
        provider = HermesRuntimeProvider(StaticHermesClient(_result("{}", "other-model")))

        with self.assertRaises(HermesRunsError) as raised:
            provider.execute(HermesRuntimeDispatch(_source_package(source_bytes), request, _hermes_profile(), "<official>prompt</official>", _registry(), 1, source_bytes))
        self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            service = LocalRuntimeService("real", None, RecoveryInventory(repository._registry), HermesRuntimeProvider(FailingHermesClient(HermesRunsError("ERROR_LLM_BACKEND_AUTH"))))
            request = _request("0")

            with self.assertRaises(RuntimeProviderError) as raised:
                service.prepare_step(repository, ROOT, _validator(), _hermes_profile(), request)

            self.assertEqual("ERROR_LLM_BACKEND_AUTH", raised.exception.code)
            self.assertNotIn("output", raised.exception.message.lower())
            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))

    def test_rejects_unexpected_terminal_event_before_return_or_persistence(self) -> None:
        content = (ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")
        provider = HermesRuntimeProvider(StaticHermesClient(_result(content, last_event="tool_call")))

        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            service = LocalRuntimeService("real", None, RecoveryInventory(repository._registry), provider)

            with self.assertRaises(RuntimeProviderError) as raised:
                service.prepare_step(repository, ROOT, _validator(), _hermes_profile(), _request("0"))

            self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)
            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))

    def test_rejects_hermes_output_identity_mismatch_before_validation_or_persistence(self) -> None:
        content = (ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")
        provider = IdentityMismatchHermesProvider(StaticHermesClient(_result(content)))

        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            service = LocalRuntimeService("real", None, RecoveryInventory(repository._registry), provider)

            with self.assertRaises(RuntimeProviderError) as raised:
                service.prepare_step(repository, ROOT, _validator(), _hermes_profile(), _request("0"))

            self.assertEqual("ERROR_RUNTIME_OUTPUT_IDENTITY_INVALID", raised.exception.code)
            self.assertNotIn("fixture", raised.exception.message.lower())
            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))

    def test_persists_validated_hermes_output_and_preserves_output_bytes(self) -> None:
        content = (ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            provider = HermesRuntimeProvider(StaticHermesClient(_result(content.decode("utf-8"))))
            service = LocalRuntimeService("real", None, RecoveryInventory(repository._registry), provider)
            request = _request("0")

            prepared = service.prepare_step(repository, ROOT, _validator(), _hermes_profile(), request)

            self.assertEqual(content, prepared.candidate_bytes)
            self.assertEqual("hermes-run-0001", prepared.llm_result["provider_run_id"])
            self.assertEqual("gpt-5.6-sol", prepared.llm_result["model_id"])
            self.assertEqual({"input_tokens": 11, "output_tokens": 7, "total_tokens": 18}, prepared.llm_result["token_usage"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), prepared.llm_result["output"]["content_sha256"])

    def test_invalid_hermes_output_leaves_projections_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            provider = HermesRuntimeProvider(StaticHermesClient(_result("{}")))
            service = LocalRuntimeService("real", None, RecoveryInventory(repository._registry), provider)

            with self.assertRaisesRegex(RuntimeProviderError, "ERROR_LLM_BACKEND_RESPONSE_INVALID"):
                service.prepare_step(repository, ROOT, _validator(), _hermes_profile(), _request("0"))

            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))


if __name__ == "__main__":
    unittest.main()
