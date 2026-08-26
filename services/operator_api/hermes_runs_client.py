from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import dataclass, replace
from threading import Lock, Thread
from time import monotonic, sleep
from typing import Final, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import SplitResult, urlsplit
from urllib.request import Request, urlopen


ErrorCode = Literal[
    "ERROR_LLM_BACKEND_AUTH",
    "ERROR_LLM_BACKEND_UNAVAILABLE",
    "ERROR_LLM_BACKEND_TIMEOUT",
    "ERROR_LLM_BACKEND_RUN_FAILED",
    "ERROR_LLM_BACKEND_INTERACTION_REQUIRED",
    "ERROR_LLM_BACKEND_RESPONSE_INVALID",
]

_SAFE_MESSAGES: Final[dict[ErrorCode, str]] = {
    "ERROR_LLM_BACKEND_AUTH": "Hermes Runs authentication failed.",
    "ERROR_LLM_BACKEND_UNAVAILABLE": "Hermes Runs is unavailable.",
    "ERROR_LLM_BACKEND_TIMEOUT": "Hermes Runs did not complete before the timeout.",
    "ERROR_LLM_BACKEND_RUN_FAILED": "Hermes Runs failed closed.",
    "ERROR_LLM_BACKEND_INTERACTION_REQUIRED": "Hermes Runs requires an unsupported interaction.",
    "ERROR_LLM_BACKEND_RESPONSE_INVALID": "Hermes Runs returned an invalid response.",
}
_STARTED_KEYS: Final[frozenset[str]] = frozenset({"run_id", "status"})
_COMPLETED_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"object", "run_id", "status", "updated_at", "created_at", "session_id", "model", "last_event", "output", "usage"}
)
_COMPLETED_OPTIONAL_KEYS: Final[frozenset[str]] = frozenset({"pending_steer"})
_RUNNING_REQUIRED_KEYS: Final[frozenset[str]] = frozenset({"object", "run_id", "status", "created_at", "updated_at", "session_id", "model"})
_RUNNING_OPTIONAL_KEYS: Final[frozenset[str]] = frozenset({"last_event"})
_USAGE_KEYS: Final[frozenset[str]] = frozenset({"input_tokens", "output_tokens", "total_tokens"})


@dataclass(frozen=True, slots=True)
class HermesRunsError(RuntimeError):
    code: ErrorCode

    def __str__(self) -> str:
        return _SAFE_MESSAGES[self.code]


@dataclass(frozen=True, slots=True)
class HermesRunsConfig:
    base_url: str
    api_key: str
    timeout_seconds: float
    poll_interval_seconds: float

    def __post_init__(self) -> None:
        parsed = urlsplit(self.base_url)
        if not self.api_key.strip() or not _is_loopback_url(parsed) or not _is_positive_number(self.timeout_seconds) or not _is_positive_number(self.poll_interval_seconds):
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))


@dataclass(frozen=True, slots=True)
class HermesRunUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True, slots=True)
class HermesRunResult:
    run_id: str
    session_id: str
    model: str
    last_event: str
    output: str
    usage: HermesRunUsage
    created_at: int | float
    updated_at: int | float
    events: tuple[dict[str, object], ...] = ()
    event_stream_error: ErrorCode | None = None


@dataclass(frozen=True, slots=True)
class HermesRunHandle:
    run_id: str
    session_id: str


@dataclass(frozen=True, slots=True)
class HermesRunWaiting:
    run_id: str
    session_id: str
    status: Literal["interaction_required", "approval_required"]


