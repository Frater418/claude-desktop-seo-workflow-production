from __future__ import annotations

from dataclasses import dataclass
import hashlib
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import tempfile
import threading
import time
import unittest
import zipfile

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from services.delivery.archive_validation import validate_archive
from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, delivery_base, delivery_request, seed_workspace, write_projection, workspace_snapshot
from tests.support.diagnostic_trace_e2e import ClosedTraceEvidence, current_trace_id, reconstruct_closed_trace, reject_active_trace


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "apps" / "operator-console" / "dist"
DRIVER = ROOT / "apps" / "operator-console" / "src" / "test" / "deliveryE2EBrowser.mjs"
M06_EVIDENCE = ROOT / "00_admin" / "audits" / "2026-08-22-m06-delivery-e2e"
M07_EVIDENCE = ROOT / "00_admin" / "audits" / "2026-08-22-m07-diagnostic-trace"
APPROVED_DIAGNOSTIC_ROOT = ROOT / "var" / "operator-diagnostics" / "v1"
M07_DIAGNOSTIC_ROOT_ENV = "M07_DIAGNOSTIC_ROOT"
CHECKPOINT_IDS = {
    "delivery_export_request_id": "delivery-export-request-66ff1f053918e8c41f3a5f57bea8863c",
    "export_id": "delivery-export-aa3335ee5ab249b02303c7abb8074b34",
    "delivery_package_id": "delivery-package-eb5b530fdb3e45f038676536d1d22517",
    "delivery_export_result_id": "delivery-export-result-99f28508f91a282db3bcc9e000dd8150",
    "idempotency_key": "idem-8f79262566f7f176266069cc24898f5a",
    "notion_import_manifest_id": "notion-import-61d3557d1959a0bd66ef7d1ce9d53154",
    "publication_registry_record_id": "publication-registry-9940e186e04b93d5643fb0544e83a6a1",
    "copywriter_manifest_id": "role-handoff-b7e688134993e41473c213f9c8d0b17a",
    "developer_manifest_id": "role-handoff-43c4a35d025de3da8ec7c06d8081bf02",
}


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> dict[str, object]:
        return json.loads(self.body)


class LiveOperatorServer:
    def __init__(self, workspace: Path, diagnostic_root: Path) -> None:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        app = create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock(), diagnostic_root=diagnostic_root))
        app.middleware("http")(frontend_projection)
        app.mount("/", StaticFiles(directory=DIST, html=True), name="operator-console")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen()
        self.port = self._socket.getsockname()[1]
        self.server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="error"))
        self.thread = threading.Thread(target=self.server.run, kwargs={"sockets": [self._socket]}, name="m06-operator-api")

    def start(self) -> None:
        self.thread.start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                if request(self.port, "GET", "/readyz").status == 200:
                    return
            except OSError:
                pass
            threading.Event().wait(0.05)
        raise AssertionError("M06 local Operator API did not become ready.")

    def stop(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=10)
        self._socket.close()
        if self.thread.is_alive():
            raise AssertionError("M06 Uvicorn thread remained alive after shutdown.")
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                raise AssertionError("M06 ephemeral port remained reachable after shutdown.")
        except OSError:
            return


def request(port: int, method: str, target: str, body: bytes | None = None) -> HttpResponse:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    connection.request(method, target, body=body, headers=headers)
    response = connection.getresponse()
    result = HttpResponse(response.status, {key.lower(): value for key, value in response.getheaders()}, response.read())
    connection.close()
    return result


def canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def diagnostic_root() -> Path:
    override = os.environ.get(M07_DIAGNOSTIC_ROOT_ENV)
    return Path(override) if override else APPROVED_DIAGNOSTIC_ROOT


def audit_snapshot(root: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}


def baseline_delivery_hashes(snapshot: dict[str, bytes]) -> dict[str, str]:
    result = json.loads(snapshot["e2e-results.json"])
    return {"checkpoint_zip_sha256": result["checkpoint_zip_sha256"], "final_zip_sha256": result["final_zip_sha256"]}


def overlay_frontend_projection(workspace: Path) -> None:
    write_projection(workspace, "context-packages.json", [])
    write_projection(workspace, "integrations-status.json", [])


