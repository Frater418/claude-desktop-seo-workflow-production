# Hermes Gateway LLM Execution Adapter Implementation Plan

> **For implementation:** Use only the execution path authorized by Raphael and the project rules. Hermes briefs only root Sisyphus. Sisyphus owns internal decomposition. No native Hermes subagents, commit, push, merge, deployment or gateway configuration change is authorized by this plan.

**Author:** Raphael Rechberger
**Status:** Approved planning insertion, not authorized for implementation
**Created:** 2026-08-23
**Timing:** M08L after M08 output-quality closure and its GitHub snapshot, before M09 Release Audit

**Execution ownership:** Option A approved by Raphael on 2026-08-23. Root Sisyphus owns the Heartweb repository implementation. Hermes owns the Hermes Gateway boundary, dedicated profile setup, capability probe, model and reasoning policy verification, live neutral Gateway proof and independent acceptance review.

**Goal:** Add a provider-neutral Heartweb LLM execution seam with a test-only Hermes Gateway backend so M10 can execute real model calls through a dedicated isolated Hermes profile while Heartweb retains all state, validation, revision and approval authority.

**Architecture:** Existing `ContextPackage`, `LLMRunRequest`, `LLMRunResult`, Worker Profile, Prompt Registry and runtime persistence remain authoritative. A new injected execution backend interface replaces the fixture-only dispatch seam. The first live backend calls the Hermes OpenAI-compatible Runs API through a dedicated `heartweb-runtime` profile. The existing local fixture path remains available as a separate explicit simulated backend. Direct official API backends remain the production target after the first controlled local output.

**Tech Stack:** Python 3.11 standard library HTTP client, existing FastAPI Operator API, existing JSON Schema Draft 2020-12 contracts, Hermes API Server `/v1/runs`, existing file repository and diagnostic trace, focused `unittest` and TypeScript tests.

---

## 1. Roadmap insertion

This plan does not add an eleventh Release Main Task and does not renumber the canonical 13-stage Sprint roadmap.

```text
M08 output quality closes
-> stable M08 GitHub WIP snapshot
-> M08L Hermes Gateway LLM execution adapter
-> focused live neutral LLM execution proof
-> M09 route-based Release Audit
-> M10 first controlled local customer output
```

M08L is a release prerequisite beneath the existing M08 to M09 edge. It must be reflected in `00_admin/MASTER_TASK_MATRIX.md` and `.json` only when implementation is authorized at the stable M08 gate.

M09 must not audit a fixture-only runtime while M10 is expected to use a real model. M08L therefore executes before M09.

## 2. Current implementation basis

The following current authorities are reused and not replaced:

- `standards/runtime/context-package.schema.json`
- `standards/runtime/llm-run-request.schema.json`
- `standards/runtime/llm-run-result.schema.json`
- `standards/runtime/worker-profile.schema.json`
- `standards/runtime/official-prompt-registry.json`
- `services/context_builder/`
- `services/operator_api/runtime.py`
- `services/operator_api/local_e2e.py`
- `services/operator_api/repository.py`
- `services/operator_api/recovery_inventory.py`
- `services/operator_api/diagnostic_trace_*`
- `tests/fixtures/context_builder/positive-worker-profile.json`

Current gap:

- `LocalRuntimeService` dispatches only an explicitly approved local fixture.
- It fabricates the deterministic test `LLMRunResult` around fixture bytes.
- There is no live model transport behind `LLMRunRequest`.
- The current Worker Profile identifies provider and model but does not bind a versioned execution backend or delegation policy.

## 3. Binding decisions

### 3.0 Approved implementation ownership

Option A is binding for M08L.

Root Sisyphus owns:

- Heartweb runtime contracts and fixtures
- `LLMExecutionBackend` and router implementation
- fixture backend extraction
- Hermes backend code inside the Heartweb repository
- Operator API composition and runtime integration
- execution-record persistence, replay and recovery
- focused repository tests and implementation evidence

Hermes owns:

