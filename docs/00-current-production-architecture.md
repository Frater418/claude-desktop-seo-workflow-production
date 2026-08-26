# Current Heartweb production architecture

**Author:** Raphael Rechberger
**Status:** Current architecture authority
**Updated:** 2026-08-26

## 1. Purpose

Heartweb automates the strategic and technical preparation of SEO and GEO customer projects. It accepts verified client input and produces an implementation-ready strategy, architecture, roadmap, Copywriter briefing, Developer specification and Delivery package.

The system is not a final editorial writer, CMS, CRM or employee monitoring platform.

## 2. Product boundary

### Heartweb owns

- verified intake and Project V2
- workflow Steps 0 through 4B
- provider Evidence and deterministic tools
- artifacts, revisions and Quality Gates
- strategy and architecture outputs
- Copywriter and Developer handoffs
- deterministic Delivery packages
- later Step-3B performance comparison

### Notion owns after handoff

- human implementation tasks
- assignees and deadlines
- comments and coordination
- Copywriting, design and development execution
- operational review and launch

Post-handoff Notion tasks do not resume the Core or mutate artifacts.

### Human team owns

- final editorial copy
- brand judgment
- implementation in WordPress, Elementor or another CMS
- customer communication and commercial approval
- publication decisions

## 3. Runtime components

### 3.1 Domain contracts

Project V2 and related contracts separate Customer, Brand, Market, Search Deployment, Entity, Risk, physical location and Service Area. The framework remains client-neutral.

The accepted briefing creates one or more `market_deployments[]` before Step 0. Every active deployment binds its own market, country, language, locale, SEO operating model, target regions, physical-location and service-area references and one exact Provider Location Registry target. The registry target carries provider identity, target type, canonical location name, provider location code and verification Evidence. A market registry entry is not a substitute for this deployment-specific provider target.

Project V2 also binds the confirmed weekly planning capacity with minimum, maximum, source, operator identity and timestamp. If the input portfolio contains no explicit hours, intake returns a typed missing-input question instead of a default. For an already accepted project, the same value can be previewed and explicitly confirmed in the Operator Console. This creates a new Project V2 and Logical Project Session revision before Step 0 continues. Step 0 and Step 3 consume the same confirmed capacity record.

Multiple physical locations or service areas may belong to one deployment when they share the same provider research target. Distinct provider research targets require distinct deployments. The initial production sequence is bound to the one active primary deployment. Missing, ambiguous, unverified or operating-model-incompatible targets stop before Step 0. There is no country, language or provider-code default.

Step 0 produces Manifest V2 as an exact read-only projection of the run-bound deployment. A Project V2 or accepted-intake revision also creates a new hash-bound Logical Project Session and archives its predecessor so a rerun cannot consume stale intake bytes.

### 3.2 Workflow graph

The workflow graph defines legal step order and predecessor releases. Prompts do not control state.

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Step 3B is activated separately by a valid day-30, day-60 or day-90 performance checkpoint.

### 3.3 Transition Service

The Transition Service is the only canonical state writer. It validates:

- tenant, project and run identity
- current revision
- workflow predecessor
- artifact and content hash
- machine Quality Gates
- Human Approval
- release state

A failed transition leaves canonical state unchanged.

### 3.4 Context Builder and LLM runtime

Each run receives a versioned Context Package containing exact source paths, revisions and hashes. LLM Run Records bind prompt ID, prompt version, model, provider, tool policy, input hash, output hash and result metadata.

Provider sessions may be reused as a cache but are never Source of Truth.

The isolated Hermes profile `heartweb-runtime` is the agentic production runtime for Steps 0, 1, 1B, 1C, 2, 3, 4A and 4B. Every Step starts a specialized, versioned agent run with its own prompt, Worker Profile, model and reasoning policy, allowed tools, output contract and bounded agent and tool rounds. A Step agent may delegate focused research, processing, synthesis or review work to Hermes subagents when the Step contract permits it.

AI performs the generative and interpretive work. Deterministic code remains responsible for hashes, identity, schema validation, Evidence normalization, state transitions, approval authority, replay and Delivery packaging.

### 3.5 Prompt Registry

Every step uses a registered prompt version and expected output contracts. Old accepted runs remain reproducible because the exact prompt bytes and related versions remain identifiable.

### 3.6 Provider Gateway

The Provider Gateway normalizes external research and metric providers. Every request binds the run deployment, provider target ID, market, country, canonical provider location name, provider location code and language. The tool boundary verifies these values against `standards/domain/provider-location-registry.json` and the persisted Project V2 deployment before any provider call. Raw provider responses and hashes become Evidence.

Step agents may receive already validated provider Evidence or request an allowed provider operation through a typed Heartweb tool. The tool executes server-side through the Provider Gateway. Prompts and agents never receive provider credentials and never bypass this boundary with direct external provider calls.

Paid, externally acting or cost-unknown provider operations require the registered preview and explicit operator confirmation before execution. Missing capabilities, credentials, quota, exact deployment bindings, verified provider targets or confirmation stop the run without a fallback. Country-only lookup through the legacy `standards/location-codes.json` is not part of the production path.

### 3.7 Artifacts and revisions

Artifacts are immutable after release. Editing creates a child revision. A revision binds:

- Project, Run and Step
- parent revision
- content hash
- prompt and context identity
- relevant Evidence
- gate and approval state

### 3.8 Quality Gates

Machine gates enforce structural and measurable requirements. Human Gates approve strategic and customer-facing meaning. Neither can be inferred from prompt prose.

### 3.9 Operator API

