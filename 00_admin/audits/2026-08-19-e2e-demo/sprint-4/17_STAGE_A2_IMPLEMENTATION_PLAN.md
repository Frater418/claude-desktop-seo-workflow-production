# Sprint 4 Stage A2 Implementation Plan

Date: 2026-08-19
Author: Raphael Rechberger
Status: approved controller synthesis for execution
Branch: `feature/e2e-operator-workflow-system`

## Goal

Implement the `stateful project, replaceable worker` boundary before the Operator API. Every LLM execution must be reproducible from immutable files and records without relying on an old provider conversation. Technical sessions remain optional cache references only.

## Governing Decisions

- DEC-0018: local Core authority, n8n orchestration, Notion operative projection.
- DEC-0019: continuous logical project session, deterministic Context Packages, reproducible LLM Runs and replaceable technical workers.
- Transition Service remains the sole atomic workflow-state authority.
- Routing Service remains the canonical runtime-error owner.
- No Stage B API, Event Store, integration simulator or UI behavior is part of Stage A2.

## Controller Corrections To Research

### Step 0 Project Source

Step 0 creates the first canonical project/manifest output and therefore cannot require Project V2 as an input.

- Step 0 uses exactly one trusted `project_intake` source with immutable content hash.
- Steps 1 through 4b require exactly one released `project_v2` source.
- A logical project session starts with an intake binding and receives a new session-record revision after Project V2 release.
- A session revision supersedes the prior logical-session record. It does not overwrite project history.

### Multiple Output Contracts

The official prompt registry and Context Package use `output_contracts` as a non-empty unique ordered array.

- Step 0: manifest/project contract currently named by Prompt 0.
- Step 1: topic inventory.
- Step 1b: architecture.
- Step 1c: design system and template.
- Step 2: keyword evidence.
- Step 3: plan.
- Step 3b: adjustment.
- Step 4a: briefing and claim ledger.
- Step 4b: page spec and staging evidence.

No Stage A2 record may reduce a multi-output Step to one contract.

### Prompt Registry Contract

Create both:

- `standards/runtime/official-prompt-registry.schema.json`
- `standards/runtime/official-prompt-registry.json`

The registry is repository-owned configuration, validated like the workflow and quality registries. It binds all nine Step IDs to exact prompt path, prompt version, prompt SHA-256 and every output contract path/version/SHA-256.

## Package A2.1: Runtime Contracts And Official Registries

### Files

Create:

- `standards/runtime/logical-project-session.schema.json`
- `standards/runtime/official-prompt-registry.schema.json`
- `standards/runtime/official-prompt-registry.json`
- `standards/runtime/worker-profile.schema.json`
- `standards/runtime/context-package.schema.json`
- `standards/runtime/llm-run-request.schema.json`
- `standards/runtime/llm-run-result.schema.json`
- `tests/contracts/test_llm_runtime_contracts.py`
- `tests/fixtures/context_builder/*.json`
- Stage A2.1 implementation report

### Logical Project Session

Required:

- logical session ID and session revision
- tenant and project identity
- binding mode: `project_intake` or `project_v2`
- source ID, revision, controlled logical reference and SHA-256
- created timestamp and actor
- local Core authority constant
- technical session policy constants
- optional supersedes/superseded-by logical-session record IDs

Prohibited:

- provider credentials
- raw technical session handle
- run status authority
- approval, release or gate authority
- embedded chat transcript

### Worker Profile

Required:

- profile ID and version
- profile SHA-256
- provider capability reference without secret
- allowed model IDs and one default model
- allowed workflow steps
- tool-policy ID/version/hash
- unique allowed operations
- direct provider calls forbidden
- enabled flag

Forbidden operations include:

- approval
- release
- completion
- transition mutation
- arbitrary filesystem access
- deployment
- direct provider call

### Context Package

Required:

- package ID and schema version
- tenant/project/run/step identity
- logical-session ID and revision
- trigger and target artifact revision
- exact prompt binding
- project context binding
- worker-profile reference
- non-empty `output_contracts` array
- deterministic ordered source descriptors
- source-manifest SHA-256
- package SHA-256
- builder version and creation provenance

Source kinds:

- project_intake
- project_v2
- official_prompt
- output_contract
- released_predecessor
- rejected_artifact
- evidence
- decision
- quality_gate_run
- revision_request
- operator_instruction
- blocker
- resolution

Lifecycle states:

- active
- released
- rejected
- superseded
- historical

Trust levels:

- trusted
- operator_asserted
- untrusted
- not_applicable

Every source uses a controlled logical reference. Absolute Windows/POSIX paths, URI schemes and traversal are forbidden.

### LLM Run Request

Required:

- request identity, tenant/project/run/step and target revision
- correlation and idempotency identity
- run mode matching package trigger
- logical-session and Context Package identity/hash
- worker profile, provider, model and tool-policy identity/hash
- input SHA-256 equal to Context Package SHA-256
- exact output-contract array
- dispatch policy
- requested timestamp

Fresh execution is mandatory for:

- initial Step 0
- every next Step
- every substantial revision

Technical session cache hints are permitted only for exact retry/resume after Stage A2 semantic validation.

### LLM Run Result

Required:

- request and Context Package identity/hash
- worker/provider/model/tool-policy provenance
- target revision
- result status
- start and finish timestamps
- input and result SHA-256
- non-negative token usage with exact arithmetic
- optional technical-session observation without raw handle

Success requires candidate output references and forbids error. Failure/cancellation requires structured error and forbids output. Result never creates Artifact Record, Gate Run, Approval, Release or completed Run state.

### Contract TDD Gate

