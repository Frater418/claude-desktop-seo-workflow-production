# Sprint 4 Stage A2 Context Builder Research

Date: 2026-08-20
Author: Raphael Rechberger
Status: implementation-ready research only
Scope: deterministic Context Builder, context validator, and technical session policy for Sprint 4 Stage A2. This report proposes no production change.

## Decision Boundary

Stage A2 is planned, not implemented. `DEC-0019` establishes the implemented architectural decision: a project is stateful and a technical worker is replaceable. It requires a versioned Context Package with exact sources, revisions, hashes, prompt identity, and recovery without a provider session. See `00_admin/DECISIONS.md`, `DEC-0019`.

The approved work lists the five new closed contracts and three Python modules in `00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md`, Stage A2. The authoritative task specification is `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`, Task 4.2. `CURRENT_POINT_OF_WORK.md`, Stage A2 confirms that none exist yet and requires fail-fast rejection before dispatch. Therefore all structures and error codes below marked **Proposed** are a Stage A2 design, not implemented facts.

## Implemented Facts To Preserve

| Area | Implemented fact and owner | Stage A2 consequence |
|---|---|---|
| Workflow authority | `services/transition_service/service.py:process_transition` validates run identity, expected revision, input hash, workflow edge, predecessor release, gates, approvals, retry bound, and creates release records. | Builder reads released records. It neither changes run status nor decides release, approval, retry count, or workflow edges. |
| Workflow topology | `standards/workflow/workflow-graph.json` defines initial route `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`; `3b` is only a repeatable post-publication sideflow. | Builder derives required predecessor only from this graph. It must reject an initial `3b` package. |
| Immutable records | `standards/runtime/run-envelope.schema.json`, `artifact-record.schema.json`, `release-record.schema.json`, `evidence-record.schema.json`, `quality-gate-run.schema.json`, and `approval-record.schema.json` are closed Draft 2020-12 runtime records. Artifact storage keys are tenant/project/run scoped. | References bind existing identities and content hashes. Builder does not replace these record schemas or invent mutable artifact storage. |
| Revision intent | `standards/operator/revision-request.schema.json` binds current artifact ID, hash, revision, immutable constraints, evidence, reviewer feedback, and bounded attempt number. | A revision package consumes this record plus separately typed findings and operator instruction. It does not reinterpret the request as an approval. |
| Error ownership | `services/operator_routing/router.py:route_error` maps the fixed runtime inventory to one route and owner. `standards/operator/error-routing-policy.json` is canonical. | New Stage A2 error codes require a deliberate inventory and routing-policy change in the implementation task. The builder must not emit ad hoc strings. |
| Controlled paths | `services/preflight_common/output_paths.py:resolve_step_output` derives the sole V2 output destination, rejects absolute paths, traversal, symlink/reparse escapes, and overwrite. | Context sources use logical references only. The pure builder never resolves filesystem paths. Later adapters may resolve a known storage key under a controlled root. |
| Prompt and output contracts | Official prompts are the nine files under `prompts/`: steps `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, and `4b`. Their current versions are `1.5.0` for step 0 and `2.0.0` for all others. Output contracts are owned by `standards/outputs/*.schema.json`; V2 controlled renderer outputs are owned by `services/preflight_common/output_paths.py`. | Package binds one official prompt and one applicable output contract by logical ID, version, repository-relative path, and SHA-256. It must never take a caller supplied prompt or output path. |
| Integrations | Stage A V2 contracts in `standards/integrations/` are closed; `tests/contracts/test_integration_contracts_v2.py` verifies simulated identities, non-authoritative Notion projections, bounded n8n retry/DLQ provenance, and ten client-neutral archetypes. | Stage A2 supplies validated package and run references to later adapters. It must not create events, projections, retries, DLQ entries, or live connections. |
| Existing test precedent | `tests/test_transition_service.py`, `tests/contracts/test_transition_contract.py`, `tests/test_operator_error_routing.py`, and `tests/contracts/test_operator_records.py` use stable error codes and identity/hash negative cases. | Stage A2 follows this style with pure in-memory fixtures and exact error-code assertions. |

`tests/contracts/test_integration_contracts_v2.py:test_contracts_contain_no_ahd_or_live_client_constants` is a direct client-neutrality precedent. AHD remains only a later golden-path fixture, never a Stage A2 contract constant.

### Contract Inventory Reviewed

The current workflow surface is `standards/workflow/workflow-graph.json` and `workflow-graph.schema.json`. Runtime inventory reviewed: `approval-record.schema.json`, `artifact-record.schema.json`, `claim-record.schema.json`, `error-envelope.schema.json`, `evidence-record.schema.json`, `quality-gate-run.schema.json`, `release-record.schema.json`, `run-envelope.schema.json`, `transition-command.schema.json`, and `waiver-record.schema.json` under `standards/runtime/`. Operator inventory reviewed: `blocker-record.schema.json`, `error-routing-policy.json`, `error-routing-policy.schema.json`, `escalation-record.schema.json`, `operator-task.schema.json`, `resolution-record.schema.json`, `revision-request.schema.json`, and `workflow-defect.schema.json` under `standards/operator/`.

Integration inventory reviewed: `event-catalog.json`, `event-catalog-v2.json`, `workflow-event.schema.json`, `workflow-event-v2.schema.json`, `notion-projection.schema.json`, `notion-projection-v2.schema.json`, `notion-proposal.schema.json`, `notion-record-v2.schema.json`, `notion-snapshot.schema.json`, `n8n-command.schema.json`, `n8n-simulation-state.schema.json`, `n8n-wait-subscription.schema.json`, `n8n-retry-entry.schema.json`, and `n8n-dlq-entry.schema.json` under `standards/integrations/`. Relevant existing service/test surfaces are `services/transition_service/service.py:process_transition`, `services/operator_routing/router.py:route_error`, `services/integration_contracts/notion_graph.py:validate_notion_graph`, `tests/test_transition_service.py`, `tests/contracts/test_transition_contract.py`, `tests/test_operator_error_routing.py`, `tests/contracts/test_operator_records.py`, `tests/contracts/test_integration_contracts.py`, `tests/contracts/test_integration_contracts_v2.py`, and `tests/test_notion_graph_validator.py`.

## Proposed Contract Model

All five schemas are closed Draft 2020-12 objects, use stable `$id` values under `https://heartweb.example/schema/runtime/`, use lowercase hexadecimal SHA-256 fields, and reject unknown fields. They use the existing tenant, project, run, artifact, and step ID patterns where applicable.

### 1. Logical Project Session

`logical-project-session.schema.json` is a read model, not a provider session. Required fields:

- `logical_session_id`, `tenant_id`, `project_id`, `project_v2_ref`, `project_v2_sha256`, `current_run_id`, `current_step_id`, `current_revision`, `status`, `created_at`, `updated_at`.
- `project_v2_ref` is `storage:project-v2/<project_id>/<revision>` or a similarly closed logical-reference grammar, never an OS path or URL supplied by a caller.
- `technical_sessions` is an optional history of opaque cache handles with provider, model, worker-profile ID, package ID/hash, status, and expiration. It is informational only and cannot make a package valid.

The session carries no authoritative workflow status beyond the referenced run. Transition Service remains authoritative.

### 2. Worker Profile And LLM Run Contracts

`worker-profile.schema.json` requires `worker_profile_id`, profile version, provider, allowed model IDs, model policy, tool-policy ID/version, allowed operations, and profile SHA-256. It contains no secret, token, endpoint, customer name, or session handle.

`llm-run-request.schema.json` requires tenant/project/run/step identity, target revision, `run_mode`, worker profile ID/hash, selected provider/model, tool policy ID/hash, Context Package ID/hash, input hash, trigger, and a session-policy decision. Allowed `run_mode` values are `initial_step`, `next_step`, `revision`, `retry`, and `resume`. It has no field granting approval, release, completion, or direct state mutation.

`llm-run-result.schema.json` requires request ID/hash, result status, started/finished timestamps, input/output/result hashes, optional candidate artifact ID/hash, token usage, provider/model/worker/profile provenance, optional technical-session observation, and either a structured error or success metadata. A candidate artifact is not released by this contract.

### 3. Context Package

`context-package.schema.json` requires:

- Package identity: `context_package_id`, schema version, tenant/project/run/step IDs, trigger, target artifact revision, run mode, builder version, requested budget tier, created-at, and `package_sha256`.
- Binding: one `prompt` object and one `expected_output_contract` object, each with controlled logical reference, ID, version, and SHA-256. Prompt path is repository-relative and must be one of the nine official prompt paths. Output contract path is repository-relative under `standards/outputs/`.
- Project baseline: exactly one `project_v2` source reference and hash.
- Ordered `sources`: typed immutable descriptors, not embedded arbitrary files. Every descriptor has `source_kind`, `logical_ref`, `record_id`, tenant/project identity, revision where relevant, `content_sha256`, lifecycle state, trust label, inclusion reason, and sequence number.
- `source_manifest_sha256`: hash of the ordered sources alone, allowing a reviewer to distinguish source-set drift from package metadata drift.
- `budget`: requested tier, deterministic byte limit, selected byte count, and omitted optional-source descriptors. Required content cannot be silently omitted.

`logical_ref` is an opaque identifier from a closed grammar, such as `runtime:artifact/<artifact_id>`, `runtime:evidence/<evidence_id>`, `runtime:release/<release_id>`, `operator:revision/<revision_request_id>`, `prompt:<step_id>`, and `output-contract:<step_id>`. It cannot contain `/..`, a drive prefix, an absolute POSIX path, a URI scheme, or a raw workspace path. A filesystem adapter may map it only after validation and only beneath its tenant-controlled root.

### 4. Source States, Trust, And Ordering

**Proposed lifecycle states** are `active`, `released`, `rejected`, `superseded`, and `historical`. `released` is required for predecessors. `active` is permitted for current Project V2, decisions, current gate state, and current evidence within freshness. `rejected` is permitted only as the revision target. `superseded` and `historical` are excluded unless an explicit revision rule lists them, in which case they are visible as non-current comparison material and cannot satisfy a required source.

**Proposed trust labels** are `trusted`, `untrusted`, and `operator_asserted`. `trusted` is for released internal artifacts and validated internal records. `operator_asserted` is for a typed instruction or decision, never evidence of an external claim. Crawl, SERP, competitor, provider response, and arbitrary web material default to `untrusted`. They are includable only with that explicit label, source hash, retrieval time, permitted-use value, and an internal evidence record. They cannot become trusted merely because they appear in a prompt. A missing label fails validation.

**Proposed canonical source order** is a fixed `(rank, source_kind, logical_ref, record_id, revision, content_sha256)` sort, with ranks:

1. official prompt
2. expected output contract
3. Project V2
4. released predecessor release and artifact pairs, ordered by workflow path
5. current rejected artifact for revision only
6. revision request, machine findings, human findings, and operator instruction for revision only
7. current decisions and gate records
8. allowed evidence, ordered trusted before operator-asserted before untrusted
9. explicit historical comparison sources, if an approved revision rule requires them

The builder assigns contiguous sequence numbers after this sort. It must not preserve caller order, timestamp order, dictionary insertion order, or filesystem enumeration order.

### 5. Canonical Serialization And Hashing

**Proposed algorithm:** construct only JSON values from the validated immutable input snapshot. Reject non-finite numbers, bytes, sets, datetime objects, and floats where a string/integer contract is required. Serialize with Python `json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)`, UTF-8 encode the ASCII result, and calculate `hashlib.sha256(...).hexdigest()`. This matches the existing deterministic fingerprint convention in `services/transition_service/service.py:_fingerprint`.

`source_manifest_sha256` hashes the canonical `sources` array. `package_sha256` hashes the canonical package object with `package_sha256` omitted. Package ID derives deterministically from the first 16 hex characters of `package_sha256`, for example `context-<16hex>`, only after the complete package has been built. If the existing ID regex requires a longer suffix, the schema should use the existing established runtime identifier grammar rather than weakening it. Rebuilding from identical input values must produce byte-identical canonical JSON and the same hashes on Windows and Linux.

### 6. Freshness, Supersession, And Revision Rules

Freshness is input-policy based, not inferred from a provider session. Each source has `valid_from`; externally retrieved evidence additionally has `retrieved_at` and optional `valid_until`, consistent with `evidence-record.schema.json`. The validator receives `evaluation_at` explicitly. A source is stale if `valid_until <= evaluation_at`, if its current record version/hash differs from the descriptor, if a newer release supersedes a required predecessor, or if a revision package points to a non-current rejected artifact.

An initial or next-step package requires exactly the graph-required released predecessor and its matching release record, artifact revision, and hash. Step 0 has no predecessor. A revision package requires all of the following:

- the official prompt and expected output contract for the same step;
- the current rejected artifact with ID/hash/revision matching `revision-request.schema.json`;
- the released predecessor set that supplied the rejected artifact's valid baseline;
- the open, non-superseded revision request;
- typed machine findings from relevant quality-gate runs and typed human findings from the review record;
- a non-empty structured operator revision instruction;
- immutable fields, forbidden changes, expected new revision `current_revision + 1`, and allowed evidence.

The builder never overwrites the rejected artifact and never labels a rerun as a retry. A revision creates a new target artifact revision. A retry repeats the same validated request/package and does not change sources, target revision, prompt, or output contract. Resume re-dispatches an already validated request after an interruption and does not rebuild context. If current records have changed, retry/resume is rejected and a new revision or new step package is required.

### 7. Deterministic Budget Tiers

Budget is an explicit caller-selected enum, not a model-dependent token estimate: `compact` 32 KiB, `standard` 128 KiB, and `extended` 384 KiB of canonical selected-source payload bytes. The package always contains all descriptors and hashes. The selected payload is chosen in canonical source order within the tier:

- Mandatory sources through rank 7 must fit. Otherwise return `ERROR_CONTEXT_BUDGET_REQUIRED_EXCEEDED`; do not truncate a required record.
- Rank 8 and 9 sources are included while the next complete source fits. Remaining optional descriptors appear in `omitted_sources` with reason `budget_exceeded` and remain auditable.
- A revision may not omit rejected artifact, findings, instruction, immutable constraints, prompt, Project V2, output contract, or released predecessors. If these exceed the tier, caller must select a larger permitted tier or repair the inputs.

The package records byte counts, not provider-token estimates. The dispatch adapter may calculate provider tokens later, but that calculation cannot alter package membership or hash.

## Pure Module Boundaries

Create `services/context_builder/` with no imports of `Path`, environment variables, clocks, network clients, mutable repositories, or provider SDKs.

| Module | Pure public boundary | Exclusions |
|---|---|---|
| `builder.py` | `build_context_package(snapshot, policy, evaluation_at) -> ContextPackage` accepts already-loaded dicts/dataclasses, normalizes, sorts, applies budget, and returns canonical package plus hash. | No reads, writes, dispatch, status mutation, path resolution, or prompt downloading. |
| `validator.py` | `validate_context(snapshot, package, policy, evaluation_at) -> ValidationResult` and `assert_context_valid(...)` perform schema, identity, lifecycle, freshness, lineage, hash, prompt/output, trust, and revision checks. | No JSON Schema file loading from disk in the pure core. A thin test/adapter layer supplies compiled schemas and records. |
| `session_policy.py` | `decide_session(request, validated_package, logical_session, cache_record, now) -> SessionDecision` determines fresh/reuse/recover only. | No provider session creation, storage, retry loop, or state update. |

Use frozen dataclasses or plain immutable-by-convention mappings internally. Return a structured result with ordered errors: `code`, JSON-pointer-like `path`, `message`, `remediation`. The calling adapter owns schema loading, controlled logical-reference resolution, artifact byte loading, persistence, `route_error`, and dispatch. This design is executable without filesystem, network, or state side effects and therefore runs identically on Windows and Linux.

## Fail-Fast Error Contract

**Proposed Stage A2 codes:** `ERROR_CONTEXT_SCHEMA_INVALID`, `ERROR_CONTEXT_IDENTITY_MISMATCH`, `ERROR_CONTEXT_PROJECT_V2_MISSING`, `ERROR_CONTEXT_PROMPT_UNOFFICIAL`, `ERROR_CONTEXT_PROMPT_HASH_MISMATCH`, `ERROR_CONTEXT_OUTPUT_CONTRACT_MISMATCH`, `ERROR_CONTEXT_LOGICAL_REF_INVALID`, `ERROR_CONTEXT_PREDECESSOR_MISSING`, `ERROR_CONTEXT_PREDECESSOR_UNRELEASED`, `ERROR_CONTEXT_SOURCE_HASH_MISMATCH`, `ERROR_CONTEXT_SOURCE_STALE`, `ERROR_CONTEXT_SOURCE_SUPERSEDED`, `ERROR_CONTEXT_SOURCE_STATE_INVALID`, `ERROR_CONTEXT_UNTRUSTED_UNMARKED`, `ERROR_CONTEXT_TRUST_POLICY_DENIED`, `ERROR_CONTEXT_REVISION_INVALID`, `ERROR_CONTEXT_BUDGET_REQUIRED_EXCEEDED`, `ERROR_CONTEXT_PACKAGE_HASH_MISMATCH`, and `ERROR_TECHNICAL_SESSION_POLICY_DENIED`.

Every failure occurs before a LLM request is built. It includes the exact logical reference or field path and a remediation, but never leaks physical paths, credentials, or source payload. Implementation must add every code to the canonical runtime inventory and map it through `services/operator_routing/router.py:route_error`; otherwise it fails its own routing validation. Cross-tenant or project/run mismatch must be classified as the existing isolation/abort path rather than downgraded to a retry.

## Technical Session Policy

The default decision is `fresh_required` for every initial step, next step, and substantial revision, per `DEC-0019` and the Sprint 4 build plan. A technical session is an opaque provider cache observation, never a Context Package source, identity authority, or condition for recovery.

Fresh session is mandatory when: no cache is supplied; run mode is `initial_step`, `next_step`, or `revision`; prompt/version/hash, worker profile/hash, provider/model, tool policy/hash, package hash, tenant/project/run, or target revision differs; cache is expired/lost/unknown; the prior result failed after provider-side mutation; a security/isolation condition exists; or policy requires a new model context.

Reuse is permitted only for a `retry` or `resume` when all of these exact values match: tenant/project/run, step, target revision, Context Package ID/hash, prompt hash, worker profile hash, provider/model, tool-policy hash, allowed operations, and cache expiration is strictly after `now`. The policy result records `reuse_permitted`, reason, cache reference, and all compared hashes. Reuse does not skip `validate_context`.

Lost-session recovery is `recover_fresh`: retain the logical project session and all immutable files/records, rebuild or revalidate the package from the same snapshot, compare its hash to the stored request hash, then create a fresh technical session. A mismatch is not recoverable as resume and must fail for source drift. No chat transcript is needed or trusted.

Retry, resume, and revision remain distinct:

- Retry: bounded transport/provider retry of the same request and same package. It may reuse only an exact cache.
- Resume: continuation after orchestration interruption using the same stored request/package after full revalidation. A lost handle becomes recover-fresh, not a failed project.
- Revision: semantic correction after rejection or changed approved inputs. It creates a new package, new request, new target revision, and fresh technical session by default.

## Package Walkthroughs With Client-Neutral Fixtures

### First-Step Package

Fixture names should be neutral, for example `tests/fixtures/context_builder/positive-initial-step.json`. The fixture contains `tenant-demo`, `project-demo`, a released Step 0 Project V2 artifact and release record, an in-progress Step 1 run, official `prompts/1-pillar-identifikation.xml.md` at version `2.0.0`, its SHA-256, and `standards/outputs/step-1-topic-inventory.schema.json` with its SHA-256. It includes an active Project V2 descriptor and the graph-required released Step 0 predecessor pair. Optional competitor material is an evidence descriptor explicitly labelled `untrusted` with retrieval time and hash.

`validate_context` confirms same tenant/project, graph edge `0 -> 1`, matching predecessor release/artifact hash, one official Step 1 prompt, and output-contract applicability. `build_context_package` sorts prompt, output contract, Project V2, predecessor release/artifact, then optional evidence; it assigns sequences, applies the requested `standard` budget, and calculates source and package hashes. `decide_session` returns `fresh_required` because this is `initial_step`. The resulting LLM request binds only package ID/hash, worker profile, model/tool policy, and input hash. It cannot complete Step 1.

### Revision Package

Fixture `tests/fixtures/context_builder/positive-revision-step.json` contains a rejected current Step 4a artifact at revision 2, its matching open `revision-request` record, released Step 3 predecessor, current Project V2, official `prompts/4a-content-briefing-und-schema.xml.md`, Step 4a briefing output contract, current quality-gate machine findings, human review findings, typed operator instruction, immutable constraints, forbidden changes, and permitted evidence. All descriptors share one tenant/project/run scope.

The validator requires the rejected artifact ID/hash/revision to equal the revision request, excludes superseded evidence, sets target revision 3, and verifies every revision-required component is present before selection. The builder records rank 5 rejected artifact then rank 6 revision material, with untrusted SERP material explicitly labelled and constrained. Session policy returns `fresh_required`. A later failed provider attempt may retry revision 3 only with the unchanged revision package; a new human finding requires a new revision package, not resume.

## TDD Sequence And Exact Tests

1. Add failing contract tests in `tests/contracts/test_llm_runtime_contracts.py`: each new schema is closed Draft 2020-12, has unique stable runtime `$id`, validates positive logical session/profile/package/request/result fixtures, rejects unknown fields, malformed IDs/hashes, arbitrary paths, non-official prompt references, mismatched prompt/output hashes, and forbidden authority fields.
2. Add failing pure behavior tests in `tests/test_context_builder.py`: rebuild from shuffled input mappings/lists and assert byte-identical canonical JSON, source sequence, source-manifest hash, package hash, and derived ID.
3. Add positive fixtures: initial step, next step, revision, retry exact cache reuse, resume exact cache reuse, and lost-session recover-fresh. Include all ten client-neutral archetypes through a parameterized identity-only matrix rather than embedding customer names.
4. Add negative fixtures: missing Project V2; predecessor missing, unreleased, stale, superseded, wrong revision, or wrong hash; tenant/project/run mismatch; stale evidence; untrusted crawl/SERP/competitor source without a label; untrusted source denied by policy; arbitrary POSIX, Windows, URI, traversal, and reparse-like logical references; wrong prompt step/version/hash; wrong output contract; revision missing rejected artifact/findings/instruction/immutable constraints; required-source budget overflow; package hash mismatch; cache mismatch on every reuse-bound field; expired and lost cache.
5. Implement schema validation and exact ordered structured errors first, then `validator.py`, then canonical builder/hash, then session policy. Assert no input object is mutated and no filesystem/network/state function is called. Use monkeypatch guards for `open`, `Path`, sockets, time, and environment access in the pure-module tests.
6. Add Windows/Linux parity test using the same in-memory fixture and expected canonical JSON/hash. It must not use a temporary directory. Run focused tests, `tests/run_full_suite.py`, and the approved Stage A Host/OMO verification gates.

## Recommended Architecture And Ownership

Adopt the five schemas and three pure modules named in the build plan. Add only `tests/test_context_builder.py`, `tests/contracts/test_llm_runtime_contracts.py`, and client-neutral JSON fixtures under `tests/fixtures/context_builder/`. The Stage A2 adapter boundary may load records later, but Stage A2 itself owns package construction, validation, canonicalization, and technical-session decisions only.

Transition Service retains state, release, approval, predecessor-transition, and retry-attempt authority. Routing Service retains code-to-owner routing. Quality Gate Registry and runner retain findings and gate outcomes. Output contracts and controlled output paths retain artifact shape and destination authority. Integration contracts retain event/projection/simulation transport. Stage B owns persistence, APIs, event append, and dispatch. Stage C owns n8n/Notion transport. Sprint 5 owns display and operator interaction.

Review gates are: contract/spec review after RED/GREEN; quality review that attempts reordered-input, cross-tenant, stale/superseded, arbitrary-reference, untrusted-source, budget, and cache-bypass false greens; Windows and OMO parity; full suite; then a scope diff proving no Stage B/C/UI behavior was introduced. The implementation should follow the mandatory task cycle in `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`, Section 7.

## Contradictions, Risks, And Explicit Exclusions

- The build plan calls the Project V2 reference "exact" but no Project V2 runtime schema or logical-reference grammar exists yet. Stage A2 should add a descriptor to its package schema, not create a second Project V2 domain schema. The existing domain validator remains owner of Project V2 validity.
- Existing `evidence-record.schema.json` has source type and hashes but no trust/lifecycle label. Duplicating the entire evidence schema inside Context Package would create two truth sources. Stage A2 should carry contextual trust/lifecycle descriptors and reference the existing evidence record.
- `revision-request.schema.json` has reviewer feedback and evidence but no standalone machine/human finding contract or typed operator-instruction contract. Stage A2 needs small closed descriptor definitions in its own package schema unless a later approved shared record contract is introduced. Do not make free-text comments authoritative.
- Do not add prompt-content parsing, tokenization, provider SDKs, filesystem resolution, cache storage, database schema, API endpoint, event, Notion/n8n behavior, automatic approval/release, live crawling, or client-specific defaults. Those would duplicate owners or start later stages.
- Do not overengineer a general DAG resolver or a session transcript store. The existing workflow graph and immutable files provide the required lineage and recovery boundary.
