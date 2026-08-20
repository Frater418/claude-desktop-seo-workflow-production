# Sprint 4 Local FastAPI Architecture Research

## Scope and Evidence Status

This is a read-only architecture recommendation for Sprint 4. It distinguishes current repository contracts from required implementation work. Statements prefixed **Design decision** are not implemented contracts and require implementation review before they become binding.

The canonical plan calls Sprint 4 the Local Workflow API and integration-simulator sprint, names the intended API and event-store files, and lists the read-only resource families and command verbs. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:585-623`] The active decision requires an independently executable local core, with n8n as transport and orchestration and Notion as an operational projection, while protecting status, hash, revision, and gate decisions in the local core or Transition Service. [`00_admin/DECISIONS.md:81-93`] Project state confirms that Sprint 3 is released, Sprint 4 is in progress, the local API does not yet exist, and live Notion and n8n remain unconfigured. [`00_admin/PROJECT_STATE.md:7`, `00_admin/PROJECT_STATE.md:96-117`; `00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md:40`]

## Implemented Contract Baseline

### Workflow and transitions

- The initial route is exactly `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`; every listed step requires an artifact and quality gate, and every initial edge requires a released predecessor, artifact, and gate record. [`standards/workflow/workflow-graph.json:5-23`]
- Step `3b` is a repeatable post-publication sideflow, triggered at days 30, 60, and 90 after publication. It is not an initial route edge. [`standards/workflow/workflow-graph.json:25-27`; `tests/contracts/test_workflow_graph.py:35-49`]
- The transition command is a closed Draft 2020-12 schema. It requires command, tenant, project, run, revision, idempotency, operation, step, input-hash, and timestamp fields; selected operations require output hashes, artifacts, approvals, or supersession references. [`standards/runtime/transition-command.schema.json:2-18`]
- `process_transition` is the current central rule engine. It checks idempotency fingerprinting, full tenant/project/run identity, revision and input hash, permitted state operation, current-step targeting, released predecessor, artifact identity and hash, retry exhaustion, machine gates, approval validity, human gates, and returns a copied next run only after all checks pass. [`services/transition_service/service.py:181-346`]
- The service distinguishes a matching idempotent replay from a reused key with a changed payload and exposes `ERR_IDEMPOTENCY_CONFLICT`. [`services/transition_service/service.py:203-217`; `tests/test_transition_service.py:217-225`]
- The existing durable ledger is a JSON fingerprint map guarded by create-only `.lock` file handling and written atomically with `os.replace`; lock contention is fail-fast. [`services/transition_service/service.py:53-65`, `services/transition_service/service.py:349-395`; `tests/test_transition_service.py:243-322`]

### Runtime, operator, and integration contracts

- Runtime errors have a centrally enumerated canonical set and the operator routing policy must map every canonical code exactly once before routing. [`services/operator_routing/router.py:8-57`, `services/operator_routing/router.py:87-111`]
- The six operator-record schema families are closed Draft 2020-12 contracts: task, blocker, revision request, workflow defect, escalation, and resolution. [`tests/contracts/test_operator_records.py:12-19`, `tests/contracts/test_operator_records.py:60-68`]
- Workflow events are already a closed append-only contract requiring event id, event type, schema version, occurrence time, correlation id, idempotency key, identity, integration mode, and payload. The allowed event types are enumerated by schema and tested against the catalog. [`standards/integrations/workflow-event.schema.json:4-19`; `tests/contracts/test_integration_contracts.py:52-71`]
- Simulated and live events, n8n commands, and Notion projections are deliberately distinct through exclusive `simulation_id` or `live_connection_id` fields. [`standards/integrations/workflow-event.schema.json:21-36`; `standards/integrations/n8n-command.schema.json:18-31`; `standards/integrations/notion-projection.schema.json:11-24`]
- Notion projections are operational only: they declare `transition_service` as authority and cannot be atomic state writers. n8n commands are restricted to dispatch, wait, retry, resume, and dead-letter, not approval or completion. [`standards/integrations/notion-projection.schema.json:7-20`; `standards/integrations/n8n-command.schema.json:7-30`; `tests/contracts/test_integration_contracts.py:82-124`]

### Domain, storage, and portability constraints

- Domain validation resolves versioned schemas and validates market, reference, location, service-area, local-scope, GBP, locale, and YMYL evidence semantics. [`services/domain_contract/validator.py:18-24`, `services/domain_contract/validator.py:67-80`, `services/domain_contract/validator.py:102-189`]
- All ten real customer-domain fixtures validate. They cover local medical, regional care, regional expert, programmatic local, national B2B, English international resort, international speaker, cross-border finance, Sri Lankan Ayurveda DACH, and sensitive education retreat. [`tests/test_domain_contract_validator.py:24-30`; `tests/fixtures/domain/real-customer-matrix/local-medical.json:1`; `tests/fixtures/domain/real-customer-matrix/regional-care.json:1`; `tests/fixtures/domain/real-customer-matrix/regional-solo-expert.json:1`; `tests/fixtures/domain/real-customer-matrix/programmatic-local-satellite-network.json:1`; `tests/fixtures/domain/real-customer-matrix/national-b2b.json:1`; `tests/fixtures/domain/real-customer-matrix/english-international-resort-ota-social.json:1`; `tests/fixtures/domain/real-customer-matrix/international-speaker-brand.json:1`; `tests/fixtures/domain/real-customer-matrix/cross-border-finance.json:1`; `tests/fixtures/domain/real-customer-matrix/sri-lankan-ayurveda-dach.json:1`; `tests/fixtures/domain/real-customer-matrix/sensitive-education-retreat.json:1`]
- Existing output-path containment resolves only versioned V2 destinations below an existing workspace, rejects unsafe identifiers, path escape, symlink or Windows reparse-point traversal, and overwrites. [`services/preflight_common/output_paths.py:10-18`, `services/preflight_common/output_paths.py:33-71`; `tests/test_controlled_output_paths.py:10-39`]
- The plan confines customer event data to the individual customer workspace at `v2/operator/events/`. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:615-623`] This preserves the framework/customer-workspace separation required by the project rules. [`AGENTS.md:8-25`]