Tests must cover:

- closed Draft 2020-12 schemas and unique IDs
- all nine prompt entries and exact current bytes
- exact prompt metadata versions
- multi-output contract coverage
- Step 0 intake versus Step 1+ Project V2 conditions
- unknown fields and forbidden authority fields
- malformed IDs, hashes and logical references
- cache reuse forbidden for initial/next/revision
- success/failure result conditionals
- no AHD/client constants, credentials or raw session handles
- Python 3.11/3.12 compatibility

## Package A2.2: Deterministic Context Builder And Session Policy

### Files

Create:

- `services/context_builder/__init__.py`
- `services/context_builder/builder.py`
- `services/context_builder/validator.py`
- `services/context_builder/session_policy.py`
- `tests/test_context_builder.py`
- Stage A2.2 implementation report

Modify only when required:

- `services/operator_routing/router.py`
- `standards/operator/error-routing-policy.json`
- routing tests

### Pure Boundaries

The modules accept already loaded mappings and exact source bytes. They may not:

- read or write files
- inspect environment variables
- use system clocks without injected time
- open sockets
- call providers
- dispatch workers
- mutate repositories or workflow state

### Canonicalization

- JSON values only
- `ensure_ascii=True`
- `sort_keys=True`
- separators `(',', ':')`
- `allow_nan=False`
- UTF-8 bytes
- lowercase SHA-256
- caller order ignored
- deterministic source rank and tie-break sort
- contiguous include order assigned by builder

The package ID is caller-provided and immutable. Package SHA-256 excludes only `package_sha256`. Retry and resume reuse the same stored package ID/hash after revalidation rather than creating a nominally new package.

### Source Ordering

1. official prompt
2. output contracts ordered by registry
3. project intake or Project V2
4. released predecessor release/artifact pairs in workflow order
5. rejected artifact for revision only
6. revision request, findings and operator instruction for revision only
7. decisions, gates, blockers and resolutions
8. evidence ordered trusted, operator asserted, then untrusted
9. explicitly allowed historical comparison data

### Semantic Validation

Validate JSON Schema first, then:

- tenant/project/run/step identity
- logical-session binding and revision
- prompt registry path/version/hash
- every output contract path/version/hash
- exact source bytes and source hashes
- logical-reference grammar
- duplicate source identity/order
- lifecycle and supersession
- freshness using injected evaluation time
- workflow predecessor edge and Release Record
- revision request and rejected-artifact binding
- new target revision
- untrusted evidence labeling and permitted use
- package/source-manifest hash
- no input mutation

### Session Policy

Return one of:

- `fresh_required`
- `reuse_permitted`
- `recover_fresh`
- `denied`

Rules:

- initial, next-step and revision always fresh
- retry/resume may reuse only when every identity and hash matches
- missing, expired or lost technical session becomes recover-fresh when the stored package revalidates unchanged
- context drift denies retry/resume and requires a new package
- technical session identity never validates or changes package content

### Error Routing

Use a minimal canonical set:

- `ERROR_CONTEXT_SCHEMA_INVALID`
- `ERROR_CONTEXT_IDENTITY_MISMATCH`
- `ERROR_CONTEXT_SOURCE_INVALID`
- `ERROR_CONTEXT_PROMPT_BINDING_INVALID`
- `ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID`
- `ERROR_CONTEXT_PREDECESSOR_INVALID`
- `ERROR_CONTEXT_REVISION_BINDING_INVALID`
- `ERROR_CONTEXT_TRUST_POLICY_INVALID`
- `ERROR_CONTEXT_PACKAGE_HASH_MISMATCH`
- `ERROR_LLM_REQUEST_INVALID`
- `ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT`
- `ERROR_LLM_RESULT_INVALID`
- `ERROR_TECHNICAL_SESSION_POLICY_DENIED`

Each code must appear exactly once in canonical runtime inventory and routing policy. Do not add a second router.

### Behavioral TDD Gate

Negative tests first:

- missing Step 0 intake
- Project V2 missing after Step 0
- cross-tenant/project/run source
- unofficial prompt or wrong prompt bytes
- missing/mismatched output contract
- unreleased/wrong predecessor
- stale/superseded/historical required source
- rejected artifact outside revision
- revision binding mismatch
- untrusted evidence without label/reason
- arbitrary path or traversal reference
- duplicate source identity/order
- package/source hash mismatch
- changed input object
- cache mismatch on every bound field
- lost cache recovery with unchanged package
- lost cache plus source drift denial
- token arithmetic and result identity mismatch

Positive tests:

- Step 0 initial intake package
- Step 1 next-step package from released Step 0
- multi-output Step 1c package
- revision package
- deterministic shuffled-input parity
- exact retry
- exact resume
- lost-session recover-fresh
- Windows/OMO byte-identical canonical package

## Reviews And Completion

Sequence:

1. A2.1 implementer RED/GREEN
2. controller verification
3. A2.1 spec review
4. A2.1 quality review
5. A2.2 implementer RED/GREEN
6. controller verification
7. A2.2 spec review
8. A2.2 quality review
9. Windows full suite
10. OMO full suite
11. `hermes verify --json`
12. Stage A2 checkpoint
13. feature-branch commit and push

No Stage B work starts before Stage A2 terminal approval.

## Explicit Exclusions

- no provider or LLM call in Stage A2 implementation
- no raw provider session handle or transcript persistence
- no event catalog change
- no API or Event Store
- no Notion or n8n simulator
- no UI or generated TypeScript
- no workflow graph duplication
- no automatic approval, release, completion or deployment
- no AHD/client-specific production constants
- no commit or push to master