async def frontend_projection(request_message: Request, call_next: object) -> Response:
    base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
    projects = f"/v1/tenants/{TENANT}/projects"
    path = request_message.url.path
    if request_message.method == "GET" and path == f"{base}/steps":
        return JSONResponse({"data": [{"tenant_id": TENANT, "project_id": PROJECT, "run_id": f"run-step-{step}-0001", "step_id": step, "status": "completed", "blocker": "Keine offenen Schrittblocker", "next_action": "Lieferpaket pruefen"} for step in ("0", "1", "1b", "1c", "2", "3", "4a", "4b")]})
    response = await call_next(request_message)
    if request_message.method != "GET" or response.status_code != 200 or (path != projects and not path.startswith(base)) or "/delivery" in path:
        return response
    body = b"".join([chunk async for chunk in response.body_iterator])
    payload = json.loads(body)
    data = payload.get("data")
    if path in {projects, base}:
        rows = data if isinstance(data, list) else [data]
        for row in rows:
            if isinstance(row, dict):
                row.update({"customer": "Neutral Delivery Customer", "current_step": "4b", "progress": "8 von 8 Schritten", "blocker_count": 1, "owner": "Heartweb Admin Operator", "next_action": "Lieferpaket pruefen"})
    elif path == f"{base}/runs/current" and isinstance(payload, dict):
        payload["expected_revision"] = payload.get("revision", 1)
    elif path == f"{base}/tasks" and isinstance(data, list):
        payload["data"] = [{**row, "run_id": "run-step-4b-0001", "step_id": "4b", "owner": "Heartweb Admin Operator", "deadline": "2026-09-01", "resolution": "Manuelle Uebergabe", "dependency": "Freigabe"} for row in data if isinstance(row, dict)]
    elif path == f"{base}/artifacts" and isinstance(data, list):
        payload["data"] = [row for row in data if isinstance(row, dict) and row.get("run_id") == "run-step-4b-0001"]
    elif path == f"{base}/gates" and isinstance(data, list):
        payload["data"] = [{**row, "project_id": PROJECT, "summary": "Maschinenpruefung bestanden"} for row in data if isinstance(row, dict) and row.get("run_id") == "run-step-4b-0001"]
    return Response(content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), status_code=response.status_code, media_type="application/json")


def final_request() -> dict[str, object]:
    value = delivery_request(
        scope="final",
        idempotency_key="idem-delivery-00000002",
        created_at="2026-08-22T10:15:31Z",
        export_id="delivery-export-00000002",
        delivery_package_id="delivery-package-00000002",
        delivery_export_result_id="delivery-export-result-00000002",
        delivery_export_request_id="delivery-export-request-00000002",
        package_revision=8,
    )
    value["role_package_requests"] = [
        {"role": "copywriter", "role_handoff_manifest_id": "role-handoff-copywriter-00000002"},
        {"role": "developer", "role_handoff_manifest_id": "role-handoff-developer-00000002"},
    ]
    notion = value["notion_import_request"]
    assert isinstance(notion, dict)
    notion["notion_import_manifest_id"] = "notion-import-00000002"
    return value


def append_missing_developer_release(workspace: Path) -> None:
    root = workspace / "v2" / "operator"
    artifacts = json.loads((root / "artifacts.json").read_text(encoding="utf-8"))
    approvals = json.loads((root / "approvals.json").read_text(encoding="utf-8"))
    artifact = next(item for item in artifacts if item["artifact_id"] == "artifact-developer-handoff-0001")
    approval = next(item for item in approvals if item["artifact_id"] == artifact["artifact_id"])
    release = {
        "tenant_id": TENANT,
        "project_id": PROJECT,
        "release_id": "release-artifact-developer-handoff-0001",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["content_sha256"],
        "artifact_revision": artifact["revision"],
        "run_id": artifact["run_id"],
        "step_id": "4b",
        "gate_id": "GATE-4B",
        "approval_id": approval["approval_id"],
        "policy_version": "1.0.0",
        "status": "released",
        "released_at": "2026-08-22T10:15:30Z",
    }
    releases = json.loads((root / "releases.json").read_text(encoding="utf-8"))
    write_projection(workspace, "releases.json", [*releases, release])
    write_projection(workspace, f"releases/{release['release_id']}.json", release)