## Required Sprint 4 Changes

The plan explicitly requires `services/operator_api/app.py`, `repository.py`, `models.py`, `event_store.py`, the two integration simulators, their associated tests, and an API integration suite. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:598-655`]

The API must not create a second workflow engine. Sprint 4 requires every command to pass through Transition Service or Routing Service, while simulators must not duplicate core gate, hash, revision, or transition rules. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:609-614`, `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:636-643`]

## Recommended Local FastAPI Architecture

### Process boundaries

**Design decision:** Build one local ASGI application in `services/operator_api/app.py`. It composes four narrow components:

1. `models.py`: Pydantic request and response envelopes generated from, or explicitly mapped to, the existing JSON schemas. It validates HTTP shape only and does not reimplement business rules.
2. `repository.py`: read-model reconstruction and customer-workspace access. It receives a configured workspace root rather than accepting arbitrary filesystem paths from requests.
3. `event_store.py`: append and scan operations only, including idempotency lookup and a workspace-local writer lock.
4. `app.py`: HTTP routing, dependency injection, exception-to-HTTP mapping, OpenAPI publication, and readiness checks.

The application should invoke `services.transition_service.process_transition` for state-changing transition commands and `services.operator_routing.route_error` for emitted core errors. Those two existing services are the mandatory delegated rule authorities. [`services/transition_service/service.py:181-346`; `services/operator_routing/router.py:104-111`]

### Read-only endpoints

**Design decision:** Expose only derived projections, never mutable raw files, beneath a tenant and project scope:

- `GET /healthz` and `GET /readyz`
- `GET /v1/tenants/{tenant_id}/projects`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/workflow`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/steps/{step_id}`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/artifacts`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/gates`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/tasks`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/tickets`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/assignments`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/performance-checkpoints`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/metrics`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/adjustment-proposals`
- `GET /v1/tenants/{tenant_id}/projects/{project_id}/integrations/status`