The local API exposes typed commands and read models for the Admin Console. It preserves tenant and workspace containment, idempotency, replay and structured error behavior.

### 3.10 German Single-Admin Console

The Console is the production cockpit for one internal operator. It supports:

- project intake and selection
- workflow execution
- task and blocker handling
- artifact editing and revision comparison
- reviews and Human Gates
- release and recovery
- Delivery preview and download

Technical hashes, raw records and logs remain behind detail views.

### 3.11 Delivery Service

Delivery reads released Core records and creates derived packages. It cannot mutate Core state.

Delivery outputs include:

- checkpoint package
- final handoff package
- Copywriter package
- Developer package
- Project Management package
- manual Notion import project
- deterministic secure ZIP
- manifest and checksums

### 3.12 Diagnostic trace

The minimal diagnostic trace records automated and manual runs in one shared local format. It connects visible action, API request, Transition result, event, canonical readback, last success and first failure. It is Evidence only and never state authority.

## 4. Integration architecture

### 4.1 First local release

```text
Operator Console
-> Local Operator API
-> explicit production preview and confirmation
-> isolated Hermes heartweb-runtime
-> specialized Step agent and bounded subagents
-> typed Heartweb tools
-> Provider Gateway and Evidence
-> Core validation, Human Gate and workflow transition
-> Delivery Service
-> files, ZIP and manual Notion import
```

The local Hermes Gateway is a required production dependency but is never started automatically by the Console. Live Notion, n8n and a public server are not required for the first controlled output.

### 4.2 Future n8n orchestration

```text
UI trigger
-> n8n
-> typed Core command
-> provider and tool orchestration
-> Core validation and release
-> Delivery
-> Notion project creation
```

n8n owns transport, waiting, retry, notification and scheduling. It does not own workflow state.

### 4.3 Notion handoff

The approved Delivery creates one complete customer implementation project in Notion. Human execution remains there without Core callbacks.

### 4.4 Performance loop

```text
Day 30, 60 or 90
-> released strategy and plan
-> publication registry
-> verified GSC, Ahrefs and applicable local metrics
-> Step 3B
-> versioned adjustment proposal
-> explicit strategy approval
-> future plan and task update in Notion
```

Missing or stale metrics stop the checkpoint. The original plan is not overwritten.

## 5. Persistence and reproducibility

The system guarantees accepted artifact bytes, content hashes, source identities, revisions, approvals and releases. It does not guarantee that a fresh stochastic LLM rerun produces identical wording.

For exact reproduction, use the accepted stored artifact. A rerun produces a new revision.

## 6. Extensibility

The architecture supports:

- new prompt versions
- stronger output contracts
- new providers and tools
- optional customer archetype modules
- new Quality Gates
- additional workflow steps
- server deployment adapters
- semantic retrieval over the document registry

Every semantic extension must preserve versioning, fail-fast behavior, prior run readability and client neutrality.

## 7. Documentation and retrieval

The repository index is deterministic and contains lifecycle and authority metadata. A future semantic retriever must filter by this metadata before similarity ranking.

Read order:

1. `00_admin/ONBOARDING_REFERENCE.md` for the deterministic single-entry snapshot
2. `00_admin/SESSION_BOOTSTRAP.md`
3. `00_admin/PROJECT_STATE.md`
4. active and superseding entries in `00_admin/DECISIONS.md`
5. `00_admin/REPOSITORY_INDEX.md`
6. active plan and exact linked contracts

The generated Onboarding Reference is a navigational snapshot. Project State, active Decisions and the exact source contract remain authoritative when any embedded block is older than its source.

Historical and superseded files remain available but are excluded from default retrieval.

## 8. Current and planned capability

### Implemented in the current repository baseline

- V2 Core, workflow and transitions
- Context Packages and LLM records
- specialized Hermes Step agents, Worker Profiles and Tool Policies for Steps 0 through 4B
- persistent Production Executions with bounded continuation, retry and re-steering
- multi-location Search Deployment, Provider Target and planning-capacity bindings
- typed Heartweb tools, Provider Gateway operations and persisted Evidence
- artifacts, revisions, gates, approvals and releases
- Operator API and German Console
- browser-tested release-critical actions
- deterministic Delivery API, Delivery Center, role packages, manual Notion import and secure ZIPs
- shared local diagnostic trace
- locally restored PQ-0, PQ-1, PQ-2 and PQ-4 output quality

### Current acceptance evidence and limits

- The real CL pilot has a reviewed, approved, completed and released Step-0 Manifest V2 Revision 3.
- Step 1 Run `run-next-7f7e2b778f4521b9` is `in_progress` without Production Execution, Agent Evidence or LLM output.
- The complete real route through Step 4B, all Human Gates, final Delivery package and professional operator review are not yet proven.
- Repository consolidation under DEC-0031 does not change PT-03, PT-11, M10 or Production Acceptance status.

### Pre-release remaining

- produce Step 1 through the canonical Hermes and Provider Gateway route
- continue 1B, 1C, 2, 3, 4A and 4B with real required Evidence and fail-fast behavior
- perform every required Human Gate and revision decision
- generate, extract and inspect the final Delivery package
- complete the real-project Golden Path and explicit M10 acceptance

### Post-release

- live Notion and n8n
- complete Step 3B before the first day-30 checkpoint
- public deployment adapters
- broad archetype and international expansion
- additional mobile and presentation work

## 9. Non-goals

- no second state engine in Notion or n8n
- no automatic final Copywriter output
- no silent metric or claim estimation
- no AHD-specific shared product logic
- no requirement for a vector database
- no live deployment before explicit approval