def assert_safe_zip(test: unittest.TestCase, archive_bytes: bytes, expected_zip_sha256: str, extraction: Path) -> dict[str, object]:
    test.assertEqual(expected_zip_sha256, hashlib.sha256(archive_bytes).hexdigest())
    validation = validate_archive(archive_bytes)
    test.assertEqual(validation.package_sha256, hashlib.sha256(json.dumps({"files": [{"path": entry.relative_path, "sha256": hashlib.sha256(entry.content).hexdigest(), "size": len(entry.content)} for entry in validation.payloads], "format_version": "1.0", "identity": {"package_root": validation.identity.package_root, "tenant_id": validation.identity.tenant_id, "project_id": validation.identity.project_id, "export_id": validation.identity.export_id, "package_id": validation.identity.package_id, "scope": validation.identity.scope, "package_revision": validation.identity.package_revision, "created_at": validation.identity.created_at}}, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest())
    (extraction / "archive.zip").write_bytes(archive_bytes)
    with zipfile.ZipFile(extraction / "archive.zip") as archive:
        test.assertIsNone(archive.testzip())
        names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names}
        test.assertEqual(1, len(roots))
        for info in archive.infolist():
            relative = info.filename.split("/", 1)[1]
            test.assertNotIn("\\", relative)
            test.assertNotIn("..", Path(relative).parts)
            test.assertFalse(relative.startswith("/"))
            test.assertFalse(Path(relative).drive)
            test.assertTrue(stat.S_ISREG(info.external_attr >> 16))
        archive.extractall(extraction / "extracted")
        root = next(iter(roots))
        manifest = json.loads(archive.read(f"{root}/export-manifest.json"))
        checksums = {path: digest for digest, path in (line.split("  ", 1) for line in archive.read(f"{root}/checksums.sha256").decode("utf-8").splitlines())}
        payloads = {entry["path"] for entry in manifest["files"]}
        test.assertEqual(payloads | {"export-manifest.json"}, set(checksums))
        for path, digest in checksums.items():
            test.assertEqual(digest, hashlib.sha256(archive.read(f"{root}/{path}")).hexdigest())
    return manifest


def assert_package_boundaries(test: unittest.TestCase, archive_bytes: bytes) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "package.zip"
        path.write_bytes(archive_bytes)
        with zipfile.ZipFile(path) as archive:
            root = archive.namelist()[0].split("/", 1)[0]
            names = {name.removeprefix(f"{root}/") for name in archive.namelist()}
            for role in ("copywriter", "developer"):
                prefix = f"{role}-handoff/"
                test.assertTrue({f"{prefix}ROLE_INDEX.md", f"{prefix}TASK_SUMMARY.md", f"{prefix}role-handoff-manifest.json"}.issubset(names))
                manifest = json.loads(archive.read(f"{root}/{prefix}role-handoff-manifest.json"))
                folders = {path.split("/", 1)[0] for path in manifest["included_paths"]}
                test.assertEqual({"keyword-research", "roadmap", "copywriter-handoff"} if role == "copywriter" else {"architecture", "design", "roadmap", "developer-handoff"}, folders)
            copywriter = archive.read(f"{root}/copywriter-handoff/ROLE_INDEX.md").decode("utf-8") + archive.read(f"{root}/copywriter-handoff/TASK_SUMMARY.md").decode("utf-8")
            test.assertIn("blocker-delivery-0001", copywriter)
            test.assertIn("open", copywriter)
            notion = json.loads(archive.read(f"{root}/notion-import/notion-import-manifest.json"))
            test.assertEqual("manual_import", notion["integration_mode"])
            test.assertTrue(all(row["read_only"] for row in notion["artifact_rows"]))
            test.assertTrue(all(row["history_only"] for row in notion["task_rows"] if row["task_class"] == "core_history"))
            implementation = next(row for row in notion["task_rows"] if row["external_id"] == "task-implementation-0001")
            test.assertEqual("notion_implementation", implementation["task_class"])
            test.assertEqual("none", implementation["core_effect"])
            assignment = next(row for row in notion["assignment_rows"] if row["external_id"] == "assignment-implementation-0001")
            test.assertEqual("unassigned", assignment["assignee"])
            test.assertIn("assignment-implementation-0001", notion["unresolved_assignee_ids"])
            test.assertIn(b"assignment-implementation-0001", archive.read(f"{root}/notion-import/USER_MAPPING_TEMPLATE.csv"))
            payload = b"\n".join(archive.read(name) for name in archive.namelist())
            for forbidden in (b"/home/", b"/workspace/", b"C:\\Users\\", b"file://", b"api_key", b"apikey", b"client_secret", b"password", b"BEGIN PRIVATE KEY", b"Bearer ", b"callback", b"resume_run", b"artifact_mutation", b"task_completion_callback"):
                test.assertNotIn(forbidden, payload)


class DeliveryE2ETests(unittest.TestCase):
    def test_neutral_delivery_route_from_checkpoint_to_final(self) -> None:
        self.assertTrue(DIST.is_dir(), "Production Operator Console dist is missing. Run the permitted production build first.")
        self.assertTrue(DRIVER.is_file(), "Focused real Delivery browser driver/evidence is absent.")
        self.assertTrue(M06_EVIDENCE.is_dir(), "Frozen M06 audit evidence is missing.")
        m06_before = audit_snapshot(M06_EVIDENCE)
        baseline_hashes = baseline_delivery_hashes(m06_before)
        selected_diagnostic_root = diagnostic_root()
        reject_active_trace(selected_diagnostic_root)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            proof_root = Path(temporary) / "m07-proof"
            browser_evidence = proof_root if M07_DIAGNOSTIC_ROOT_ENV in os.environ else M07_EVIDENCE
            checkpoint_proof = proof_root / "checkpoint.zip"
            seed_workspace(workspace, incomplete_final=True)
            overlay_frontend_projection(workspace)
            before_preview = workspace_snapshot(workspace, include_delivery=True)
            server = LiveOperatorServer(workspace, selected_diagnostic_root)
            server.start()
            try:
                base = delivery_base()
                checkpoint_preview = request(server.port, "GET", f"{base}/preview?scope=checkpoint")
                final_preview = request(server.port, "GET", f"{base}/preview?scope=final")
                self.assertEqual(200, checkpoint_preview.status, checkpoint_preview.body.decode("utf-8"))
                self.assertTrue(checkpoint_preview.json()["policy_eligible"])
                self.assertEqual(200, final_preview.status)
                self.assertFalse(final_preview.json()["policy_eligible"])
                self.assertIn("developer-handoff", final_preview.json()["missing_deliverable_ids"])
                self.assertEqual(before_preview, workspace_snapshot(workspace, include_delivery=True))
                steps_projection = request(server.port, "GET", f"/v1/tenants/{TENANT}/projects/{PROJECT}/steps").json()
                self.assertTrue(all("blocker" in row and "next_action" in row for row in steps_projection["data"]), steps_projection)

                final_body = canonical_bytes(final_request())
                premature = request(server.port, "POST", f"{base}/exports", final_body)
                self.assertEqual(409, premature.status)
                self.assertEqual("DELIVERY_FINAL_POLICY_REJECTED", premature.json()["code"])
                self.assertEqual(before_preview, workspace_snapshot(workspace, include_delivery=True))

                browser = self.run_browser(server.port, browser_evidence, checkpoint_proof)
                self.assertEqual(browser["checkpoint_request_body"], browser["retry_request_body"])
                checkpoint_request = json.loads(browser["checkpoint_request_body"])
                self.assertEqual(CHECKPOINT_IDS["export_id"], checkpoint_request["export_id"])
                self.assertEqual(CHECKPOINT_IDS["idempotency_key"], checkpoint_request["export_request"]["idempotency_key"])
                self.assertEqual(CHECKPOINT_IDS["copywriter_manifest_id"], checkpoint_request["role_package_requests"][0]["role_handoff_manifest_id"])
                self.assertEqual(CHECKPOINT_IDS["developer_manifest_id"], checkpoint_request["role_package_requests"][1]["role_handoff_manifest_id"])

                trace = reconstruct_closed_trace(selected_diagnostic_root, current_trace_id(selected_diagnostic_root), "00_admin/audits/2026-08-22-m07-diagnostic-trace/delivery-center-1280x900.png")
                self.assertEqual(trace.trace_id, browser["diagnostic_trace_id"])
                self.assertEqual(trace.close_id, browser["diagnostic_close_id"])
                self.assertEqual(trace.closed_at, browser["diagnostic_closed_at"])
                self.assertEqual("closed", browser["diagnostic_status"])
                self.assert_trace_closed_immutability(server.port, trace)

                history = request(server.port, "GET", f"{base}/exports").json()["data"]
                self.assertEqual([CHECKPOINT_IDS["export_id"]], [entry["export_id"] for entry in history])
                checkpoint_record = request(server.port, "GET", f"{base}/exports/{CHECKPOINT_IDS['export_id']}").json()
                checkpoint_download = request(server.port, "GET", f"{base}/exports/{CHECKPOINT_IDS['export_id']}/download")
                self.assertEqual(checkpoint_record["zip_sha256"], checkpoint_download.headers["etag"].strip('"'))
                self.assertEqual(checkpoint_download.body, (workspace / "v2" / "operator" / "delivery" / "exports" / CHECKPOINT_IDS["export_id"] / "archive.zip").read_bytes())
                self.assertEqual(checkpoint_download.body, checkpoint_proof.read_bytes())
                with tempfile.TemporaryDirectory() as extraction:
                    assert_safe_zip(self, checkpoint_download.body, checkpoint_record["zip_sha256"], Path(extraction))

                before_release = workspace_snapshot(workspace, include_delivery=True)
                append_missing_developer_release(workspace)
                after_release = workspace_snapshot(workspace, include_delivery=True)
                changed = {path for path in set(before_release) | set(after_release) if before_release.get(path) != after_release.get(path)}
                self.assertEqual({"v2/operator/releases.json", "v2/operator/releases/release-artifact-developer-handoff-0001.json"}, changed)
                self.assertTrue(request(server.port, "GET", f"{base}/preview?scope=final").json()["policy_eligible"])

                created = request(server.port, "POST", f"{base}/exports", final_body)
                self.assertEqual(201, created.status)
                final_result = created.json()
                self.assertEqual("created", final_result["replay_state"])
                self.assertEqual("2026-08-22T10:15:31Z", final_result["created_at"])
                final_record = request(server.port, "GET", f"{base}/exports/{final_result['export_id']}").json()
                self.assertEqual("final", final_record["scope"])
                self.assertEqual(7, len(final_record["required_deliverables"]))
                self.assertTrue(all(item["release_status"] == "released" for item in final_record["required_deliverables"]))
                self.assertTrue(all(final_record[field] for field in ("task_assignment_manifest_path", "quality_summary", "export_manifest_path", "checksums_path")))
                final_download = request(server.port, "GET", f"{base}/exports/{final_result['export_id']}/download")
                with tempfile.TemporaryDirectory() as extraction:
                    assert_safe_zip(self, final_download.body, final_result["zip_sha256"], Path(extraction))
                assert_package_boundaries(self, final_download.body)

                persisted = workspace_snapshot(workspace, include_delivery=True)
                replayed = request(server.port, "POST", f"{base}/exports", final_body)
                self.assertEqual(200, replayed.status)
                expected_replay = dict(final_result, replay_state="replayed")
                self.assertEqual(expected_replay, replayed.json())
                self.assertEqual(persisted, workspace_snapshot(workspace, include_delivery=True))
                self.assertEqual(2, len(request(server.port, "GET", f"{base}/exports").json()["data"]))
                self.assertEqual(baseline_hashes, {"checkpoint_zip_sha256": checkpoint_record["zip_sha256"], "final_zip_sha256": final_result["zip_sha256"]})
                self.write_m07_evidence(browser, trace, checkpoint_record, final_result)
                self.assertEqual(m06_before, audit_snapshot(M06_EVIDENCE))
            finally:
                server.stop()

    def run_browser(self, port: int, evidence: Path, checkpoint_download: Path) -> dict[str, object]:
        environment = os.environ | {"M06_BASE_URL": f"http://127.0.0.1:{port}", "M07_EVIDENCE_DIR": str(evidence), "M06_CHECKPOINT_DOWNLOAD": str(checkpoint_download), "M07_SCREENSHOT_REFERENCE": "00_admin/audits/2026-08-22-m07-diagnostic-trace/delivery-center-1280x900.png"}
        process = subprocess.Popen(["node", str(DRIVER)], cwd=ROOT, env=environment, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            raise AssertionError(f"M06 browser driver timed out: {stderr or stdout}") from None
        self.assertEqual(0, process.returncode, stderr or stdout)
        return json.loads(stdout)

    def assert_trace_closed_immutability(self, port: int, trace: ClosedTraceEvidence) -> None:
        base = f"/v1/tenants/{TENANT}/projects/{PROJECT}/diagnostic-traces/{trace.trace_id}"
        rejected = request(port, "POST", f"{base}/entries", canonical_bytes({"operation_id": "operation-0005-after-close", "occurred_at": "2026-08-22T10:15:30Z", "action": "browser_observation", "route": f"/v1/tenants/{TENANT}/projects/{PROJECT}/delivery/exports", "api_method": "POST", "api_status": 200, "error_code": None, "remediation": None, "expected_actions": ["create_delivery_export", "download_delivery_export"], "rendered_actions": ["create_delivery_export", "download_delivery_export"], "disabled_actions": [], "evidence_references": []}))
        self.assertEqual(409, rejected.status)
        self.assertEqual("ERROR_DIAGNOSTIC_TRACE_CLOSED", rejected.json()["code"])
        replayed = request(port, "POST", f"{base}/close", canonical_bytes({"close_id": trace.close_id, "closed_at": trace.closed_at}))
        self.assertEqual(200, replayed.status)
        self.assertTrue(replayed.json()["replay"])
        self.assertEqual(trace.run_bytes, (diagnostic_root() / trace.relative_run_path).read_bytes())
        self.assertEqual(trace.run_sha256, hashlib.sha256((diagnostic_root() / trace.relative_run_path).read_bytes()).hexdigest())

    def write_m07_evidence(self, browser: dict[str, object], trace: ClosedTraceEvidence, checkpoint: dict[str, object], final: dict[str, object]) -> None:
        M07_EVIDENCE.mkdir(parents=True, exist_ok=True)
        results = {"trace_id": trace.trace_id, "relative_run_path": trace.relative_run_path, "run_sha256": trace.run_sha256, "last_successful_operation_id": trace.last_successful_operation_id, "first_failing_operation_id": None, "delivery_hashes": {"checkpoint_zip_sha256": checkpoint["zip_sha256"], "final_zip_sha256": final["zip_sha256"]}, "browser": {"diagnostic_trace_id": browser["diagnostic_trace_id"], "diagnostic_close_id": browser["diagnostic_close_id"], "diagnostic_closed_at": browser["diagnostic_closed_at"], "diagnostic_status": browser["diagnostic_status"], "screenshot": "delivery-center-1280x900.png"}}
        (M07_EVIDENCE / "e2e-results.json").write_text(f"{json.dumps(results, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
        report = f"""Change ID: M07-DIAGNOSTIC-TRACE-001

Observed failure:
The M06 browser cell started a diagnostic trace but did not configure the automated M06 scenario, append normalized browser evidence, or close and reconstruct the trace.

Changed files and symbols:
tests/test_delivery_e2e.py
apps/operator-console/src/test/deliveryE2EBrowser.mjs
tests/support/diagnostic_trace_e2e.py

Affected route, flow and gate:
Uebergabe und Export
POST diagnostic-traces
POST diagnostic-traces/{{trace_id}}/entries
POST diagnostic-traces/{{trace_id}}/close
PT-09 and the existing 1280x900 M06 Delivery Center cell

Focused red test:
python -m unittest tests.test_delivery_e2e.DeliveryE2ETests.test_neutral_delivery_route_from_checkpoint_to_final

Direct closure tests selected:
One isolated red execution with M07_DIAGNOSTIC_ROOT
One approved-root green execution of the exact M06 E2E cell

Why each test is in scope:
The browser driver proves the real Console creates, records, observes, and closes the automated Delivery trace.
The Python reconstruction proves immutable JSONL, current pointer, index, closed-only semantics, and close replay without mutation.

Unrelated tests deliberately retained from baseline:
All other browser cells, M05 viewport matrix, full suite, live integrations, deployment, and unrelated routes.

Result:
Focused M07 trace {trace.trace_id} closed at {trace.closed_at}. Immutable run SHA-256 {trace.run_sha256}. Checkpoint ZIP SHA-256 {checkpoint["zip_sha256"]}. Final ZIP SHA-256 {final["zip_sha256"]}.

Remaining blocker:
None.

Next product task:
None.

Evidence classification:
Previous baseline evidence: M06 frozen Delivery audit
New focused evidence: M07 closed automated diagnostic trace for the existing M06 cell
Not assessed: other browser cells, live integrations, deployment, and other routes
"""
        (M07_EVIDENCE / "SECTION_11_REPORT.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