- read-only probe of the installed Hermes API Server
- sanitized capability and response fixtures supplied at the agreed handoff boundary
- dedicated `heartweb-runtime` profile setup outside the Heartweb repository
- local interactive OAuth handoff to Raphael without reading or copying tokens
- model catalog inspection and final model/reasoning profile recommendation
- API Server key and loopback-boundary verification without exposing secret values
- one real neutral Gateway execution proof
- independent review of Heartweb identities, hashes, tool use, model provenance and failure behavior

Writer boundary:

1. Sisyphus remains the only writer to Heartweb implementation paths during M08L.
2. Hermes does not patch Sisyphus-owned repository files while the Root implementation wave is active.
3. Hermes-side profile and Gateway configuration stays outside the Heartweb repository and contains no customer artifacts.
4. Sanitized probe fixtures enter the repository only through the Root-controlled implementation handoff.
5. Final acceptance is based on real files, contracts, focused tests and a live neutral run, not either agent's narrative report.

Execution sequence:

```text
M08 stable gate
-> Hermes controller creates and verifies GitHub WIP snapshot
-> Hermes performs read-only Gateway capability probe
-> Root Sisyphus implements the Heartweb adapter against sanitized observed contracts
-> Hermes configures and verifies the isolated heartweb-runtime boundary
-> Root closes focused code and recovery evidence
-> Hermes runs independent live neutral acceptance proof
-> M08L closes
-> M09 begins
```

### 3.1 Heartweb remains authority

Hermes returns an artifact candidate only. Hermes cannot:

- change workflow status
- approve or reject a gate
- select tenant, project, run or revision
- release an artifact
- write canonical Heartweb records directly
- invent provider metrics or customer facts

Heartweb validates and persists the returned candidate through existing contracts and revision services.

### 3.2 Test backend versus production backend

The first adapter is explicitly:

```text
execution_backend: hermes_gateway
profile: heartweb-runtime
auth_mode: oauth
environment: local_test
production_eligible: false
```

The first official direct provider adapter is a separate post-M10 production-hardening package. Heartweb must not call raw OpenAI Codex OAuth endpoints directly.

### 3.3 Dedicated Hermes profile

Do not use the default personal Hermes profile.

The `heartweb-runtime` profile must have:

- separate sessions and state
- Memory and user-profile injection disabled
- no unrelated skills
- no customer cross-session reuse
- restricted API-server toolsets
- no terminal, messaging, browser, file-write or deployment tools by default
- explicit model and provider configuration
- explicit API server key
- no Gateway autostart change on Raphael's Windows machine

### 3.4 Fresh session per Heartweb run

Initial Step, next Step and revision requests use a fresh Hermes run. Heartweb does not depend on Hermes conversation continuity.

Retries or resume may use a cache hint only when the existing `dispatch_policy` and exact context hashes permit it.

### 3.5 Subagents are optional and bounded

The first vertical slice uses one Hermes agent run with delegation disabled.

A later optional delegation policy may permit high-value Steps 1B, 1C, 4A or 4B to use at most two leaf reviewers and one review round. This is not part of the initial M08L acceptance gate unless Raphael separately enables it.

### 3.6 OAuth credential ownership

OAuth credentials are not transmitted by Heartweb and are never included in an agent brief, plan, Context Package, LLM request, trace, artifact or Git record.

The ownership boundary is:

```text
Raphael performs one local interactive authorization
-> dedicated heartweb-runtime Hermes profile stores and refreshes OAuth internally
-> Heartweb authenticates only to the local Hermes API Server with its own API_SERVER_KEY
-> Hermes authenticates to the upstream model provider
```

Heartweb records only non-secret provenance:

- `auth_mode: oauth`
- Hermes profile identifier
- provider identifier
- model identifier
- reasoning effort
- timestamps, token usage and hashes

Do not copy OAuth token files from the default profile. Do not pass OAuth access tokens, refresh tokens, authorization codes or device codes to root Sisyphus or any worker. If the dedicated profile is not authorized, M08L stops with `ERROR_LLM_BACKEND_AUTH` and Raphael completes the local interactive authorization outside the agent run.

### 3.7 Versioned model and reasoning policy

The verified current local route is `openai-codex/gpt-5.6-sol` with global reasoning `high`. Using that combination for every workflow Step is intentionally rejected as wasteful and slower than necessary.

