"""Start the real local Heartweb Operator Console on Windows."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time
import types
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import uvicorn
from fastapi.staticfiles import StaticFiles


SOURCE_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
DIST = RESOURCE_ROOT / "apps" / "operator-console" / "dist"
DEFAULT_CUSTOMER_ROOT = Path.home() / "Documents" / "Projekte" / "Heartweb" / "Kunden"
DEFAULT_DIAGNOSTIC_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Heartweb" / "operator-diagnostics" / "v1"
DEFAULT_SECRET_ENV = DEFAULT_DIAGNOSTIC_ROOT.parents[1] / ".env"
LOCAL_SECRET_NAMES = frozenset({"DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"})
HERMES_PROFILE = "heartweb-runtime"
HERMES_PROFILE_ENV = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "hermes" / "profiles" / HERMES_PROFILE / ".env"
HERMES_PROFILE_CONFIG = HERMES_PROFILE_ENV.with_name("config.yaml")
HERMES_RUNTIME_LOG = DEFAULT_DIAGNOSTIC_ROOT.parents[1] / "heartweb-runtime.log"
EXPECTED_HERMES_MODEL = "gpt-5.6-sol"
OPERATOR_SERVICE_ID = "heartweb-operator-console"
OPERATOR_HTML_MARKER = "<title>Heartweb Admin Operator Konsole</title>"
OPERATOR_PID_RECORD = DEFAULT_DIAGNOSTIC_ROOT.parents[1] / "operator-console.pid.json"
_ERROR_ALREADY_EXISTS = 183
_WAIT_OBJECT_0 = 0
_WAIT_ABANDONED = 0x00000080


@dataclass(frozen=True, slots=True)
class HermesRuntimeSettings:
    base_url: str
    api_key: str


@dataclass(slots=True)
class HermesRuntimeHandle:
    process: subprocess.Popen[bytes] | None

    def close(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


@dataclass(slots=True)
class OperatorInstanceMutex:
    handle: int | None
    owned: bool

    def wait_for_ownership(self, timeout_seconds: float) -> bool:
        if self.handle is None:
            self.owned = True
            return True
        if self.owned:
            return True
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        result = kernel32.WaitForSingleObject(ctypes.c_void_p(self.handle), max(0, int(timeout_seconds * 1000)))
        self.owned = result in {_WAIT_OBJECT_0, _WAIT_ABANDONED}
        return self.owned

    def close(self) -> None:
        if self.handle is None:
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if self.owned:
            kernel32.ReleaseMutex(ctypes.c_void_p(self.handle))
            self.owned = False
        kernel32.CloseHandle(ctypes.c_void_p(self.handle))
        self.handle = None


class HermesRuntimeStartupError(RuntimeError):
    pass


class OperatorInstanceError(RuntimeError):
    pass


def _load_local_secrets(path: Path = DEFAULT_SECRET_ENV) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name in LOCAL_SECRET_NAMES and value and name not in os.environ:
            os.environ[name] = value


def _local_mcp_namespace() -> None:
    """Ensure repository MCP modules win over an installed package of the same name."""
    package = types.ModuleType("mcp")
    package.__path__ = [str(RESOURCE_ROOT / "mcp")]
    sys.modules["mcp"] = package


def _hermes_runtime_settings(path: Path = HERMES_PROFILE_ENV) -> HermesRuntimeSettings:
    values = _env_values(path)
    host = values.get("API_SERVER_HOST", "127.0.0.1")
    port_value = values.get("API_SERVER_PORT", "8642")
    api_key = values.get("API_SERVER_KEY", "")
    if values.get("API_SERVER_ENABLED", "").lower() != "true" or host not in {"127.0.0.1", "localhost"} or not api_key:
        raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_CONFIG_INVALID: Das isolierte Heartweb-Hermes-Profil ist nicht sicher konfiguriert.")
    try:
        port = int(port_value)
    except ValueError as error:
        raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_CONFIG_INVALID: Der lokale Hermes-Port ist ungueltig.") from error
    if not 1 <= port <= 65535:
        raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_CONFIG_INVALID: Der lokale Hermes-Port ist ungueltig.")
    return HermesRuntimeSettings(base_url=f"http://{host}:{port}", api_key=api_key)


def _tool_search_disabled(path: Path = HERMES_PROFILE_CONFIG) -> bool:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return False
    tools_indent: int | None = None
    search_indent: int | None = None
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        leading = raw_line[: len(raw_line) - len(raw_line.lstrip())]
        if "\t" in leading:
            return False
        indent = len(leading)
        stripped = raw_line.strip()
        if tools_indent is None:
            if indent == 0 and stripped == "tools:":
                tools_indent = indent
            continue
        if indent <= tools_indent:
            break
        if search_indent is None:
            if stripped == "tool_search:":
                search_indent = indent
            continue
        if indent <= search_indent:
            break
        if stripped.startswith("enabled:"):
            value = stripped.split(":", 1)[1].split("#", 1)[0].strip().strip("'\"")
            return value.lower() == "off"
    return False


def _env_values(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_CONFIG_MISSING: Das isolierte Heartweb-Hermes-Profil fehlt.")
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as error:
        raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_CONFIG_MISSING: Das isolierte Heartweb-Hermes-Profil ist nicht lesbar.") from error
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip()
    return values


def _ensure_hermes_runtime(settings: HermesRuntimeSettings) -> HermesRuntimeHandle:
    if not _tool_search_disabled():
        raise HermesRuntimeStartupError(
            "ERROR_OPERATOR_AI_RUNTIME_CONFIG_INVALID: Das isolierte Heartweb-Hermes-Profil muss tools.tool_search.enabled=off setzen."
        )
    if _health_ready(settings.base_url):
        if not _capabilities_ready(settings):
            raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_AUTH: Die laufende Heartweb-KI-Laufzeit hat nicht die erwartete Authentifizierung oder Runs-Faehigkeit.")
        return HermesRuntimeHandle(None)
    executable = shutil.which("hermes")
    if executable is None:
        raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_MISSING: Die lokale Hermes-CLI wurde nicht gefunden.")
    HERMES_RUNTIME_LOG.parent.mkdir(parents=True, exist_ok=True)
    with HERMES_RUNTIME_LOG.open("ab") as log:
        process = subprocess.Popen(
            [executable, "-p", HERMES_PROFILE, "gateway", "run", "--quiet", "--external-supervisor"],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        if _health_ready(settings.base_url):
            if _capabilities_ready(settings):
                return HermesRuntimeHandle(process)
            _stop_process(process)
            raise HermesRuntimeStartupError("ERROR_OPERATOR_AI_RUNTIME_AUTH: Die isolierte Heartweb-KI-Laufzeit ist nicht korrekt authentifiziert.")
        if process.poll() is not None:
            raise HermesRuntimeStartupError(f"ERROR_OPERATOR_AI_RUNTIME_START_FAILED: Die isolierte Heartweb-KI-Laufzeit konnte nicht starten. Diagnose: {HERMES_RUNTIME_LOG}")
        time.sleep(0.25)
    _stop_process(process)
    raise HermesRuntimeStartupError(f"ERROR_OPERATOR_AI_RUNTIME_TIMEOUT: Die isolierte Heartweb-KI-Laufzeit wurde nicht rechtzeitig bereit. Diagnose: {HERMES_RUNTIME_LOG}")


def _health_ready(base_url: str) -> bool:
    document = _get_json(f"{base_url}/health", None)
    return isinstance(document, dict) and document.get("status") in {"ok", "ready"}


def _capabilities_ready(settings: HermesRuntimeSettings) -> bool:
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    capabilities = _get_json(f"{settings.base_url}/v1/capabilities", headers)
    models = _get_json(f"{settings.base_url}/v1/models", headers)
    features = capabilities.get("features") if isinstance(capabilities, dict) else None
    model_rows = models.get("data") if isinstance(models, dict) else None
    return (
        isinstance(features, dict)
        and features.get("run_submission") is True
        and features.get("run_status") is True
        and isinstance(model_rows, list)
        and any(isinstance(row, dict) and row.get("id") == EXPECTED_HERMES_MODEL for row in model_rows)
    )


def _get_json(url: str, headers: dict[str, str] | None) -> dict[str, object] | None:
    try:
        with urlopen(Request(url, headers=headers or {}), timeout=2.0) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _acquire_operator_mutex(host: str, port: int) -> OperatorInstanceMutex:
    if os.name != "nt":
        return OperatorInstanceMutex(None, True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
    create_mutex.restype = ctypes.c_void_p
    handle = create_mutex(None, 1, f"Local\\HeartwebOperatorConsole-{host}-{port}")
    if not handle:
        raise OperatorInstanceError("ERROR_OPERATOR_INSTANCE_LOCK: Die lokale Single-Instance-Sperre konnte nicht erstellt werden.")
    return OperatorInstanceMutex(int(handle), ctypes.get_last_error() != _ERROR_ALREADY_EXISTS)


def _operator_ready_document(base_url: str) -> dict[str, object] | None:
    document = _get_json(f"{base_url}/readyz", None)
    data = document.get("data") if isinstance(document, dict) else None
    if not isinstance(data, dict) or data.get("status") != "ready" or not _operator_html_matches(base_url):
        return None
    return document


def _operator_html_matches(base_url: str) -> bool:
    try:
        with urlopen(Request(f"{base_url}/"), timeout=2.0) as response:
            value = response.read(65536).decode("utf-8")
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError):
        return False
    return OPERATOR_HTML_MARKER in value


def _port_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _wait_for_operator(base_url: str, timeout_seconds: float) -> dict[str, object] | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        document = _operator_ready_document(base_url)
        if document is not None:
            return document
        time.sleep(0.25)
    return None


def _runtime_fingerprint() -> str:
    digest = hashlib.sha256()
    roots = (RESOURCE_ROOT / "services" / "operator_api", DIST)
    files = [Path(__file__).resolve()]
    for root in roots:
        if root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())
    for path in sorted(files, key=lambda item: item.as_posix().lower()):
        try:
            relative = path.relative_to(RESOURCE_ROOT).as_posix()
            content = path.read_bytes()
        except (OSError, ValueError) as error:
            raise OperatorInstanceError("ERROR_OPERATOR_RUNTIME_FINGERPRINT: Der lokale Heartweb-Laufzeitstand ist nicht lesbar.") from error
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _write_operator_pid_record(host: str, port: int, fingerprint: str) -> None:
    OPERATOR_PID_RECORD.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "service": OPERATOR_SERVICE_ID,
        "process_id": os.getpid(),
        "host": host,
        "port": port,
        "runtime_fingerprint": fingerprint,
    }
    temporary = OPERATOR_PID_RECORD.with_name(f".{OPERATOR_PID_RECORD.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        os.replace(temporary, OPERATOR_PID_RECORD)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise OperatorInstanceError("ERROR_OPERATOR_PID_RECORD: Die lokale Heartweb-Prozessbindung konnte nicht gespeichert werden.") from error


def _read_operator_pid_record() -> dict[str, object] | None:
    try:
        value = json.loads(OPERATOR_PID_RECORD.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _remove_operator_pid_record(process_id: int) -> None:
    record = _read_operator_pid_record()
    if isinstance(record, dict) and record.get("process_id") == process_id:
        OPERATOR_PID_RECORD.unlink(missing_ok=True)


def _restart_existing_operator(document: dict[str, object], host: str, port: int) -> None:
    data = document.get("data")
    record = _read_operator_pid_record()
    if not isinstance(data, dict) or not isinstance(record, dict):
        raise OperatorInstanceError("ERROR_OPERATOR_RESTART_UNVERIFIED: Die laufende alte Heartweb-Instanz besitzt noch keine sichere Neustartbindung.")
    process_id = data.get("process_id")
    fingerprint = data.get("runtime_fingerprint")
    verified = (
        data.get("service") == OPERATOR_SERVICE_ID
        and record.get("service") == OPERATOR_SERVICE_ID
        and isinstance(process_id, int)
        and not isinstance(process_id, bool)
        and process_id > 0
        and record.get("process_id") == process_id
        and record.get("host") == host
        and record.get("port") == port
        and isinstance(fingerprint, str)
        and record.get("runtime_fingerprint") == fingerprint
    )
    if not verified:
        raise OperatorInstanceError("ERROR_OPERATOR_RESTART_UNVERIFIED: Die laufende Instanz konnte nicht eindeutig als verwaltete Heartweb-Instanz bestaetigt werden.")
    try:
        os.kill(process_id, signal.SIGTERM)
    except OSError as error:
        raise OperatorInstanceError("ERROR_OPERATOR_RESTART_FAILED: Die verifizierte Heartweb-Instanz konnte nicht beendet werden.") from error
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        if not _port_in_use(host, port):
            return
        time.sleep(0.25)
    raise OperatorInstanceError("ERROR_OPERATOR_RESTART_TIMEOUT: Die verifizierte Heartweb-Instanz hat den Port nicht rechtzeitig freigegeben.")


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the real local Heartweb Operator Console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--tenant-id", default="tenant-heartweb")
    parser.add_argument("--customer-root", type=Path, default=DEFAULT_CUSTOMER_ROOT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--restart", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    url = f"http://{args.host}:{args.port}"
    customer_root = args.customer_root.expanduser().absolute()
    try:
        instance_mutex = _acquire_operator_mutex(args.host, args.port)
    except OperatorInstanceError as error:
        print(str(error), file=sys.stderr)
        return 5

    try:
        existing = _operator_ready_document(url)
        if existing is None and not instance_mutex.owned:
            existing = _wait_for_operator(url, 30.0)
            if existing is None and not instance_mutex.wait_for_ownership(0.0):
                print("ERROR_OPERATOR_INSTANCE_STARTING: Eine andere Heartweb-Instanz startet, wurde aber nicht rechtzeitig bereit.", file=sys.stderr)
                return 5
        if existing is not None:
            if not args.restart:
                print(f"HEARTWEB_OPERATOR_URL={url}", flush=True)
                print(f"HEARTWEB_CUSTOMER_ROOT={customer_root}", flush=True)
                print("INFO_OPERATOR_ALREADY_RUNNING: Die vorhandene Heartweb Operator Console wird geoeffnet.", flush=True)
                if not args.no_browser:
                    webbrowser.open(url)
                return 0
            try:
                _restart_existing_operator(existing, args.host, args.port)
            except OperatorInstanceError as error:
                print(str(error), file=sys.stderr)
                print("Die alte Instanz bitte einmal manuell schliessen. Danach kann Heartweb die sicheren Neustartdaten selbst verwalten.", file=sys.stderr)
                return 5
            if not instance_mutex.wait_for_ownership(15.0):
                print("ERROR_OPERATOR_INSTANCE_LOCK: Die Neustart-Sperre wurde nicht rechtzeitig freigegeben.", file=sys.stderr)
                return 5
            print("INFO_OPERATOR_RESTART: Die verifizierte Heartweb-Instanz wurde beendet und wird neu gestartet.", flush=True)
        elif _port_in_use(args.host, args.port):
            print(
                f"ERROR_OPERATOR_PORT_IN_USE: {args.host}:{args.port} wird von einem Prozess belegt, der nicht eindeutig als Heartweb Operator Console erkannt wurde.",
                file=sys.stderr,
            )
            return 5

        if not DIST.is_dir() or not (DIST / "index.html").is_file():
            print("ERROR_OPERATOR_FRONTEND_BUILD_MISSING: apps/operator-console/dist fehlt.", file=sys.stderr)
            return 2
        customer_root.mkdir(parents=True, exist_ok=True)
        if customer_root.is_symlink() or not customer_root.is_dir():
            print("ERROR_OPERATOR_CUSTOMER_ROOT_INVALID: Der Kundenordner ist nicht sicher nutzbar.", file=sys.stderr)
            return 3
        DEFAULT_DIAGNOSTIC_ROOT.mkdir(parents=True, exist_ok=True)
        _load_local_secrets()

        try:
            hermes_settings = _hermes_runtime_settings()
            hermes_runtime = _ensure_hermes_runtime(hermes_settings)
        except HermesRuntimeStartupError as error:
            print(str(error), file=sys.stderr)
            return 4

        try:
            _local_mcp_namespace()
            if str(RESOURCE_ROOT) not in sys.path:
                sys.path.insert(0, str(RESOURCE_ROOT))

            from services.operator_api.app import AppConfig, create_app
            from services.operator_api.hermes_runtime_provider import HermesRuntimeProvider
            from services.operator_api.hermes_runs_client import HermesRunsClient, HermesRunsConfig
            from services.operator_api.intake_project_generator import HermesIntakeProjectGenerator
            from services.operator_api.repository import WorkspaceRegistry

            hermes_client = HermesRunsClient(
                HermesRunsConfig(
                    base_url=hermes_settings.base_url,
                    api_key=hermes_settings.api_key,
                    timeout_seconds=300.0,
                    poll_interval_seconds=0.5,
                )
            )
            intake_generator = HermesIntakeProjectGenerator(
                client=hermes_client,
                repository_root=RESOURCE_ROOT,
            )
            app = create_app(
                registry=WorkspaceRegistry(()),
                repository_root=RESOURCE_ROOT,
                config=AppConfig(
                    RESOURCE_ROOT,
                    provisioning_root=customer_root,
                    provisioning_enabled=True,
                    execution_mode="real",
                    diagnostic_root=DEFAULT_DIAGNOSTIC_ROOT,
                    intake_project_generator=intake_generator,
                    hermes_runtime_provider=HermesRuntimeProvider(
                        hermes_client,
                        customer_root=customer_root,
                    ),
                ),
            )
            fingerprint = _runtime_fingerprint()
            app.state.operator_service = OPERATOR_SERVICE_ID
            app.state.operator_runtime_fingerprint = fingerprint
            app.state.operator_process_id = os.getpid()
            app.mount("/", StaticFiles(directory=DIST, html=True), name="operator-console")
            _write_operator_pid_record(args.host, args.port, fingerprint)
            print(f"HEARTWEB_OPERATOR_URL={url}", flush=True)
            print(f"HEARTWEB_CUSTOMER_ROOT={customer_root}", flush=True)
            if not args.no_browser:
                threading.Timer(1.0, lambda: webbrowser.open(url)).start()
            try:
                uvicorn.run(app, host=args.host, port=args.port, access_log=False, log_level="warning")
            finally:
                _remove_operator_pid_record(os.getpid())
        finally:
            hermes_runtime.close()
    finally:
        instance_mutex.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
