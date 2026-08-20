# Sprint 4 Stage A2 Runtime Contract Research

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Architecture research only. This report recommends the minimum Stage A2 contract family. It does not authorize implementation or change existing authority boundaries.

## Decision Summary

Adopt `stateful project, replaceable worker` from DEC-0019 as five closed JSON Schema Draft 2020-12 records plus deterministic semantic validation. Persist logical project history and source bindings. Treat every provider or technical session only as a recoverable cache hint. Keep artifact release, approval, workflow state, and error routing in their already implemented contracts and services.

The recommended contract IDs and files are exactly:

| File | Proposed schema ID | Record purpose |
| --- | --- | --- |
| `standards/runtime/logical-project-session.schema.json` | `https://heartweb.example/schema/runtime/logical-project-session.schema.json` | Durable, non-provider logical session for one tenant and project. |
| `standards/runtime/worker-profile.schema.json` | `https://heartweb.example/schema/runtime/worker-profile.schema.json` | Versioned worker identity, provider/model policy, and tool policy. |
| `standards/runtime/context-package.schema.json` | `https://heartweb.example/schema/runtime/context-package.schema.json` | Deterministic, immutable, ordered source set for one intended step revision. |
| `standards/runtime/llm-run-request.schema.json` | `https://heartweb.example/schema/runtime/llm-run-request.schema.json` | Validated request that binds a worker and context package before dispatch. |
| `standards/runtime/llm-run-result.schema.json` | `https://heartweb.example/schema/runtime/llm-run-result.schema.json` | Append-only execution observation, including output, token, timing, and error provenance. |

All five must set `$schema` to `https://json-schema.org/draft/2020-12/schema`, set `additionalProperties: false` at every object boundary, use only ASCII JSON values in shipped fixtures, and use the existing ID and lower-case SHA-256 conventions. They are additive. No existing schema ID or V1/V2 integration record changes in Stage A2.

## Implemented Facts And Boundaries

### Implemented authority model

- The active decision is [DEC-0019](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/DECISIONS.md:95): durable files, append-only events, released artifacts, evidence, decisions, gates, and revisions are authoritative. Context packages bind exact sources, hashes, prompt ID/version, worker, provider/model, tools, and tokens. Technical provider sessions are optional caches.
- [PROJECT_STATE](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/PROJECT_STATE.md:111) and [CURRENT_POINT_OF_WORK](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-19-e2e-demo/sprint-4/CURRENT_POINT_OF_WORK.md:100) mark Stage A2 planned, canonically approved, and not implemented. Therefore every contract below is proposed design, not current runtime behavior.
- `process_transition` in [services/transition_service/service.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:181) is the implemented atomic workflow state authority. It rejects tenant/project/run mismatches, stale revisions and input hashes, invalid graph edges, incomplete gates, stale approvals, and idempotency conflicts before returning a changed run.
- `route_error` in [services/operator_routing/router.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/operator_routing/router.py:104) is the canonical code-to-owner route. The Stage A2 validator must emit new canonical error codes only after adding them to its policy coverage. It must not invent a second routing mechanism.
- The current workflow graph in [workflow-graph.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/workflow/workflow-graph.json:1) owns the initial route, released-predecessor requirements, and 3b post-publication sideflow. Stage A2 may validate against it but must not encode a competing graph.

### Implemented records that Stage A2 must reference, not duplicate

| Existing contract | Existing fact | Stage A2 handling |
| --- | --- | --- |
| [run-envelope.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/run-envelope.schema.json:1) | A run has tenant, project, step, gate, revision, input hash, idempotency key, attempt, and status. | Reference `run_id`, `revision`, `step_id`, `input_hash`, and existing run state. Do not restate run lifecycle. |
| [artifact-record.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/artifact-record.schema.json:1) | Immutable artifact record binds tenant/project/run/step/revision, bytes hash, contract version, producer version, and controlled storage key. | Reference artifact ID, revision, content SHA-256, status and record storage key. Never embed artifact bytes or caller paths. |
| [evidence-record.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/evidence-record.schema.json:1) | Evidence carries provenance, time interval, jurisdiction, hash, and recorder. | Use evidence references with explicit `trust_level`; retain existing evidence record as evidence authority. |
| [quality-gate-run.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/quality-gate-run.schema.json:1) | Gate outcomes bind artifact bytes, policy/registry versions, findings, and check time. | Use immutable references only. A run result cannot create, pass, or waive a gate. |
| [approval-record.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/approval-record.schema.json:1) and [release-record.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/release-record.schema.json:1) | Approval and release are revision and artifact hash bound. | Context may include released predecessor and rejected-current references. LLM records cannot create either record or assert authority. |
| [revision-request.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/operator/revision-request.schema.json:1) | A revision request already contains current artifact/version/hash, findings, immutable constraints, evidence, reviewer feedback, and bounded attempt number. | Use a required `revision_request` reference for revision mode. Do not duplicate its findings or constraints as new authoritative records. |
| [workflow-event-v2.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event-v2.schema.json:1) | Events are append-only, idempotent, correlated, simulated/live disambiguated, and have closed V2 payloads. | Add future event types only through the event catalog in a later approved stage, not in Stage A2 schema work. |
| [notion-record-v2.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-record-v2.schema.json:1) | Notion records are typed projections with source event/revision and typed relations. | Future projection may display session/package/run records, but it remains non-authoritative. |
| [n8n-command.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-command.schema.json:1) | n8n transports versioned, correlated commands and does not own state. | Later dispatch carries a validated request ID and hash. It does not construct package inputs or authorize reuse. |