The Worker Profile must bind a versioned `inference_policy` containing at least:

- exact provider and allowed model IDs
- default model ID
- reasoning effort
- maximum output tokens
- timeout
- fallback mode
- maximum agent and tool rounds
- delegation policy reference

The initial fallback mode is `fail_closed`. A missing or exhausted preferred model must not silently switch model family, provider or reasoning tier because that would change output provenance and make model comparisons unreliable.

Initial logical profile matrix:

| Step | Logical profile | Initial model class | Reasoning | Rationale |
|---|---|---|---|---|
| 0 | `worker-profile-intake-structured` | fastest validated structured 5.6 tier | low | extract and validate supplied facts, no strategic invention |
| 1 | `worker-profile-pillar-strategy` | balanced 5.6 tier | medium | strategic synthesis with bounded structure |
| 1B | `worker-profile-site-architecture-deep` | `gpt-5.6-sol` | high | high-value information architecture and cross-page reasoning |
| 1C | `worker-profile-design-system` | balanced 5.6 tier | medium | structured template and design-system specification |
| 2 | `worker-profile-keyword-classification` | fastest validated structured 5.6 tier | low | metrics come from tools; model classifies rather than invents data |
| 3 | `worker-profile-roadmap-planning` | balanced 5.6 tier | medium | deterministic solver owns capacity; model explains and prioritizes |
| 3B | `worker-profile-performance-analysis` | balanced 5.6 tier | medium, high only for ambiguous adjustment proposals | real metrics constrain the analysis |
| 4A | `worker-profile-copywriter-briefing-deep` | `gpt-5.6-sol` | high | highest-value semantic and editorial briefing synthesis |
| 4B | `worker-profile-developer-spec` | balanced 5.6 tier or `gpt-5.6-sol` | medium | typed Page Spec plus deterministic renderer reduces free reasoning need |

The exact fast and balanced model IDs are selected from the authenticated `heartweb-runtime` model catalog during Task 1. They must not be guessed in contracts. If only `gpt-5.6-sol` is available in the first test profile, use the same model with low, medium or high reasoning according to the matrix rather than forcing high everywhere.

Escalation policy:

1. Start at the profile's assigned tier.
2. Schema or identity failure is fixed at the input or contract layer, not by increasing reasoning.
3. A human quality rejection may create a new revision using one higher reasoning tier.
4. Only repeated strategic inadequacy may justify a stronger model profile.
5. Independent high-reasoning review is reserved for 1B, 4A, 4B and final real-output acceptance.

## 4. Hermes transport choice

Use the Hermes API Server Runs API rather than Chat Completions:

```text
POST /v1/runs
GET  /v1/runs/{run_id}
GET  /v1/runs/{run_id}/events
POST /v1/runs/{run_id}/stop
GET  /v1/capabilities
GET  /health/detailed
```

Reasons:

- explicit run ID
- reconnectable status
- lifecycle events
- suitable for long model and tool work
- no dependence on a held streaming connection
- clear correlation with Heartweb `llm_run_request_id`

The initial adapter may poll `GET /v1/runs/{id}` with a bounded timeout. SSE event consumption is optional for the first vertical slice and must not create a second Heartweb event authority.

## 5. Secrets and network boundary

Use secret aliases only:

- `HEARTWEB_HERMES_API_BASE_URL`
- `HEARTWEB_HERMES_API_KEY`
- `HEARTWEB_HERMES_PROFILE`

Rules:

- API Server binds to loopback for local testing.
- No API key enters a Context Package, LLM request, artifact, event, trace or Git file.
- Browser code never receives the Hermes API key.
- Operator API calls Hermes server-to-server.
- Errors redact Authorization headers and response bodies that may contain credentials.
- Missing base URL, key or profile stops with a stable error before creating a Heartweb artifact.
- Missing or expired upstream OAuth remains an internal Hermes profile condition and maps to `ERROR_LLM_BACKEND_AUTH`; no OAuth material crosses the adapter boundary.

## 6. New runtime contracts

Prefer additive contracts rather than breaking the existing v1 request and result fixtures. Version the existing Worker Profile schema and fixtures when adding `inference_policy`; do not hand-wave reasoning settings outside the hashed profile.

