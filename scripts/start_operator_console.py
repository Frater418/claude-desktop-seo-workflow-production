"""Start the real local Heartweb Operator Console on Windows."""

from __future__ import annotations

import argparse
import os
import sys
import threading
import types
import webbrowser
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles


SOURCE_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
DIST = RESOURCE_ROOT / "apps" / "operator-console" / "dist"
DEFAULT_CUSTOMER_ROOT = Path.home() / "Documents" / "Projekte" / "Heartweb" / "Kunden"
DEFAULT_DIAGNOSTIC_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Heartweb" / "operator-diagnostics" / "v1"
DEFAULT_SECRET_ENV = DEFAULT_DIAGNOSTIC_ROOT.parents[1] / ".env"
LOCAL_SECRET_NAMES = frozenset({"DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"})


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


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the real local Heartweb Operator Console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--tenant-id", default="tenant-heartweb")
    parser.add_argument("--customer-root", type=Path, default=DEFAULT_CUSTOMER_ROOT)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if not DIST.is_dir() or not (DIST / "index.html").is_file():
        print("ERROR_OPERATOR_FRONTEND_BUILD_MISSING: apps/operator-console/dist fehlt.", file=sys.stderr)
        return 2
    customer_root = args.customer_root.expanduser().absolute()
    customer_root.mkdir(parents=True, exist_ok=True)
    if customer_root.is_symlink() or not customer_root.is_dir():
        print("ERROR_OPERATOR_CUSTOMER_ROOT_INVALID: Der Kundenordner ist nicht sicher nutzbar.", file=sys.stderr)
        return 3
    DEFAULT_DIAGNOSTIC_ROOT.mkdir(parents=True, exist_ok=True)
    _load_local_secrets()

    _local_mcp_namespace()
    if str(RESOURCE_ROOT) not in sys.path:
        sys.path.insert(0, str(RESOURCE_ROOT))

    from services.operator_api.app import AppConfig, create_app
    from services.operator_api.repository import WorkspaceRegistry

    app = create_app(
        registry=WorkspaceRegistry(()),
        repository_root=RESOURCE_ROOT,
        config=AppConfig(
            RESOURCE_ROOT,
            provisioning_root=customer_root,
            provisioning_enabled=True,
            execution_mode="real",
            diagnostic_root=DEFAULT_DIAGNOSTIC_ROOT,
        ),
    )
    app.mount("/", StaticFiles(directory=DIST, html=True), name="operator-console")
    url = f"http://{args.host}:{args.port}"
    print(f"HEARTWEB_OPERATOR_URL={url}", flush=True)
    print(f"HEARTWEB_CUSTOMER_ROOT={customer_root}", flush=True)
    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=args.host, port=args.port, access_log=False, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
