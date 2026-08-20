# Stage B Operator API Terminal Approval Audit

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Independent, local, read-only approval audit of the current Stage B final state after the registry-wide recovery-readiness fix. Report 47 supplied the prior P1 context. Reports 43 and 44 were checked only for their stated Stage B fixes. No Stage C, provider, network, deployment, source, test, or prior-report change was performed. Temporary ASGI workspaces were removed automatically.

## Current-State Checks

- `WorkspaceRegistry.registrations` exposes the immutable full registration tuple at `services/operator_api/repository.py:69-71`. `ProjectRepository.has_any_operator_recoveries` calls `has_operator_recoveries` for every registration at `services/operator_api/repository.py:202-206`.
- Startup derives readiness from that registry-wide check at `services/operator_api/app.py:66-69`; `/readyz` remains unavailable while `projection_rebuild_needed` is true at `services/operator_api/app.py:94-98`.
- The only `_repair_operator_record` call sites are the existing-recovery replay path at `services/operator_api/app.py:299-306` and the post-append finalization path at `services/operator_api/app.py:309-315`. Both reach the same repair function, which recomputes the flag from all registered workspaces after successful finalization at `services/operator_api/app.py:349-358`.
- The report 43 record-identity fix remains intact: the allowlisted record-type identity mapping is fixed at `services/operator_api/repository.py:20-27`, and `operator_record_id` validates the selected canonical field at `services/operator_api/repository.py:142-150`. Its reordered, same-tenant two-record regression is `tests/test_operator_api.py:160-173`.
- The report 43 nested-transition identity fix remains intact: all shared fields are bound before delegation at `services/operator_api/app.py:318-330`; the mismatch matrix verifies no event or run mutation at `tests/test_operator_api.py:141-158`.
- The report 44 durable-recovery fix remains intact: a recovery sidecar is written before append and finalized through the shared repair path at `services/operator_api/app.py:299-315`; replay recovery without a second event is covered at `tests/test_operator_api.py:175-198`.

## Findings

### P0

None observed.

### P1

None observed. The report 47 P1 condition no longer reproduces: a pending recovery in one registered workspace keeps `/readyz` at `503` after a successful command in another workspace.

### P2

None observed.

### P3

None observed.

## Local Command Evidence

1. Command:

   ```text
   PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api.OperatorApiTests.test_other_workspace_success_cannot_hide_pending_recovery -v
   ```

   Outcome: exit 0. `Ran 1 test in 0.634s`, `OK`.

2. Command:

   ```text
   PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store -v
   ```

   Outcome: exit 0. `Ran 12 tests in 8.508s`, `OK`. This includes the two-workspace readiness regression, recovery replay, canonical record identity, nested transition identity matrix, append/replay conflict, invalid-event, partial-tail, and duplicate-event EventStore cases. The installed Starlette HTTPX deprecation warning was emitted and did not affect the result.

3. Command: the exact local public-ASGI probe below, executed with `fastapi.testclient.TestClient` against two fresh `TemporaryDirectory` workspaces.

   ```text
   PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
   import tempfile
   from pathlib import Path
   from unittest.mock import patch

   from fastapi.testclient import TestClient
   from services.operator_api.app import create_app
   from services.operator_api.repository import ProjectRepository, RepositoryError, WorkspaceRegistration, WorkspaceRegistry
   from tests.test_operator_api import PROJECT, ROOT, TENANT, OperatorApiTests, operator_record, record_command

   with tempfile.TemporaryDirectory() as first_temporary, tempfile.TemporaryDirectory() as second_temporary:
       first_workspace = Path(first_temporary)
       second_workspace = Path(second_temporary)
       harness = OperatorApiTests()
       harness.seed(first_workspace)
       harness.seed(second_workspace)
       second_tenant = "tenant-other"
       second_project = "project-other"
       registry = WorkspaceRegistry((
           WorkspaceRegistration(TENANT, PROJECT, first_workspace),
           WorkspaceRegistration(second_tenant, second_project, second_workspace),
       ))
       client = TestClient(create_app(registry=registry, repository_root=ROOT))
       first_route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/request-input"
       first_payload = record_command("request-input", operator_record("task-00000001"), "audit-first")
       with patch.object(ProjectRepository, "finalize_operator_recovery", side_effect=RepositoryError("ERR_TENANT_ISOLATION", "Projection unavailable.")):
           first_status = client.post(first_route, json=first_payload).status_code
       pending_ready = client.get("/readyz").status_code
       second_record = operator_record("task-00000002")
       second_record.update(tenant_id=second_tenant, project_id=second_project)
       second_payload = record_command("request-input", second_record, "audit-second")
       second_payload.update(tenant_id=second_tenant, project_id=second_project)
       second_payload["event"]["identity"].update(tenant_id=second_tenant, project_id=second_project)
       second_route = f"/v1/tenants/{second_tenant}/projects/{second_project}/commands/request-input"
       second_status = client.post(second_route, json=second_payload).status_code
       final_ready = client.get("/readyz").status_code
       sidecar = first_workspace / "v2/operator/projection-recovery/operator-task--task-00000001.json"
       print(f"MULTI_WORKSPACE_READINESS first={first_status} pending_ready={pending_ready} other_success={second_status} after_other_ready={final_ready} pending_sidecar={sidecar.exists()}")
   PY
   ```

   Outcome: `MULTI_WORKSPACE_READINESS first=503 pending_ready=503 other_success=200 after_other_ready=503 pending_sidecar=True`. This is the requested observable result: a successful command in the second workspace does not conceal the first workspace's pending recovery.

## Unexecuted Or Blocked Checks

Blocked: Native Windows reparse-point execution was unavailable on this Linux host and was not required for this registry-wide local ASGI approval check. An initial manual-probe draft passed the `tests` directory rather than repository root to `create_app` and exited before application construction with a missing workflow-graph file; the corrected exact probe above executed successfully. No product behavior was observed from that draft.

APPROVED