### Modify `standards/runtime/worker-profile.schema.json`

Add a required versioned `inference_policy` with:

- `reasoning_effort`: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` or `ultra`
- `max_output_tokens`
- `timeout_seconds`
- `fallback_mode`: initially `fail_closed`
- `max_agent_turns`
- `max_tool_rounds`
- `delegation_policy_ref`

Update positive and negative fixtures and ensure the complete Worker Profile hash binds these values.

### Create `standards/runtime/llm-execution-backend.schema.json`

Required fields:

- `execution_backend_id`
- `schema_version`
- `backend_version`
- `backend_kind`: `local_fixture`, `hermes_gateway`, later `direct_api`
- `provider_id`
- `allowed_model_ids`
- `default_model_id`
- `profile_id`
- `transport`
- `timeout_seconds`
- `poll_interval_seconds`
- `max_tool_rounds`
- `delegation_policy_ref`
- `enabled`
- `created_at`

### Create `standards/runtime/llm-execution-record.schema.json`

Required fields:

- Heartweb tenant, project, run, step and revision
- `llm_run_request_id`
- `llm_run_result_id`
- `execution_backend_id` and version
- Hermes API run ID
- Hermes profile identifier
- provider and model IDs
- requested, started and finished timestamps
- terminal run status
- input, raw terminal output and normalized candidate hashes
- token usage when available
- tool-use count and allowed tool names
- delegation observation: disabled, not_used, used
- error class and provider error code when failed

This record stores provenance, not model reasoning.

### Optional future `standards/runtime/delegation-policy.schema.json`

Initial policy:

```text
allowed: false
max_workers: 0
max_depth: 0
max_rounds: 0
```

The optional bounded-review profile is deferred until the single-agent vertical slice is accepted.

## 7. Execution interface

### Create `services/llm_gateway/base.py`

Define one protocol:

```python
class LLMExecutionBackend(Protocol):
    def execute(
        self,
        request: Mapping[str, JsonValue],
        context_package: Mapping[str, JsonValue],
        prompt_bytes: bytes,
        output_contracts: tuple[Mapping[str, JsonValue], ...],
    ) -> BackendExecution:
        ...
