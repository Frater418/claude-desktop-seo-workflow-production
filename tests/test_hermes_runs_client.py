from __future__ import annotations

import copy
import json
import socket
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from services.operator_api.hermes_runs_client import HermesRunsClient, HermesRunsConfig, HermesRunsError


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "hermes_gateway"
API_KEY = "test-api-key-not-a-secret"
RUN_ID = "run_sanitized_001"
SESSION_ID = "session_sanitized_001"


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, exception_type: object, exception: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def config() -> HermesRunsConfig:
    return HermesRunsConfig(
        base_url="http://127.0.0.1:39001",
        api_key=API_KEY,
        timeout_seconds=5.0,
        poll_interval_seconds=0.25,
    )


class HermesRunsClientTests(unittest.TestCase):
    def test_execute_posts_exact_request_and_returns_completed_observation(self) -> None:
        create_request = load_fixture("create-request.json")
        started_response = load_fixture("started-response.json")
        running_response = load_fixture("running-response.json")
        completed_response = load_fixture("completed-response.json")
        self.assertEqual("hermes.run", running_response["object"])
        opened = Mock(side_effect=[FakeResponse(started_response), FakeResponse(running_response), FakeResponse(completed_response)])

        with (
            patch("services.operator_api.hermes_runs_client.urlopen", opened),
            patch("services.operator_api.hermes_runs_client.monotonic", side_effect=[0.0, 0.0]),
            patch("services.operator_api.hermes_runs_client.sleep") as slept,
        ):
            result = HermesRunsClient(config()).execute(
                input_text=create_request["input"],
                instructions=create_request["instructions"],
                session_id=create_request["session_id"],
            )

        self.assertEqual(RUN_ID, result.run_id)
        self.assertEqual(SESSION_ID, result.session_id)
        self.assertEqual("gpt-5.6-sol", result.model)
        self.assertEqual("run.completed", result.last_event)
        self.assertEqual("{\"marker\":\"sanitized-neutral\"}", result.output)
        self.assertEqual(12, result.usage.input_tokens)
        self.assertEqual(8, result.usage.output_tokens)
        self.assertEqual(20, result.usage.total_tokens)
        self.assertEqual(1787486400, result.created_at)
        self.assertEqual(1787486401, result.updated_at)
        create_call = opened.call_args_list[0]
        request = create_call.args[0]
        self.assertEqual("POST", request.get_method())
        self.assertEqual("http://127.0.0.1:39001/v1/runs", request.full_url)
        self.assertEqual(create_request, json.loads(request.data.decode("utf-8")))
        self.assertEqual(f"Bearer {API_KEY}", request.get_header("Authorization"))
        self.assertEqual("application/json", request.get_header("Content-type"))
        self.assertEqual(
            ["http://127.0.0.1:39001/v1/runs/run_sanitized_001", "http://127.0.0.1:39001/v1/runs/run_sanitized_001"],
            [call_entry.args[0].full_url for call_entry in opened.call_args_list[1:]],
        )
        slept.assert_called_once_with(0.25)

    def test_execute_rejects_invalid_completed_response_without_leaking_output(self) -> None:
        started_response = load_fixture("started-response.json")
        completed_response = load_fixture("completed-response.json")
        completed_response["output"] = "OAuth access_token customer-secret"
        completed_response["usage"] = {"input_tokens": 12, "output_tokens": 8, "total_tokens": 19}

        with patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse(completed_response)]), patch("services.operator_api.hermes_runs_client.monotonic", return_value=0.0), patch("services.operator_api.hermes_runs_client.sleep"):
            with self.assertRaises(HermesRunsError) as raised:
                HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

        self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)
        self.assertNotIn("customer-secret", str(raised.exception))
        self.assertNotIn("OAuth", str(raised.exception))

    def test_execute_maps_auth_and_connection_failures_to_safe_codes(self) -> None:
        auth_error = HTTPError("http://127.0.0.1:39001/v1/runs", 401, "Unauthorized", None, None)

        for failure, expected_code in ((auth_error, "ERROR_LLM_BACKEND_AUTH"), (URLError(socket.gaierror("unreachable")), "ERROR_LLM_BACKEND_UNAVAILABLE")):
            with self.subTest(expected_code=expected_code), patch("services.operator_api.hermes_runs_client.urlopen", side_effect=failure):
                with self.assertRaises(HermesRunsError) as raised:
                    HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

            self.assertEqual(expected_code, raised.exception.code)
            self.assertNotIn(API_KEY, str(raised.exception))
            self.assertNotIn("Authorization", str(raised.exception))

    def test_execute_times_out_after_started_poll(self) -> None:
        started_response = load_fixture("started-response.json")
        timeout_config = HermesRunsConfig(
            base_url="http://127.0.0.1:39001",
            api_key=API_KEY,
            timeout_seconds=1.0,
            poll_interval_seconds=0.25,
        )

        with patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse(started_response)]), patch("services.operator_api.hermes_runs_client.monotonic", side_effect=[0.0, 1.0]), patch("services.operator_api.hermes_runs_client.sleep") as slept:
            with self.assertRaises(HermesRunsError) as raised:
                HermesRunsClient(timeout_config).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

        self.assertEqual("ERROR_LLM_BACKEND_TIMEOUT", raised.exception.code)
        slept.assert_not_called()

    def test_execute_fails_closed_for_terminal_failures_and_interaction(self) -> None:
        started_response = load_fixture("started-response.json")
        cases = (("failed", "ERROR_LLM_BACKEND_RUN_FAILED"), ("cancelled", "ERROR_LLM_BACKEND_RUN_FAILED"), ("approval_required", "ERROR_LLM_BACKEND_INTERACTION_REQUIRED"), ("unknown", "ERROR_LLM_BACKEND_RUN_FAILED"))

        for status, expected_code in cases:
            with self.subTest(status=status), patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse({"run_id": RUN_ID, "status": status})]), patch("services.operator_api.hermes_runs_client.monotonic", return_value=0.0), patch("services.operator_api.hermes_runs_client.sleep"):
                with self.assertRaises(HermesRunsError) as raised:
                    HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

            self.assertEqual(expected_code, raised.exception.code)

    def test_config_rejects_non_loopback_url_and_empty_key_without_exposure(self) -> None:
        for base_url, api_key in (("https://gateway.example.test", API_KEY), ("http://127.0.0.1:39001", "")):
            with self.subTest(base_url=base_url), self.assertRaises(HermesRunsError) as raised:
                HermesRunsConfig(base_url=base_url, api_key=api_key, timeout_seconds=1.0, poll_interval_seconds=0.25)

            self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)
            self.assertNotIn(raised.exception.code, {"AUTH", "UNAVAILABLE", "TIMEOUT", "RUN_FAILED", "INTERACTION_REQUIRED", "RESPONSE_INVALID"})
            self.assertNotIn(API_KEY, str(raised.exception))

    def test_completed_response_rejects_session_mismatch(self) -> None:
        started_response = load_fixture("started-response.json")
        malformed = copy.deepcopy(load_fixture("completed-response.json"))
        malformed["session_id"] = "session_sanitized_other"

        with patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse(malformed)]), patch("services.operator_api.hermes_runs_client.monotonic", return_value=0.0), patch("services.operator_api.hermes_runs_client.sleep"):
            with self.assertRaises(HermesRunsError) as raised:
                HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

        self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_completed_response_rejects_extra_and_invalid_usage_values(self) -> None:
        started_response = load_fixture("started-response.json")

        for case in ("missing_object", "extra", "non_integer", "negative"):
            with self.subTest(case=case):
                malformed = copy.deepcopy(load_fixture("completed-response.json"))
                if case == "missing_object":
                    del malformed["object"]
                elif case == "extra":
                    malformed["unexpected"] = True
                elif case == "non_integer":
                    malformed["usage"]["input_tokens"] = True
                else:
                    malformed["usage"]["output_tokens"] = -1

                with patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse(malformed)]), patch("services.operator_api.hermes_runs_client.monotonic", return_value=0.0), patch("services.operator_api.hermes_runs_client.sleep"):
                    with self.assertRaises(HermesRunsError) as raised:
                        HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

                self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_completed_response_rejects_string_and_negative_timestamps(self) -> None:
        started_response = load_fixture("started-response.json")

        for field, value in (("created_at", "1787486400"), ("updated_at", -1)):
            with self.subTest(field=field), patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse({**load_fixture("completed-response.json"), field: value})]), patch("services.operator_api.hermes_runs_client.monotonic", return_value=0.0), patch("services.operator_api.hermes_runs_client.sleep"):
                with self.assertRaises(HermesRunsError) as raised:
                    HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

            self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)

    def test_running_response_rejects_contract_drift(self) -> None:
        started_response = load_fixture("started-response.json")
        completed_response = load_fixture("completed-response.json")
        cases = (
            ("run_id", "run_sanitized_other"),
            ("session_id", "session_sanitized_other"),
            ("model", "gpt-5.6-other"),
            ("created_at", "1787486400"),
            ("updated_at", -1),
            ("unexpected", True),
        )

        for field, value in cases:
            with self.subTest(field=field):
                running_response = copy.deepcopy(load_fixture("running-response.json"))
                running_response[field] = value

                with patch("services.operator_api.hermes_runs_client.urlopen", side_effect=[FakeResponse(started_response), FakeResponse(running_response), FakeResponse(completed_response)]), patch("services.operator_api.hermes_runs_client.monotonic", side_effect=[0.0, 0.0]), patch("services.operator_api.hermes_runs_client.sleep"):
                    with self.assertRaises(HermesRunsError) as raised:
                        HermesRunsClient(config()).execute(input_text="input", instructions="instructions", session_id=SESSION_ID)

                self.assertEqual("ERROR_LLM_BACKEND_RESPONSE_INVALID", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
