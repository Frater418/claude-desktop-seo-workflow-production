# Live Fixture Readback

The temporary server mounted the production `apps/operator-console/dist` and the real `services.operator_api.app.create_app` at `http://127.0.0.1:43179`.

## Successful Reads

- `GET /readyz` returned `{"data":{"status":"ready"}}`.
- `GET /v1/tenants/tenant-visual-qa/projects` returned two canonical projects: `project-alpha` and `project-beta`.
- `GET /v1/tenants/tenant-visual-qa/projects/project-alpha/runs/current` returned `run-qa-project-alpha-0001`, step `0`, revision `1`.
- `GET /v1/tenants/tenant-visual-qa/projects/project-beta/runs/current` returned `run-qa-project-beta-0001`, step `0`, revision `1`.
- `GET /v1/tenants/tenant-visual-qa/projects/project-alpha/artifacts` returned draft revision `1` and current revision `2`.
- `GET /v1/tenants/tenant-visual-qa/projects/project-beta/releases` returned released `release-qa-0001` for the current revision.
- `GET /` returned the production document with title `Heartweb Admin Operator Konsole` and a hashed JavaScript asset.

The fixture and server wrapper were created only under `/tmp/opencode` and were removed after teardown.