### Prompt and output facts

Every official prompt is already versioned in `<prompt_metadata>` and is an implementation input, not an implicit runtime contract. The registry must bind these existing files, their metadata, and their exact bytes:

| Step | Official prompt | Implemented prompt version | Relevant prohibition |
| --- | --- | --- | --- |
| 0 | [0-kickoff.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/0-kickoff.xml.md:4) | 1.5.0 | GATE-0 remains an operator action. |
| 1 | [1-pillar-identifikation.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1-pillar-identifikation.xml.md:4) | 2.0.0 | No approval, completion, next step, or direct provider call. |
| 1b | [1b-seitenarchitektur.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1b-seitenarchitektur.xml.md:4) | 2.0.0 | Only `awaiting_gate` transition. |
| 1c | [1c-pillar-template.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1c-pillar-template.xml.md:4) | 2.0.0 | Only `awaiting_gate` transition. |
| 2 | [2-cluster-recherche.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/2-cluster-recherche.xml.md:4) | 2.0.0 | No direct provider call or completion. |
| 3 | [3-120-tage-plan.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3-120-tage-plan.xml.md:4) | 2.0.0 | No approval, completion, or next step. |
| 3b | [3b-performance-check.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3b-performance-check.xml.md:4) | 2.0.0 | Original plan is immutable and a new revision is required. |
| 4a | [4a-content-briefing-und-schema.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4a-content-briefing-und-schema.xml.md:4) | 2.0.0 | No direct provider call, approval, completion, or next step. |
| 4b | [4b-landingpage-html.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4b-landingpage-html.xml.md:4) | 2.0.0 | No approval, completion, deployment, or direct provider call. |

The authoritative Step 0 artifact is Project V2 as required by the prompt suite and the E2E Masterplan Task 4.2. The Stage A2 contracts should use an explicit `project_source` reference with its contract identifier, artifact ID or canonical record ID, revision, controlled `storage_key`, and SHA-256. The context builder must not use a free-form `project_v2_path` supplied by a caller.

## Proposed Contract Family

### Common definitions

Each proposed schema defines these local reusable primitives instead of cross-file `$ref` dependencies:

- `tenant_id`: `^tenant-[a-z0-9][a-z0-9-]{2,63}$`
- `project_id`: `^project-[a-z0-9][a-z0-9-]{2,63}$`
- `run_id`: `^run-[a-z0-9][a-z0-9-]{7,63}$`
- `artifact_id`: `^artifact-[a-z0-9][a-z0-9-]{7,63}$`
- `evidence_id`: `^evidence-[a-z0-9][a-z0-9-]{7,63}$`
- `sha256`: `^[a-f0-9]{64}$`
- `step_id`: enum `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, `4b`
- ISO UTC timestamps using `format: date-time`
- semver values using `^[0-9]+\\.[0-9]+\\.[0-9]+$`

`storage_key` is a controlled logical identifier. It must match the existing tenant/project containment convention or a future project workspace registry key. It is not a filesystem path and does not allow `..`, absolute paths, URI schemes, symlinks, or opaque caller-supplied locations.

#### Source reference

Use one shared local definition named `source_ref` in Context Package. Required fields are `source_kind`, `source_id`, `tenant_id`, `project_id`, `revision`, `content_sha256`, `storage_key`, `source_status`, and `trust_level`. Optional fields are `run_id`, `step_id`, `contract_id`, `contract_version`, `recorded_at`, and `valid_until`.

- `source_kind` enum: `project_v2`, `official_prompt`, `released_predecessor`, `rejected_artifact`, `evidence`, `decision`, `quality_gate_run`, `revision_request`, `operator_instruction`, `output_contract`.
- `source_status` enum: `active`, `released`, `rejected`, `superseded`, `historical`.
- `trust_level` enum: `trusted`, `untrusted`, `not_applicable`.
- Only `evidence` can use `untrusted`; it must then carry `untrusted_reason`. This makes crawl, SERP, competitor, and similar external material data rather than instructions.
- Non-evidence sources must use `trusted` or `not_applicable`; external material must never be promoted by omission.

The hash is the hash of the exact persisted bytes represented by `storage_key`. The builder, not a client, resolves the key in the registered workspace and verifies the bytes before dispatch.

### 1. Logical Project Session

**File and ID:** `standards/runtime/logical-project-session.schema.json`, `https://heartweb.example/schema/runtime/logical-project-session.schema.json`.