class HermesRunsClient:
    def __init__(self, config: HermesRunsConfig) -> None:
        self._config = config

    def execute(
        self,
        *,
        input_text: str,
        instructions: str,
        session_id: str,
        model: str | None = None,
        provider: str | None = None,
        reasoning_effort: str | None = None,
    ) -> HermesRunResult:
        handle = self.start(
            input_text=input_text,
            instructions=instructions,
            session_id=session_id,
            model=model,
            provider=provider,
            reasoning_effort=reasoning_effort,
        )
        return self.wait(handle)

    def start(
        self,
        *,
        input_text: str,
        instructions: str,
        session_id: str,
        model: str | None = None,
        provider: str | None = None,
        reasoning_effort: str | None = None,
    ) -> HermesRunHandle:
        if session_id == "":
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        payload: dict[str, object] = {"input": input_text, "instructions": instructions, "session_id": session_id}
        if model is not None:
            payload["model"] = model
        if provider is not None:
            payload["provider"] = provider
        if reasoning_effort is not None:
            payload["model_options"] = {"reasoning_effort": reasoning_effort}
        started = _parse_started(self._request_json("POST", "/v1/runs", payload))
        return HermesRunHandle(started.run_id, session_id)

    def wait(self, handle: HermesRunHandle, *, timeout_seconds: int | None = None) -> HermesRunResult:
        effective_timeout = timeout_seconds or self._config.timeout_seconds
        if effective_timeout <= 0:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        events = _EventCollector(self, handle.run_id, effective_timeout)
        events.start()
        deadline = monotonic() + effective_timeout
        while True:
            try:
                terminal = self._poll(handle.run_id, handle.session_id)
            except HermesRunsError as error:
                if error.code != "ERROR_LLM_BACKEND_INTERACTION_REQUIRED":
                    self._best_effort_stop(handle.run_id)
                events.finish()
                raise
            if isinstance(terminal, HermesRunWaiting):
                events.finish()
                raise HermesRunsError("ERROR_LLM_BACKEND_INTERACTION_REQUIRED")
            if terminal is not None:
                observed, stream_error = events.finish()
                return replace(terminal, events=observed, event_stream_error=stream_error)
            if monotonic() >= deadline:
                self._best_effort_stop(handle.run_id)
                events.finish()
                raise HermesRunsError("ERROR_LLM_BACKEND_TIMEOUT")
            sleep(self._config.poll_interval_seconds)

    def steer(self, run_id: str, input_text: str) -> bool:
        if not input_text.strip():
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        response = self._request_json("POST", f"/v1/runs/{run_id}/steer", {"input": input_text})
        if set(response) != {"object", "run_id", "accepted"} or response.get("object") != "hermes.run.steer" or response.get("run_id") != run_id or response.get("accepted") is not True:
            raise HermesRunsError("ERROR_LLM_BACKEND_INTERACTION_REQUIRED")
        return True

    def approve_once(self, run_id: str, *, allow: bool) -> int:
        choice = "once" if allow else "deny"
        response = self._request_json("POST", f"/v1/runs/{run_id}/approval", {"choice": choice, "resolve_all": False})
        resolved = response.get("resolved")
        if not isinstance(resolved, int) or isinstance(resolved, bool) or resolved != 1:
            raise HermesRunsError("ERROR_LLM_BACKEND_INTERACTION_REQUIRED")
        return resolved

    def stop(self, run_id: str) -> None:
        response = self._request_json("POST", f"/v1/runs/{run_id}/stop", None)
        if response.get("run_id") != run_id or response.get("status") != "stopping":
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")

    def _event_stream(self, run_id: str, timeout_seconds: int) -> tuple[dict[str, object], ...]:
        request = Request(
            f"{self._config.base_url}/v1/runs/{run_id}/events",
            method="GET",
            headers={"Authorization": f"Bearer {self._config.api_key}", "Accept": "text/event-stream"},
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                data_lines: list[str] = []
                events: list[dict[str, object]] = []
                for raw_line in response:
                    line = raw_line.decode("utf-8").rstrip("\r\n")
                    if line == "":
                        if data_lines:
                            events.append(_parse_event("\n".join(data_lines)))
                            data_lines.clear()
                        continue
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                if data_lines:
                    events.append(_parse_event("\n".join(data_lines)))
                return tuple(events)
        except HTTPError as error:
            code: ErrorCode = "ERROR_LLM_BACKEND_AUTH" if error.code in {401, 403} else "ERROR_LLM_BACKEND_UNAVAILABLE"
            raise HermesRunsError(code) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            code = "ERROR_LLM_BACKEND_TIMEOUT" if isinstance(error, (TimeoutError, socket.timeout)) else "ERROR_LLM_BACKEND_UNAVAILABLE"
            raise HermesRunsError(code) from error
        except UnicodeDecodeError as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error

    def _best_effort_stop(self, run_id: str) -> None:
        try:
            self.stop(run_id)
        except HermesRunsError:
            return

    def inspect(self, handle: HermesRunHandle) -> HermesRunResult | HermesRunWaiting | None:
        observed = self._poll(handle.run_id, handle.session_id)
        if not isinstance(observed, HermesRunResult):
            return observed
        try:
            events = self._event_stream(handle.run_id, int(min(self._config.timeout_seconds, 60)))
        except HermesRunsError as error:
            return replace(observed, event_stream_error=error.code)
        return replace(observed, events=events)

    def _poll(self, run_id: str, session_id: str) -> HermesRunResult | HermesRunWaiting | None:
        response = self._request_json("GET", f"/v1/runs/{run_id}", None)
        status = _parse_status(response, run_id)
        match status:
            case "started":
                if set(response) != _STARTED_KEYS:
                    raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
                return None
            case "running":
                _parse_running(response, run_id, session_id)
                return None
            case "completed":
                return _parse_completed(response, run_id, session_id)
            case "interaction_required" | "approval_required":
                if set(response) != _STARTED_KEYS:
                    raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
                return HermesRunWaiting(run_id=run_id, session_id=session_id, status=status)
            case "failed" | "cancelled":
                if set(response) != _STARTED_KEYS:
                    raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
                raise HermesRunsError("ERROR_LLM_BACKEND_RUN_FAILED")
            case _:
                if set(response) != _STARTED_KEYS:
                    raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
                raise HermesRunsError("ERROR_LLM_BACKEND_RUN_FAILED")

    def _request_json(self, method: Literal["GET", "POST"], path: str, payload: dict[str, object] | None) -> dict[str, object]:
        body = None if payload is None else json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self._config.base_url}{path}",
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self._config.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            match error.code:
                case 401 | 403:
                    raise HermesRunsError("ERROR_LLM_BACKEND_AUTH") from error
                case _:
                    raise HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE") from error
        except (URLError, TimeoutError, socket.timeout) as error:
            code: ErrorCode = "ERROR_LLM_BACKEND_TIMEOUT" if isinstance(error, (TimeoutError, socket.timeout)) else "ERROR_LLM_BACKEND_UNAVAILABLE"
            raise HermesRunsError(code) from error
        except UnicodeDecodeError as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
        if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        return value