These resources exactly implement the planned read-only families. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:598-607`] The workflow response must make `3b` visible as `not_due` until a valid post-publication checkpoint is due, consistent with project state and the graph. [`00_admin/PROJECT_STATE.md:87-93`; `standards/workflow/workflow-graph.json:25-27`]

### Command endpoints and request contracts

**Design decision:** Use `POST /v1/tenants/{tenant_id}/projects/{project_id}/commands/{verb}` for the planned verbs: `start`, `request-revision`, `request-input`, `create-defect`, `escalate`, `request-waiver`, `approve`, `reject`, `resolve`, and `resume`. Each body must include `command_id`, `idempotency_key`, `correlation_id`, `expected_revision`, target run and step identity, and a typed payload. The API must verify that route identity equals body identity before delegating.

`start`, `approve`, and `resume` must construct or carry the current transition-command shape and call Transition Service. The transition schema already provides the allowed operations and conditional requirements, so FastAPI models must not weaken them. [`standards/runtime/transition-command.schema.json:5-18`; `services/transition_service/service.py:219-346`] The remaining command verbs should validate and persist their existing operator-record contract, create typed workflow events, and use Routing Service for any core failure. Existing operator records and events are closed contracts, rather than free-form endpoint payloads. [`tests/contracts/test_operator_records.py:47-93`; `standards/integrations/workflow-event.schema.json:4-56`]

**Design decision:** Return a stable command-result envelope with `command_id`, `correlation_id`, `replay`, `events`, an optional current projection, and `errors`. Preserve core error codes verbatim. Do not expose a success result before its event append succeeds.

### Append-only event store, idempotency, and concurrency

**Design decision:** Use UTF-8 JSON Lines, one complete `workflow-event.schema.json` object per line, at a deterministic contained path beneath `<customer-workspace>/v2/operator/events/`, for example `events.jsonl`. This filename is intentionally a proposed layout, not a current contract. It honors the required customer-workspace root and event fields. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:615-623`; `standards/integrations/workflow-event.schema.json:4-19`]

**Design decision:** Under one workspace-local exclusive lock, scan for the idempotency key and canonical request fingerprint before append. A same fingerprint returns the previously recorded result as `replay: true`; a different fingerprint returns `ERR_IDEMPOTENCY_CONFLICT` and does not append. This follows the demonstrated Transition Service semantics. [`services/transition_service/service.py:81-84`, `services/transition_service/service.py:203-217`; `tests/test_transition_service.py:217-225`]

**Design decision:** Append one newline-terminated serialized event using a temporary adjacent file plus atomic replacement only for compacted projections or idempotency indexes. Do not rewrite the JSONL event log. Reuse the existing create-only lock and atomic-write approach rather than introduce platform-specific `fcntl`; the current test intentionally verifies import without `fcntl`. [`services/transition_service/service.py:53-65`, `services/transition_service/service.py:349-353`; `tests/test_transition_service.py:233-270`]

### Tenant isolation and containment

**Design decision:** Resolve a tenant and project only from server-side workspace configuration or an authenticated tenant-project registry. Never concatenate request-provided path components. Validate `tenant_id` and `project_id` against the loaded project/run records, and reject mismatches before any read or append with the existing `ERR_TENANT_ISOLATION` code. The transition core already rejects identity mismatch. [`services/transition_service/service.py:219-229`]

**Design decision:** All repository and event-store paths must use an existing resolved workspace root, `relative_to(root)` containment checks, and rejection of symlink or reparse-point components. Reuse or extract the behavior in `resolve_step_output`; do not implement a weaker duplicate containment check. [`services/preflight_common/output_paths.py:33-71`]

### Error mapping

**Design decision:** Map schema or Pydantic shape failures to 422 with structured field paths. Map unknown contained resources to 404. Map core state, stale approval, stale revision, gate, artifact, and tenant-isolation failures to 409 with the canonical error envelope. Map idempotency conflicts and lock contention to 409. Map unready local dependencies, such as unreadable workspace or invalid policy, to 503. Do not translate or invent domain error strings: the Routing Service has an exhaustive policy check and Transition Service emits canonical envelopes. [`services/operator_routing/router.py:87-111`; `services/transition_service/service.py:317-327`; `standards/runtime/error-envelope.schema.json:1-16`]

### OpenAPI, generated types, startup, and readiness