**Purpose:** Represent the durable project continuity visible to an operator. It is not a run envelope, provider conversation, event store, approval, or status writer.

**Required fields:**

```text
logical_session_id, schema_version, tenant_id, project_id, project_source,
created_at, created_by, state_authority, technical_session_policy
```

**Closed properties:**

- `logical_session_id`: `^logical-session-[a-z0-9][a-z0-9-]{7,63}$`.
- `schema_version`: const `1.0.0`.
- `project_source`: a trusted `source_ref` with `source_kind: project_v2` and `source_status: released`.
- `created_by`: a non-empty actor ID, not a person name assumption.
- `state_authority`: const `local_core`.
- `technical_session_policy`: object with required `default_execution`, `reuse_allowed`, `reuse_authority`, `lost_handle_recovery`; constants `fresh_per_step_or_substantial_revision`, `true`, `cache_only`, `rebuild_from_context_package` respectively.
- Optional `closed_at` and `superseded_by_logical_session_id` permit archival without history overwrite.

**Semantic rules:** one active logical session exists per `(tenant_id, project_id)` in the repository index. The project source identity and hash must match the registered Project V2. Session records do not carry run status, artifacts, approvals, release IDs, provider credentials, technical session handles, or mutable context.

### 2. Official Prompt Registry And Cryptographic Binding

No sixth standalone schema is necessary in Stage A2. Use a versioned repository-owned JSON registry at `standards/runtime/official-prompt-registry.json`, validated by a local embedded validator definition in the Context Builder. It is configuration, not per-project state.

Each closed registry entry requires:

```text
step_id, prompt_id, prompt_version, prompt_path, prompt_sha256,
output_contract_id, output_contract_version, output_contract_path,
output_contract_sha256, active
```

Rules:

- `prompt_id` is `heartweb.step.<step_id>` and is unique.
- `prompt_path` is exactly one official file under `prompts/`; it is repository-relative and must resolve to the already listed prompt for the step.
- `prompt_sha256` is verified from bytes at build/validation time, not trusted from the package author.
- `output_contract_*` binds the canonical Step output contract already named by the prompt. This prevents output shape drift without duplicating the output schemas.
- Exactly one `active: true` entry per workflow graph step, including 3b. Historical prompt versions can remain inactive for historical run verification only.

This is the minimum registry because context packages need a stable `prompt_id`, semantic version, path, and exact hash. A cryptographic-only path without a registry would make it impossible to prove the file was official for the requested step. A copied prompt body inside every request would duplicate immutable repository content and create unnecessary mutation surface.

### 3. Worker Profile

**File and ID:** `standards/runtime/worker-profile.schema.json`, `https://heartweb.example/schema/runtime/worker-profile.schema.json`.

**Purpose:** Bind a replaceable logical worker to permitted execution behavior. It is a profile registry record, not a credential store or a provider session.

**Required fields:**

```text
worker_profile_id, schema_version, profile_version, display_name,
execution_kind, provider, model_policy, tool_policy, enabled, created_at
```

**Closed properties:**

- `worker_profile_id`: `^worker-profile-[a-z0-9][a-z0-9-]{2,63}$`.
- `execution_kind`: enum `llm` only for Stage A2.
- `provider`: required `provider_id`, `provider_kind`, `credential_ref`; `credential_ref` is a non-secret capability reference, never a key, token, URL, or endpoint.
- `model_policy`: required `allowed_model_ids`, `default_model_id`, `model_change_allowed`; `default_model_id` must be in `allowed_model_ids`; `model_change_allowed` is false in v1.
- `tool_policy`: required `tool_policy_id`, `policy_version`, `allowed_operations`, `direct_provider_calls_allowed`; `direct_provider_calls_allowed` is false. `allowed_operations` is a unique subset of `read_context`, `write_candidate_output`, `request_gateway_operation`.
- `enabled`: boolean.