@dataclass(frozen=True, slots=True)
class _StartedRun:
    run_id: str


class _EventCollector:
    def __init__(self, client: HermesRunsClient, run_id: str, timeout_seconds: int) -> None:
        self._client = client
        self._run_id = run_id
        self._timeout_seconds = timeout_seconds
        self._lock = Lock()
        self._events: tuple[dict[str, object], ...] = ()
        self._error: ErrorCode | None = None
        self._thread = Thread(target=self._collect, name=f"hermes-events-{run_id}", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def finish(self) -> tuple[tuple[dict[str, object], ...], ErrorCode | None]:
        self._thread.join(timeout=2.0)
        with self._lock:
            if self._thread.is_alive() and self._error is None:
                self._error = "ERROR_LLM_BACKEND_TIMEOUT"
            return self._events, self._error

    def _collect(self) -> None:
        try:
            observed = self._client._event_stream(self._run_id, self._timeout_seconds)
        except HermesRunsError as error:
            with self._lock:
                self._error = error.code
            return
        with self._lock:
            self._events = observed


def _is_loopback_url(parsed: SplitResult) -> bool:
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        return False
    if parsed.hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        return False


def _is_positive_number(value: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _parse_started(value: dict[str, object]) -> _StartedRun:
    run_id = _required_string(value, "run_id")
    if set(value) != _STARTED_KEYS or value.get("status") != "started":
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return _StartedRun(run_id)


def _parse_event(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value) or not _is_non_empty_string(value.get("event")):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return value


def _parse_status(value: dict[str, object], expected_run_id: str) -> str:
    status = _required_string(value, "status")
    if value.get("run_id") != expected_run_id:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return status


def _parse_completed(value: dict[str, object], expected_run_id: str, expected_session_id: str) -> HermesRunResult:
    keys = set(value)
    if not _COMPLETED_REQUIRED_KEYS.issubset(keys) or keys - _COMPLETED_REQUIRED_KEYS - _COMPLETED_OPTIONAL_KEYS or value.get("status") != "completed" or value.get("run_id") != expected_run_id:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    if value.get("pending_steer") is not None:
        raise HermesRunsError("ERROR_LLM_BACKEND_INTERACTION_REQUIRED")
    _required_string(value, "object")
    required_strings = ("session_id", "model", "last_event", "output")
    strings = {key: _required_string(value, key) for key in required_strings}
    if strings["session_id"] != expected_session_id:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    usage = _parse_usage(value["usage"])
    return HermesRunResult(
        run_id=expected_run_id,
        session_id=expected_session_id,
        model=strings["model"],
        last_event=strings["last_event"],
        output=strings["output"],
        usage=usage,
        created_at=_required_epoch(value, "created_at"),
        updated_at=_required_epoch(value, "updated_at"),
    )


def _parse_running(value: dict[str, object], expected_run_id: str, expected_session_id: str) -> None:
    keys = set(value)
    if not _RUNNING_REQUIRED_KEYS.issubset(keys) or keys - _RUNNING_REQUIRED_KEYS - _RUNNING_OPTIONAL_KEYS or value.get("status") != "running" or value.get("run_id") != expected_run_id:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    if _required_string(value, "object") != "hermes.run" or _required_string(value, "session_id") != expected_session_id or _required_string(value, "model") != "gpt-5.6-sol":
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    if "last_event" in value:
        _required_string(value, "last_event")
    _required_epoch(value, "created_at")
    _required_epoch(value, "updated_at")


def _parse_usage(value: object) -> HermesRunUsage:
    if not isinstance(value, dict) or set(value) != _USAGE_KEYS:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    input_tokens = _required_usage_int(value, "input_tokens")
    output_tokens = _required_usage_int(value, "output_tokens")
    total_tokens = _required_usage_int(value, "total_tokens")
    if total_tokens != input_tokens + output_tokens:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return HermesRunUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens)


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and value != ""


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _required_string(value: dict[str, object], key: str) -> str:
    item = value.get(key)
    if not _is_non_empty_string(item):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return item


def _required_usage_int(value: dict[str, object], key: str) -> int:
    item = value.get(key)
    if not _is_non_negative_int(item):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return item


def _required_epoch(value: dict[str, object], key: str) -> int | float:
    item = value.get(key)
    if not isinstance(item, (int, float)) or isinstance(item, bool) or item < 0:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return item