**Design decision:** Use FastAPI's emitted OpenAPI document as the sole HTTP schema source and generate the planned `apps/operator-console/src/generated/api-types.ts` only from that document. The plan forbids separately invented UI contract types. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:645-649`]

**Design decision:** Startup must load the workflow graph, gate registry, error-routing policy, integration schemas, and configured workspace roots, validate their parseability and policy completeness, then fail process startup on error. `GET /readyz` should return ready only after those checks and a contained event-store probe succeed. This is consistent with the project fail-fast rule and Routing Service policy validation. [`AGENTS.md:42-45`; `services/operator_routing/router.py:80-101`]

**Design decision:** Keep portability to `pathlib`, `os.replace`, create-only lock files, and no shell execution. This is necessary because the existing transition suite explicitly validates a no-`fcntl` import path and output paths expressly account for Windows reparse points. [`tests/test_transition_service.py:20-24`, `tests/test_transition_service.py:233-241`; `services/preflight_common/output_paths.py:66-71`]

## Dependency and Runtime Accounting

`requirements-app.txt` is the sole application dependency plan inspected. It pins exactly FastAPI `0.141.1`, Starlette `1.6.0`, Pydantic `2.13.4`, Pydantic Core `2.46.4`, Uvicorn `0.52.3`, HTTPX `0.28.1`, HTTPCore `1.0.9`, AnyIO `4.14.2`, h11 `0.16.0`, Click `8.4.2`, annotated-doc `0.0.5`, annotated-types `0.8.0`, typing-inspection `0.4.4`, typing-extensions `4.16.0`, Certifi `2026.7.22`, idna `3.19`, sniffio `1.3.1`, and `jsonschema[format]` `4.26.0`. [`requirements-app.txt:1-20`] Development contract validation already pins `jsonschema[format]` `4.26.0`. [`requirements-dev.txt:1-3`]

No dependency additions are recommended. The master plan requires exact pins, a lock, or vendored Linux wheels and prohibits a live PyPI dependency in the final OMO build. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:587-596`] **Design decision:** the implementation gate must verify the approved offline wheel or lock source resolves this exact file before an OMO execution. HTTPX is already pinned but should not be used to contact Notion, n8n, providers, or other network services in Sprint 4's simulator mode.

## Contradictions and Risks

1. The plan calls `3b` a post-publication adjustment and project state describes it as `not_due` until real post-publication data, but Transition Service accepts a special `4b -> 3b` predecessor path. The API must expose it as a sideflow and require the `post_publication` operation and due-check evidence. It must not add `3 -> 3b` as an initial edge. [`standards/workflow/workflow-graph.json:16-27`; `services/transition_service/service.py:100-119`; `00_admin/PROJECT_STATE.md:87-93`]
2. The master plan names `request-waiver` and `reject` API verbs, but the existing Transition Service operation enum has neither. They must remain typed operator workflows and events until a separate approved core-contract change defines their transition semantics. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:609-614`; `standards/runtime/transition-command.schema.json:8-12`]
3. The plan says Notion is the central operational interface, while the implemented projection schema names Transition Service the state authority. The simulator must project events to Notion-shaped records and turn edits into typed commands only, never state writes. [`00_admin/DECISIONS.md:86-89`; `standards/integrations/notion-projection.schema.json:7-20`; `tests/contracts/test_integration_contracts.py:82-100`]
4. The precise event-log filename, response models, HTTP status mapping, authentication mechanism, and tenant-to-workspace registry format are not implemented contracts. This report labels them design decisions and they need a Sprint 4 review before coding.

## Required Test Coverage