**Semantic rules:** profile ID/version is looked up from a repository-owned profile registry. The selected request model must be the default model in v1. A tool policy cannot contain `approve_gate`, `reject_gate`, `release`, `complete_run`, `transition_state`, `mutate_project_state`, `direct_provider_call`, deployment, or arbitrary filesystem operations. `write_candidate_output` means writing controlled candidate output only, not changing Artifact, Gate, Approval, Release, or Run records.

### 4. Context Package

**File and ID:** `standards/runtime/context-package.schema.json`, `https://heartweb.example/schema/runtime/context-package.schema.json`.

**Purpose:** Freeze the complete ordered and hash-bound input set used for one run. This is the Stage A2 source-of-truth boundary for reproducibility.

**Required fields:**

```text
context_package_id, schema_version, tenant_id, project_id, run_id, step_id,
target_revision, trigger, logical_session_id, prompt, project_source,
worker_profile_ref, output_contract, sources, package_sha256, created_at,
created_by
```

**Closed properties:**

- `context_package_id`: `^context-[a-z0-9][a-z0-9-]{7,63}$`.
- `target_revision`: integer at least 1. It is the intended new artifact revision, never inferred from a provider response.
- `trigger`: enum `initial_step`, `next_step`, `revision`, `retry`, `resume`.
- `prompt`: required `prompt_id`, `prompt_version`, `prompt_path`, `prompt_sha256`; values must match the active registry entry for `step_id`.
- `project_source`: required trusted Project V2 source reference.
- `worker_profile_ref`: required `worker_profile_id`, `profile_version`, `content_sha256`.
- `output_contract`: required `contract_id`, `contract_version`, `contract_path`, `contract_sha256`; must match the prompt registry entry.
- `sources`: non-empty array of `source_ref`, unique by `(source_kind, source_id, revision, content_sha256)`, with an explicit `include_order` integer starting at 1 and contiguous through the array length.
- `package_sha256`: SHA-256 of the canonical package payload excluding `package_sha256`; serialize `ensure_ascii=true`, sorted keys, separators `(',', ':')`, UTF-8 bytes.

**Conditional schema rules:**

- `initial_step` requires no `released_predecessor`, `rejected_artifact`, or `revision_request` source and allows only Step 0 without a released predecessor.
- `next_step` requires at least one `released_predecessor` source, forbids `rejected_artifact` and `revision_request` sources, and requires a predecessor that matches the workflow graph edge.
- `revision` requires exactly one each of `released_predecessor` when the graph requires it, `rejected_artifact`, `revision_request`, and `operator_instruction`. It requires at least one `quality_gate_run` or a revision-request finding reference. It forbids target revision equal to the rejected artifact revision.
- `retry` requires target revision equal to the current run revision and requires no `rejected_artifact`, `revision_request`, or operator instruction. It must retain the same package source set as the original request except for a fresh package ID, created timestamp, and trigger.
- `resume` requires a blocking record or resolution source and retains the same target revision; it cannot convert a rejected artifact into a new revision.
- If any source is `untrusted`, its source kind must be `evidence`, its `untrusted_reason` is required, and it must be ordered after trusted instructions and contracts. It cannot satisfy required Project V2, prompt, predecessor, output-contract, decision, gate, or revision-request slots.

**Cross-record semantic rules:**

1. Every source has the package tenant and project. Any mismatch returns `ERROR_CONTEXT_TENANT_MISMATCH` before an LLM request exists.
2. Every `storage_key` resolves under the server-side tenant/project workspace registry. Missing content, containment failure, missing record, or byte hash mismatch returns respectively `ERROR_CONTEXT_SOURCE_MISSING`, `ERROR_CONTEXT_STORAGE_INVALID`, or `ERROR_CONTEXT_HASH_MISMATCH`.
3. `active` and `released` sources can be included according to their kind. `rejected` is allowed only as the required current artifact in revision mode. `superseded` and `historical` cannot be included as operational context. Return `ERROR_CONTEXT_SOURCE_STALE`.
4. A released predecessor must be backed by an existing release record whose tenant/project/run/step/artifact/revision/hash agree. The graph edge must agree with target step. Return `ERROR_CONTEXT_PREDECESSOR_INVALID`.
5. The rejected artifact must agree with the revision request current ID/revision/hash. Operator instruction must be bound to that revision request. Return `ERROR_CONTEXT_REVISION_BINDING_INVALID`.
6. Prompt, Project V2, worker profile, output contract, and all package sources are byte-verified before canonical hashing. The computed package hash must equal `package_sha256`, else `ERROR_CONTEXT_PACKAGE_HASH_MISMATCH`.
7. No duplicate source identity, no duplicate include order, and no free-form caller paths. Return `ERROR_CONTEXT_SOURCE_DUPLICATE` or `ERROR_CONTEXT_SOURCE_ORDER_INVALID`.
8. The package has no approval, release, transition command, run status mutation, user-provided prompt body, secret, provider response body, or output bytes. Those belong to their existing records or controlled storage.