```

`BackendExecution` contains:

- execution record fields
- raw terminal text bytes
- normalized candidate bytes
- provider and model observations
- token usage
- error metadata

### Create `services/llm_gateway/errors.py`

Stable codes:

- `ERROR_LLM_BACKEND_NOT_CONFIGURED`
- `ERROR_LLM_BACKEND_UNAVAILABLE`
- `ERROR_LLM_BACKEND_AUTH`
- `ERROR_LLM_BACKEND_TIMEOUT`
- `ERROR_LLM_BACKEND_RUN_FAILED`
- `ERROR_LLM_BACKEND_INTERACTION_REQUIRED`
- `ERROR_LLM_BACKEND_RESPONSE_INVALID`
- `ERROR_LLM_BACKEND_CONTEXT_MISMATCH`
- `ERROR_LLM_BACKEND_IDEMPOTENCY_CONFLICT`

### Create `services/llm_gateway/router.py`

Select the injected backend from a validated backend registry. Do not route based on free prompt text or UI model names.

## 8. Task graph

### Task 0: Stable insertion gate

**Objective:** Enter M08L only from a stable M08 checkpoint without contaminating active work.

**Prerequisites:**

- M08 closed
- controller-created GitHub WIP snapshot verified by remote SHA
- no Root writer active
- Project State and Main Matrix current
- explicit Raphael authorization to execute this plan

**Actions:**

1. Add M08L to `00_admin/MASTER_TASK_MATRIX.md` and `.json` beneath the M08 to M09 edge.
2. Add an active Decision for test-only Hermes execution.
3. Resume root Sisyphus only after the snapshot is confirmed.

**Verification:** Scoped `git diff --check` for planning and authority files. No product tests.

### Task 1: Probe installed Hermes API Server behavior

**Objective:** Record the exact transport contract of the installed Hermes version without changing Heartweb.

**Files:**

- Create: `00_admin/audits/<date>-m08l-hermes-llm-adapter/API_CAPABILITY_PROBE.json`
- Create: `tests/fixtures/hermes_gateway/capabilities.json`
- Create: `tests/fixtures/hermes_gateway/run-created.json`
- Create: `tests/fixtures/hermes_gateway/run-completed.json`
- Create: `tests/fixtures/hermes_gateway/run-failed.json`

**Probe:**

- `/health/detailed`
- `/v1/capabilities`
- `/api/model/options`
- `POST /v1/runs`
- `GET /v1/runs/{id}`
- profile-prefixed API path supported by the installed version

**Do not:**

- send customer data
- enable autostart
- modify the default profile
- start a delegated/subagent run

**Acceptance:** Exact sanitized request and response shapes are persisted as fixtures. No credential values are stored.

### Task 2: Add execution backend and execution record contracts

**Files:**

- Create: `standards/runtime/llm-execution-backend.schema.json`
- Create: `standards/runtime/llm-execution-record.schema.json`
- Create: `tests/test_llm_execution_contracts.py`
- Add fixtures under `tests/fixtures/runtime/`

**Red cases:**

- unknown backend kind
- model not allowed by backend
- missing profile
- missing terminal run ID
- request identity mismatch
- success without candidate hash
- failed run without stable error
- tool use outside allowed set
- delegation observed while policy disables it
- credential-like value in public execution record

**Focused verification:** Only new runtime contract tests and runtime schema loader cells.

### Task 3: Extract the fixture backend behind the common interface

**Objective:** Preserve all current simulated behavior while creating the adapter seam.

**Files:**

- Create: `services/llm_gateway/__init__.py`
- Create: `services/llm_gateway/base.py`
- Create: `services/llm_gateway/errors.py`
- Create: `services/llm_gateway/backends/__init__.py`
- Create: `services/llm_gateway/backends/local_fixture.py`
- Modify: `services/operator_api/runtime.py`
- Test: `tests/test_local_runtime.py`
- Test: new `tests/test_llm_gateway_fixture_backend.py`

**Rule:** Existing fixture bytes, request hashes, result hashes, persistence and replay remain byte-identical.

**Focused verification:** Fixture runtime and directly affected runtime persistence/recovery tests only.

### Task 4: Implement the Hermes Runs API client

**Files:**

- Create: `services/llm_gateway/hermes_api_client.py`
- Create: `tests/test_hermes_api_client.py`
- Use sanitized fixtures from Task 1

**Behavior:**

1. Require loopback or explicitly allowlisted base URL.
2. Send API Server bearer key only in Authorization header.
3. Create one fresh run with the Heartweb correlation ID.
4. Poll terminal status with bounded timeout and interval.
5. Reject approval, question or interaction-required states.
6. Preserve terminal provider/model observations.
7. Normalize network, HTTP, timeout, terminal failure and malformed response errors.
8. Never log the bearer key or raw headers.

**Focused verification:** Mock HTTP transport only. No real model call in this task.

### Task 5: Build the deterministic Hermes input envelope

**Files:**

- Create: `services/llm_gateway/hermes_input.py`
- Create: `tests/test_hermes_input.py`

**Input sections:**

- immutable Heartweb identity block
- exact Prompt Registry bytes and hash
- Context Package sources and hashes
- tool policy and allowed operations
- output contract IDs, versions and hashes
- instruction to return one JSON candidate only
- explicit prohibition on status, approval, identity and metric invention

**Rules:**

- No hidden conversation history.
- No personal Hermes memory.
- No source outside the Context Package.
- No raw secrets.
- Canonical envelope bytes and hash are deterministic.

### Task 6: Implement `HermesGatewayBackend`

**Files:**

- Create: `services/llm_gateway/backends/hermes_gateway.py`
- Create: `tests/test_hermes_gateway_backend.py`

**Behavior:**

1. Validate backend config and Heartweb identities.
2. Build deterministic Hermes input.
3. Start Hermes run.
4. Wait for terminal status.
5. Extract final candidate JSON bytes.
6. Reject prose wrappers, multiple candidates or additional undeclared fields.
7. Create an `llm-execution-record`.
8. Return candidate bytes to Heartweb.
9. Never persist directly from the backend.

**Red cases:**

- provider/model mismatch
- wrong Heartweb run identity echoed by model
- malformed JSON
- output contract mismatch
- unexpected tool call
- interaction requested
- timeout
- exact replay returns different candidate bytes

### Task 7: Refactor runtime orchestration to injected backend

**Files:**

- Modify: `services/operator_api/runtime.py`
- Modify: `services/operator_api/app.py`
- Modify: `services/operator_api/app_dependencies.py`
- Modify: `services/operator_api/local_e2e.py`
- Modify as needed: runtime persistence types and repository methods
- Test: `tests/test_local_runtime.py`
- Create: `tests/test_runtime_execution_backends.py`

**Required flow:**

```text
build and validate Context Package
-> build and validate LLMRunRequest
-> injected backend execute
-> validate execution record
-> validate candidate against LLMRunResult and output contracts
-> persist package, request, execution record and result atomically
-> create artifact candidate through existing services
```

**Invariant:** Backend output cannot write canonical workflow status or bypass artifact validation.

### Task 8: Persist execution provenance and recovery

**Files:**

- Modify: `services/operator_api/repository_runtime.py`
- Modify: `services/operator_api/repository_storage.py` if required
- Modify: `services/operator_api/recovery_inventory.py` only if a new runtime family is necessary
- Create: `tests/test_llm_execution_persistence.py`
- Create: `tests/test_llm_execution_recovery.py`

**Rules:**

- append-only execution records
- request and input hashes bind exact candidate
- exact replay returns existing accepted execution
- conflicting replay fails
- interrupted persistence is recoverable
- provider run retry receives a new execution record unless exact recovery applies
- no raw Authorization data persists

### Task 9: Configure the dedicated `heartweb-runtime` Hermes profile

**Scope:** Local setup procedure and capability verification only. Do not commit profile secrets to Heartweb.

**Configuration requirements:**

- dedicated profile state
- Memory disabled
- user profile disabled
- API Server key required
- local bind only
- restricted toolsets
- delegation disabled
- OpenAI Codex OAuth allowed only for local test classification
- fallback disabled for missing configured model

**Supporting file:**

- Create: `docs/integrations/hermes-llm-test-backend.md`

**Hard rule:** Do not enable Windows Gateway autostart. Gateway remains manually started for Raphael's local test phase.

### Task 10: Focused real neutral vertical slice

**Objective:** Prove one real model call without claiming customer-production readiness.

**Route:** Use one neutral approved Step whose output contract is already M08-verified. Prefer Step 1B or Step 4A based on the smallest complete fixture at execution time.

**Evidence:**

- Heartweb Context Package
- LLMRunRequest
- Hermes API run ID
- LLM execution record
- raw terminal response hash
- normalized candidate hash
- validated LLMRunResult
- persisted artifact candidate
- diagnostic trace

**Label:**

```text
execution_backend: hermes_gateway
auth_mode: oauth
environment: local_test
production_eligible: false
```

**Focused tests:** Exact backend, runtime, persistence and one selected Step validator/renderer closure. No complete repository suite or broad browser matrix.

### Task 11: Failure and interruption matrix

**Cases:**

- Hermes API unavailable before run
- authentication failure
- run timeout
- container/gateway restart during polling
- terminal run failed
- unexpected interaction request
- invalid structured output
- output contract failure
- persistence interruption after successful Hermes run
- replay after restart

**Acceptance:** Every case returns a stable Heartweb error and preserves the last valid canonical state.

### Task 12: Optional bounded reviewer profile design

**Status:** Planned, not release-blocking for initial M08L.

**Goal:** Define how a later high-value Worker Profile can request one independent review without open-ended delegation.

**Rules:**

- single generator remains default
- at most two leaf reviewers
- one review round
- no external side effects
- no child output becomes canonical directly
- Root output must cite which candidate findings it accepted or rejected
- token and time budget required

Do not implement until the single-agent vertical slice is reviewed by Raphael.

### Task 13: M08L closeout and M09 handoff

**Evidence report:**

- Create: `00_admin/audits/<date>-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`

**Required statements:**

- implemented versus planned adapters
- Hermes version and API capabilities
- dedicated profile and memory boundary
- exact model/provider used
- OAuth local-test limitation
- tools and delegation observed
- token usage
- focused commands run
- failure cases tested
- no canonical status mutation
- remaining production API work

**Gate:** M08L closes only when one neutral real model run reaches a valid Heartweb artifact candidate and every invalid case fails before canonical persistence.

After closeout, Root-Sisyphus may proceed to M09 only after the controller updates Project State and Matrix and confirms the snapshot boundary.

## 9. Targeted test matrix

This plan follows `standards/testing/PROTOTYPE_TEST_POLICY.md`.

| Delta | Required closure | Excluded by default |
|---|---|---|
| New runtime schemas | new contract tests and runtime schema loader | unrelated workflow, UI and Delivery tests |
| Fixture backend extraction | existing local runtime and direct persistence/recovery callers | browser and prompt quality tests |
| Hermes HTTP client | mock transport tests | real API call and unrelated Operator routes |
| Hermes backend | input, response, error and exact output contract tests | Provider Gateway and Delivery suites |
| Runtime integration | one selected Step plus runtime persistence/recovery | complete Step 0 to 4B route |
| Profile setup | capabilities and one local test run | gateway autostart, Telegram and other profiles |
| Real neutral vertical slice | one selected Step validator/renderer and runtime route | broad model benchmark and customer route |

A failure expands only to the proven direct dependency closure.

## 10. Security checklist

- [ ] API server key is secret-only and absent from Git.
- [ ] Hermes profile has no personal Memory or user profile.
- [ ] One fresh run per Heartweb request.
- [ ] No cross-tenant or cross-project session reuse.
- [ ] No browser receives Hermes credentials.
- [ ] No model can select Heartweb identities or revision.
- [ ] No Hermes output can approve a gate.
- [ ] No direct provider tool is allowed unless Heartweb Tool Policy names it.
- [ ] OAuth execution is labelled local-test and non-production.
- [ ] Fallback is disabled or fail-fast and visible.
- [ ] No hidden reasoning is persisted.
- [ ] Diagnostic trace contains only allowed provenance and errors.

## 11. Production follow-up after M10

The first controlled local output may use the Hermes test backend. Before external customer production at scale, create one official adapter behind the same interface:

- `services/llm_gateway/backends/openai_api.py`, or
- `services/llm_gateway/backends/anthropic_api.py`, or
- `services/llm_gateway/backends/google_api.py`

The choice follows a fixed AHD output benchmark. Do not implement all three before evidence shows a need.

Hermes Gateway remains available as:

- local test backend
- optional reviewer backend
- diagnostic supervisor
- manually authorized fallback

It is not the only production path.

## 12. Open questions and their status

No blocking user question remains for this implementation plan.

Technical questions resolved by Task 1:

1. Exact installed Hermes API response shape.
2. Whether the installed multi-profile listener uses profile-prefixed paths for the Runs API.
3. Exact provider and model observations exposed by the terminal run.

Later non-blocking decisions:

1. Which official API provider wins the post-M10 benchmark.
2. Whether bounded subagent review materially improves Step 4A/4B quality relative to token cost.
3. Whether the Hermes test backend moves from local Windows to the future VPS.

## 13. Explicit non-goals

- no direct raw OAuth implementation in Heartweb
- no use of Raphael's default Hermes profile
- no personal Memory in customer runs
- no autonomous gate approval
- no bidirectional Notion task callbacks
- no live Notion or live n8n work
- no Gateway autostart change
- no OpenCode/OMO production backend
- no unbounded subagents
- no multi-provider production router before M10
- no complete repository suite
- no commit, push, merge or deployment from this plan

## 14. Estimated focused effort

After stable M08 snapshot:

- capability probe and contracts: 2h to 4h
- adapter seam and Hermes client: 4h to 8h
- runtime persistence/recovery integration: 3h to 6h
- dedicated profile and real neutral run: 2h to 4h
- focused failure matrix and closeout: 2h to 4h

Total: approximately 13h to 26h focused engineering time, excluding provider or OAuth setup blockers.