Add `tests/test_operator_api.py`, `tests/test_notion_simulator.py`, `tests/test_n8n_simulator.py`, and integration tests specified by Sprint 4. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:598-655`] At minimum, cover:

1. Every read-only endpoint with a projection based on a valid real-customer fixture, including local, national, programmatic local, multilingual and regulated cases from all ten fixture files. [`tests/test_domain_contract_validator.py:24-30`]
2. Route/body identity mismatch, cross-tenant query, unknown project, traversal identifier, symlink or reparse-point escape, and unreadable workspace. Existing containment tests establish the expected rejection family. [`services/preflight_common/output_paths.py:33-71`; `tests/test_controlled_output_paths.py:23-39`]
3. `start`, `approve`, and `resume` delegated through Transition Service: valid progression, machine-gate failure, stale revision and hash, expired approval, missing human gate, retry limit, and no mutation on failure. [`tests/test_transition_service.py:168-231`]
4. Identical replay returns the same command result without a second event, conflicting replay returns `ERR_IDEMPOTENCY_CONFLICT`, and concurrent writers leave exactly one append. [`tests/test_transition_service.py:217-225`, `tests/test_transition_service.py:298-322`]
5. JSONL append-only behavior, event-schema validation, correlation propagation, simulated-only event and command fixtures, and rejection of live masquerading. [`standards/integrations/workflow-event.schema.json:7-36`; `tests/contracts/test_integration_contracts.py:58-80`, `tests/contracts/test_integration_contracts.py:107-124`]
6. Notion projection remains non-authoritative after a field edit and emits a typed command rather than a canonical state mutation. [`tests/contracts/test_integration_contracts.py:82-100`]
7. n8n simulator covers the mandated golden path, reject path, missing input, defect, escalation, waiver, role task distribution, day 30/60/90 checkpoint, metric import, 3b proposal, wait/resume, retry, and DLQ. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:636-655`]
8. Startup and readiness failures for missing graph, invalid routing policy, invalid registry, missing customer root, and unavailable local event store. The system must fail fast rather than silently downgrade. [`AGENTS.md:42-45`; `services/operator_routing/router.py:87-101`]
9. Windows and Linux portability: no `fcntl` requirement, create-only lock contention, atomic result behavior, and reparse-point containment. [`tests/test_transition_service.py:233-322`; `services/preflight_common/output_paths.py:66-71`]
10. OpenAPI snapshot validation and generated TypeScript type regeneration from the API document, with no hand-authored duplicate UI type. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:645-649`]

## Safe Disjoint Implementation Packages

1. Package A owns `services/operator_api/app.py`, `models.py`, `repository.py`, `event_store.py`, and `tests/test_operator_api.py`. It imports contracts and existing services without editing them.
2. Package B owns `services/integrations/notion_simulator.py`, `services/integrations/n8n_simulator.py`, integration fixtures, `tests/test_notion_simulator.py`, and `tests/test_n8n_simulator.py`. It consumes Package A's public command/event interfaces without editing API files.
3. Package C runs OpenAPI generation into `apps/operator-console/src/generated/api-types.ts` only after Package A freezes the document. This follows the plan's ban on UI type edits during type generation. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:1030-1044`]
4. No Sprint 4 worker should modify `standards/`, `services/transition_service/`, `services/operator_routing/`, shared project state, workflow graph, or existing contract tests unless a separately approved contract change is required. The master plan reserves shared registry, workflow graph, and project state for Hermes. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:1030-1044`]

## Build Recommendation and Review Gates

Build the local FastAPI API as a thin adapter and projection layer around the existing Transition Service, Routing Service, schemas, and customer workspace. Persist only schema-valid simulated workflow events in a contained append-only log. Derive all reads, Notion fixtures, and n8n behavior from that event stream. Do not add dependencies or create direct status-mutating endpoints.

Approval gates before merge:

1. Contract gate: all existing workflow, runtime, operator, integration, domain, transition, and containment tests pass unchanged, plus the required API and simulator tests.
2. Authority gate: code review proves every status change reaches Transition Service, every runtime error reaches Routing Service, and Notion/n8n have no canonical state-write path.
3. Storage gate: event append, replay, conflict, locking, tenant isolation, path containment, Windows reparse-point, and Linux no-`fcntl` tests pass.
4. Offline runtime gate: exact `requirements-app.txt` pins resolve from the approved OMO offline-wheel or lock source, with no live PyPI, provider, crawler, or network call. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:587-596`]
5. Integration gate: the full local API, event, Notion simulator, and n8n simulator workflow covers the planned 30/60/90 cycle and has no P0 or P1 review findings. [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:651-655`; `00_admin/DECISIONS.md:87-89`]