### 5. LLM Run Request

**File and ID:** `standards/runtime/llm-run-request.schema.json`, `https://heartweb.example/schema/runtime/llm-run-request.schema.json`.

**Purpose:** The only dispatchable, validated intent to execute one worker. It does not equal a run envelope and does not imply that a provider call has occurred.

**Required fields:**

```text
llm_run_request_id, schema_version, tenant_id, project_id, run_id, step_id,
target_revision, correlation_id, idempotency_key, run_mode, logical_session_id,
context_package_id, context_package_sha256, worker_profile_id,
worker_profile_version, provider_id, model_id, tool_policy_id,
tool_policy_version, input_sha256, output_contract, dispatch_policy,
requested_at
```

**Closed properties:**

- `llm_run_request_id`: `^llm-request-[a-z0-9][a-z0-9-]{7,63}$`.
- `correlation_id` and `idempotency_key` use the existing integration patterns.
- `run_mode`: enum `initial_step`, `next_step`, `revision`, `retry`, `resume`; it must map one-to-one to Context Package `trigger`.
- `input_sha256`: exactly `context_package_sha256`. It exists only for compatibility with existing run and transition provenance terminology.
- `output_contract`: same four-field cryptographic binding as Context Package.
- `dispatch_policy`: required `execution`, `technical_session_reuse`; constants `fresh` and `forbidden` by default.
- Optional `technical_session_ref` is a closed object with `provider_id`, `session_handle_hash`, `observed_at`, `session_state`; no raw provider session handle is persisted. `session_state` enum: `available`, `missing`, `expired`, `invalid`.

**Conditional rules:**

- If `technical_session_reuse` is `forbidden`, `technical_session_ref` is absent.
- If `technical_session_reuse` is `cache_hint`, `technical_session_ref` is required and `execution` remains `fresh_or_reuse_after_validation`; this is allowed only when `run_mode` is `retry` or `resume` and the policy validator authorizes it.
- Initial, next-step, and revision requests require `execution: fresh` and forbid cache reuse.
- `technical_session_ref.provider_id` equals `provider_id`; its existence never alters the package hash, target revision, prompt, worker, model, tool policy, or input hash.

**Cross-record semantic rules:** a request is constructed only from a schema-valid, semantically valid Context Package whose identity fields match. The profile must be enabled and its provider/model/tool policy values must match the request. `idempotency_key` replays only byte-identical request canonical form. Same key with a changed package hash, target revision, worker, model, tool policy, or dispatch policy returns `ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT`. A request cannot contain approval, release, gate decision, transition operation, artifact status, completion status, or output content.

### 6. LLM Run Result

**File and ID:** `standards/runtime/llm-run-result.schema.json`, `https://heartweb.example/schema/runtime/llm-run-result.schema.json`.

**Purpose:** Immutable observed execution evidence. It is appended after a dispatch attempt and is not used as a state transition command.

**Required fields:**

```text
llm_run_result_id, schema_version, llm_run_request_id, tenant_id, project_id,
run_id, step_id, target_revision, context_package_id, context_package_sha256,
worker_profile_id, worker_profile_version, provider_id, model_id,
tool_policy_id, tool_policy_version, status, started_at, finished_at,
input_sha256, result_sha256, token_usage
```

**Closed properties:**

- `llm_run_result_id`: `^llm-result-[a-z0-9][a-z0-9-]{7,63}$`.
- `status`: enum `succeeded`, `failed`, `cancelled`.
- `token_usage`: closed object requiring non-negative integer `input_tokens`, `output_tokens`, `total_tokens`; semantic equality is `total_tokens = input_tokens + output_tokens`. Optional `cached_input_tokens` is non-negative and cannot exceed input tokens.
- `result_sha256`: SHA-256 of the canonical result payload excluding `result_sha256` and excluding volatile timestamps. This proves record identity without pretending that provider text is canonical source state.
- Optional `technical_session_observation`: `not_used`, `reused`, `missing`, `expired`, `invalid`; it is observational only.

**Success conditional:** `succeeded` requires `output` with `output_artifact_id`, `output_revision`, `output_sha256`, `output_storage_key`, `output_contract_id`, `output_contract_version`, and `output_contract_sha256`; it requires `error` to be absent. The output is only a candidate artifact reference. `output_revision` equals target revision. Result creation must verify stored output bytes and the output contract before recording success.

**Failure or cancellation conditional:** `failed` and `cancelled` require an `error` object and forbid `output`. Error requires `provider_error_code`, `error_class`, `message`, `occurred_at`, and `retry_class`. `error_class` enum: `provider`, `tool`, `context_validation`, `policy`, `storage`, `cancelled`. `retry_class` enum: `never`, `retryable`, `manual`. For a provider error, include optional provider request correlation hash, never a raw request/response, secret, or session handle.

**Cross-record semantic rules:** request identity values, context hash, worker/profile/provider/model/tool policy, and target revision must equal the request. `started_at <= finished_at`. A result cannot report success when context validation failed because invalid packages are rejected before dispatch and produce an Error Envelope or operator route rather than an LLM Run Result. A success result cannot create Artifact Record, Gate Run, Approval, Release, or completed Run status. Artifact creation and `submit_for_gate` remain subsequent controlled actions.

## Revision And Rerun Representation

Use conditional embedded `revision_context` inside Context Package instead of a sixth Stage A2 record. This is the minimum complete design because [revision-request.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/operator/revision-request.schema.json:1) already owns the durable revision instruction and findings.

For `trigger: revision`, `revision_context` is required and closed with:

```text
revision_request_id, rejected_artifact, machine_finding_refs,
human_finding_refs, operator_instruction, immutable_constraints,
forbidden_changes, expected_output_contract, expected_new_revision
```

- `rejected_artifact` must match the existing revision request current artifact ID, revision, and SHA-256 exactly.
- `machine_finding_refs` point to existing quality-gate-run findings. `human_finding_refs` point to existing revision request reviewer feedback or another typed review record when introduced later.
- `operator_instruction` is a byte-hashed controlled record or an exact revision-request field projection. It is not arbitrary chat context.
- `immutable_constraints` are copied from the revision request only as package snapshot evidence and must byte-match it. `forbidden_changes` is a non-empty explicit subset or explicit empty array accepted by policy.
- `expected_output_contract` must equal the main package output contract. `expected_new_revision` equals `target_revision` and is greater than rejected revision.

Do not create a duplicate Stage A2 revision request, release a revision from an LLM result, or make a rerun mutate the rejected artifact. The existing plan requires new artifact revisions and preserves old artifacts.

## Minimum Future Event And API Hooks

These are interface reservations only. They are not Stage A2 implementation scope and must not change the current V2 event catalog now.

| Later owner | Minimum hook | Required identity and boundary |
| --- | --- | --- |
| Local Operator API, Stage B | `GET /projects/{project_id}/logical-session`, `GET /projects/{project_id}/context-packages/{context_package_id}`, `GET /projects/{project_id}/llm-runs/{llm_run_request_id}` | Read-only views of stored records. Route tenant/project identity must match server registry. |
| Local Operator API, Stage B | `POST` typed dispatch command carrying only `llm_run_request_id` and request SHA-256 | API validates stored request and package before provider adapter. No direct raw context or arbitrary paths. |
| Event Store, Stage B | `llm.run_requested`, `llm.run_recorded`, `context.validation_failed` | Proposed future catalog additions. Each carries correlation/idempotency identity plus record ID and SHA-256, not context bodies or secrets. |
| n8n simulator, Stage C | Dispatch only stored valid request ID and hash; accept result ID and hash | n8n transports. It cannot build packages, set state, approve, release, or turn cache reuse into authority. |
| Notion simulator, Stage C | Project logical-session, context summary, and LLM run projection | Projection uses source event/revision and remains non-authoritative, as required by Stage A V2 contracts. |

The event additions should be considered in a single later catalog V3 proposal because [test_integration_contracts_v2.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_integration_contracts_v2.py:114) deliberately asserts exact catalog, payload, and fixture parity for Stage A V2.

## TDD Fixtures And Exact Tests

### Fixture layout

Create only during implementation:

```text
tests/fixtures/runtime/
  positive-logical-project-session.json
  positive-worker-profile.json
  positive-context-package-initial.json
  positive-context-package-next-step.json
  positive-context-package-revision.json
  positive-llm-run-request-fresh.json
  positive-llm-run-request-cache-hint.json
  positive-llm-run-result-success.json
  positive-llm-run-result-failure.json
  negative-*.json
```

All fixtures use synthetic tenant, project, run, artifact, evidence, prompt, worker, and provider IDs. They contain no AHD identifier, customer name, credential, live connection, provider response body, local absolute path, or client-specific field.

### Positive tests

1. `test_all_runtime_schemas_are_closed_draft_2020_12_and_have_unique_runtime_ids`: load all five schemas, assert draft URI, top-level and nested closed objects, and exact unique IDs under `/schema/runtime/`.
2. `test_logical_session_is_durable_and_declares_cache_only_recovery_policy`: validate session and assert it contains Project V2 binding but no provider/session handle, state status, approval, or release field.
3. `test_prompt_registry_binds_every_workflow_step_to_exact_official_prompt_and_output_contract`: parse all nine prompt metadata blocks, compare step/version/path/hash with the registry, require exactly one active entry per workflow graph step, including 3b.
4. `test_context_builder_produces_byte_identical_package_for_identical_ordered_sources`: build twice from the same controlled sources and assert equal canonical bytes, include order, and package SHA-256.
5. `test_next_step_context_requires_matching_released_predecessor_and_graph_edge`: fixture Step 1b from released Step 1 and assert exact release/artifact hash binding.
6. `test_revision_context_binds_rejected_artifact_findings_instruction_constraints_and_new_revision`: fixture validates only when all references match existing revision request and new revision is greater.
7. `test_untrusted_external_evidence_is_marked_and_ordered_as_data`: untrusted evidence validates with reason and appears after trusted contracts/instructions.
8. `test_request_reproduces_prompt_model_worker_tool_context_and_idempotency_provenance`: assert request values are exact projections of validated Context Package and Worker Profile.
9. `test_lost_technical_session_recovers_from_stored_context_package`: pass cache state `missing`, rebuild a fresh request from package, and assert its input/package hash equals the original valid package.
10. `test_cache_hint_cannot_change_validated_inputs`: cache-hint retry/resume fixture retains prompt, model, worker profile, tool policy, target revision, and package hash.
11. `test_success_result_records_candidate_output_and_exact_token_accounting_without_authority`: assert output reference and token arithmetic; assert no state, approval, release, or gate fields.
12. `test_failure_result_captures_structured_error_provenance_without_output`: assert no output on failure and retained request/context provenance.

### Negative tests

1. Missing Project V2, official prompt, output contract, worker profile, or package source returns a structured fail-fast context error before any dispatch adapter call.
2. Prompt path, prompt version, or SHA-256 mismatching the official registry is rejected.
3. Source hash mismatch after bytes change is rejected.
4. Source status `superseded` or `historical` in operational context is rejected. Rejected artifact outside revision mode is rejected.
5. Cross-tenant or cross-project source, logical session, request, or result is rejected.
6. Next-step predecessor with wrong workflow edge, missing release, artifact ID, revision, or hash is rejected.
7. Revision package missing rejected artifact, machine/human finding reference, operator instruction, immutable constraint match, output contract match, or increased target revision is rejected.
8. Untrusted source without `untrusted_reason`, or untrusted non-evidence source, is rejected.
9. Duplicate source identity, duplicate include order, non-contiguous ordering, free-form path, `..`, absolute path, URI, or outside-workspace storage key is rejected.
10. Disabled worker profile, disallowed model, direct provider tool operation, or forbidden state authority operation is rejected.
11. Initial, next-step, or revision request with cache reuse is rejected. Retry/resume cache hint without a matching provider/profile policy is rejected.
12. Same idempotency key with a changed package hash, target revision, model, tool policy, or dispatch policy is rejected.
13. Result request identity mismatch, non-monotonic timestamps, token arithmetic mismatch, success without output, failure with output, or output revision not equal to target revision is rejected.
14. Any request/package/result containing approval, release, gate decision, transition operation, run completion, raw provider session handle, secret, credential value, or arbitrary prompt body is rejected by closed schemas.
15. Error mapping coverage test proves every new `ERROR_CONTEXT_*` and `ERROR_LLM_REQUEST_*` code is present exactly once in `CANONICAL_RUNTIME_ERROR_CODES` and [error-routing-policy.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/operator/error-routing-policy.json:1), preserving `validate_policy` completeness.

The test module names from the approved plan remain `tests/test_context_builder.py` and `tests/contracts/test_llm_runtime_contracts.py`. Start with negative semantic tests before builder implementation. Existing [test_transition_service.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_transition_service.py:1), [test_operator_error_routing.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_operator_error_routing.py:1), and [test_integration_contracts_v2.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_integration_contracts_v2.py:1) are regression gates, not targets for contract duplication.

## Contradictions, Duplication Risks, And Overengineering To Avoid

1. Do not make `logical-project-session` a second Run Envelope. Run attempt/status/gate/revision are already owned by [run-envelope.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/run-envelope.schema.json:1) and Transition Service.
2. Do not embed full artifact, evidence, provider response, prompt, output-contract, or Project V2 bytes in a context package. IDs, controlled storage keys, revisions, and hashes provide reproducibility and prevent divergent copies.
3. Do not add approval, release, completion, gate pass, or workflow status fields to LLM request/result. This would contradict the prompt prohibitions and the Transition Service authority model.
4. Do not persist a raw technical session ID, conversation transcript, provider credential, endpoint, or provider response as authoritative state. The cache reference is hash-only and optional.
5. Do not add Stage A2 event types to V2 incidentally. Stage A tests enforce exact catalog parity and closed event payloads.
6. Do not create a generic document database, an LLM memory store, a second workflow graph, per-client prompt registries, or a policy expression language. None is needed to satisfy DEC-0019.
7. The approved plan names a `services/context_builder/session_policy.py`, while the minimal contract family needs only request-level `dispatch_policy` plus a repository-owned profile policy. Keep `session_policy.py` deterministic and small. It should evaluate existing stored identities, not manage sessions.
8. The existing evidence schema does not carry a trust label. Put `trust_level` in package source references only for Stage A2. Do not retrofit all Evidence Records unless a separate evidence-governance decision requires it.

## Recommended Architecture, Ownership, And Gates

### Recommended architecture

1. `services/context_builder/builder.py` obtains all records through a server-side repository adapter, selects the official prompt and output contract from the registry, orders `source_ref` values deterministically, calculates canonical package bytes/hash, and returns a candidate Context Package. It performs no provider call and no status mutation.
2. `services/context_builder/validator.py` validates JSON Schema first, then all cross-record rules above, and produces existing Error Envelope-compatible codes routed by `services.operator_routing.router.route_error`.
3. `services/context_builder/session_policy.py` decides only `fresh` versus allowed `cache_hint` after Context Package validation. Missing/expired cache changes an eligible cache hint to fresh recovery, never to a blocked loss of project context and never to unvalidated reuse.
4. A later Stage B API stores and exposes validated packages, requests, and results. It delegates canonical run changes to `process_transition` and error ownership to `route_error`.
5. A later Stage C n8n simulator transports request/result IDs and hashes. Notion projects summaries. Neither builds context or owns approval/release/state.

### File ownership

| Owner area | Files |
| --- | --- |
| Runtime contract owner | The five proposed files under `standards/runtime/` and the repository-owned prompt registry. |
| Context Builder owner | `services/context_builder/builder.py`, `validator.py`, `session_policy.py`. |
| Contract test owner | `tests/contracts/test_llm_runtime_contracts.py` and `tests/fixtures/runtime/`. |
| Behavioral test owner | `tests/test_context_builder.py`. |
| Shared authority owner | Existing Transition Service, Routing Service, workflow graph, output schemas, operator schemas, and integration contracts remain unchanged except additive routing codes/policy mappings required for fail-fast errors. |

### TDD sequence

1. Add schema-valid positive fixture and closed-schema tests for all five records and prompt registry validation.
2. Add failing semantic tests for source existence, status, tenant/project, byte hash, graph predecessor, revision bindings, and source ordering.
3. Implement pure builder canonicalization and validator lookup/semantic checks. Confirm byte-identical output.
4. Add worker/model/tool and fresh/cache policy tests, then implement the policy module.
5. Add request/result projection and error/token provenance tests, then implement their builders or validators without any provider adapter.
6. Add routing coverage for new error codes and run focused plus existing transition, routing, and integration suites.

### Review gates

1. Contract specification review: exact schema IDs, closed object boundaries, all conditionals, graph/prompt/output bindings, and no new authority.
2. Contract quality review: hash canonicalization, tenant containment, stale/superseded behavior, cache-loss recovery, secret avoidance, and negative-test adequacy.
3. Host and OMO focused contract/context-builder tests.
4. Existing full suite and `hermes verify --json` only after implementation and reviews. No Stage B work starts until Stage A2 approvals are recorded, as required by [CURRENT_POINT_OF_WORK](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-19-e2e-demo/sprint-4/CURRENT_POINT_OF_WORK.md:94).

## Explicit Exclusions

- No provider, LLM, crawl, Notion, n8n, deployment, browser, or network call.
- No API, event store, simulator, UI, OpenAPI, generated type, or database implementation.
- No direct state, gate, approval, release, artifact, or revision mutation by Context Builder, worker, request, or result.
- No new client-specific constants, AHD assumptions, credentials, live integration IDs, raw session handles, free-form paths, or persisted provider transcripts.
- No change to existing workflow graph, output schemas, prompts, Stage A V2 contracts, transition behavior, or Notion/n8n authority boundaries except future explicitly approved additive work.
