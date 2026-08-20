# Sprint 1 Quality Review B

- Author: Raphael Rechberger
- Audit date: 2026-08-19
- Scope: Current Sprint 1 candidate only. Read-only audit of transition, quality-gate, crawl-disposition and Step 1 preflight services, their runtime, quality and workflow contracts, the Step 1 inventory schema, and all current related tests.
- Method: Source and schema inspection plus the prescribed local non-network test commands. No provider, crawler, deployment, AHD runtime, external network, or write operation was invoked.

## Verdict

REQUEST_CHANGES

The Sprint 1 gate requires no open P0 or P1 findings. No P0 was verified, but two P1 findings remain. The prior missing transition-service and preflight-CLI findings are resolved in current source. The prior storage-binding finding is only partially addressed and remains P1 because the CLI accepts a copied file outside the declared storage location.

## Executed Verification

| Command | Outcome | What it verifies | Limitation |
|---|---|---|---|
| `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 -v` | PASS: 43 tests in 1.938s | Candidate unit and integration behavior for Tasks 1.1 through 1.4 | Does not test a real canonical storage root, a real crawl, CLI idempotency persistence, or output-root containment. |
| `python tests/run_full_suite.py` | PASS: acceptance 7 of 7 and 77 unittest tests in 2.103s | Current local regression suite | Tests are local fixtures and do not constitute a release, provider, crawl, AHD-lineage, or security-boundary verification. |

## Findings

### P1-01: Step 1 CLI accepts copied bytes instead of the artifact declared by `storage_key`

- Evidence: `services/step1_preflight/validator.py:510`
- Evidence: `services/step1_preflight/validator.py:518`
- Evidence: `services/step1_preflight/validator.py:535`
- Evidence: `tests/test_step1_contract_v2.py:419`
- Failure reasoning: `validate_step1_files()` checks only that the caller-supplied path has the same basename as `artifact.storage_key`. It does not resolve that storage key beneath a controlled artifact root, compare the resolved path with `inventory_path`, or reject an out-of-root path. A caller can copy valid canonical bytes to any file named like the declared artifact, supply that copy with the bundle, and receive a valid result. Replacing `bundle["inventory_bytes"]` with that copy before in-memory validation does not establish that the persisted artifact record names the examined file.
- Required fix: Derive the canonical path from `artifact.storage_key` and a configured controlled storage root. Reject absolute, traversing, escaping, or symlink-escaping storage keys. Require the supplied path to resolve exactly to that derived path, then hash and validate the bytes read there. Add positive and negative CLI tests for a same-name copied file, a storage-key path mismatch, traversal, and symlink escape.

### P1-02: Crawl runner permits unbounded local output paths and can pass them to an overwrite-capable external binary

- Evidence: `services/quality_gate_runner/screaming_frog.py:529`
- Evidence: `services/quality_gate_runner/screaming_frog.py:536`
- Evidence: `services/quality_gate_runner/screaming_frog.py:541`
- Evidence: `services/quality_gate_runner/screaming_frog.py:615`
- Failure reasoning: The CLI accepts an arbitrary `--output-folder`, converts it to an absolute path before the path check, creates it, and passes it to Screaming Frog. `--overwrite` is also caller-controlled. No configured root, tenant, project, run ID, containment check, or symlink check restricts where the runner and external crawler may write. An operator or compromised upstream command can direct crawler output to any process-writable location and request overwrite. This violates the stated tenant- and run-scoped output requirement and is a filesystem-integrity boundary failure.
- Required fix: Accept a controlled evidence root rather than an arbitrary output path. Derive the output directory from validated tenant, project, and run IDs, resolve it with strict containment and symlink checks, and never expose unrestricted overwrite through the operator CLI. Add tests proving rejection of relative, foreign-root, traversal, symlink, and non-run-scoped paths before any directory creation or subprocess invocation.

### P2-01: CLI idempotency is only an injected in-memory test condition, not a persisted service guarantee

- Evidence: `services/transition_service/service.py:174`
- Evidence: `services/transition_service/service.py:180`
- Evidence: `services/transition_service/service.py:349`
- Evidence: `tests/test_transition_service.py:196`
- Failure reasoning: `process_transition()` can detect a duplicate only when a caller provides an `idempotency_ledger`. The CLI reads an optional ledger from each request but writes only a result envelope, not an updated ledger or durable command record. Repeating an identical CLI request therefore has no process-spanning idempotency state. The passing test injects the first fingerprint into the second direct function call rather than exercising a persisted CLI replay.
- Required fix: Before any runtime consumer applies the emitted result, provide one authoritative durable command ledger with atomic compare-and-record semantics, or remove the claim that this CLI enforces idempotency and block it from operational use until the planned event store exists. Add two CLI-process tests: identical replay and same-key different-payload conflict.

### P2-02: The runnable crawl path cannot carry the policy-approved waiver inputs it evaluates elsewhere

- Evidence: `services/quality_gate_runner/screaming_frog.py:508`
- Evidence: `services/quality_gate_runner/screaming_frog.py:571`
- Evidence: `services/quality_gate_runner/disposition.py:87`
- Failure reasoning: `build_evidence()` supports revision-bound waivers, artifact binding, and an evaluation time, but `run_crawl()` exposes none of those parameters and calls it without them. Consequently a Step 1 resource 404 cannot take the policy-defined waiver route through the runnable crawler path. The policy is correctly strict by default, but the approved waiver workflow is split into manual evidence construction instead of one deterministic runner path.
- Required fix: Define the signed or persisted waiver input boundary for the crawl runner and pass the validated artifact, waivers, and evaluation time into `build_evidence()`. Add a runner-level test for a valid Step 1 resource waiver and tests rejecting expired, mismatched, and disallowed waivers.

## Prior Finding Status

| Prior risk | Current status | Current evidence |
|---|---|---|
| No central transition enforcement before approval or completion | Resolved in source, subject to P2-01 persistence limitation | `services/transition_service/service.py:257` validates the external approval before approval, and `services/transition_service/service.py:278` requires a current human gate run before completion. |
| Step 1 preflight CLI absent | Resolved | `services/step1_preflight/validator.py:542` defines the CLI and `services/step1_preflight/validator.py:557` returns nonzero for invalid validation. |
| Crawl findings could produce a false green | Resolved for implemented findings | `services/quality_gate_runner/screaming_frog.py:436` evaluates the disposition and `services/step1_preflight/validator.py:413` rejects a blocked disposition. |
| Registry policy not evaluated by preflight | Resolved | `services/step1_preflight/validator.py:436` invokes the registry evaluator and `services/quality_gate_registry/evaluator.py:144` rejects a missing bound gate run. |
| Stored artifact not actually bound | Still open as P1-01 | `services/step1_preflight/validator.py:510` compares only file names. |

## Positive Controls Verified

- Transition evaluation returns a deep-copied unchanged run when validation errors exist: `services/transition_service/service.py:292`.
- Approval validation binds tenant, run, gate, artifact hash, artifact revision, decision, and current time window: `services/transition_service/service.py:97`.
- Registry applicability requires a decision when a configured-source gate has no configured tool: `services/quality_gate_registry/evaluator.py:53`.
- Crawl disposition binds a valid waiver to policy version, artifact hash, step, finding class, and time window: `services/quality_gate_runner/disposition.py:25`.
- Crawl execution uses an argument vector rather than a shell command: `services/quality_gate_runner/screaming_frog.py:547`.
- The Step 1 schema rejects unknown fields and constrains canonical inventory identity and cluster quantities: `standards/outputs/step-1-topic-inventory.schema.json:6`.
- The preflight rejects noncanonical inventory bytes and verifies their SHA-256 against the artifact and transition: `services/step1_preflight/validator.py:115`.
- The crawler captures H2, link, redirect, structured-data, hreflang, and security findings for policy disposition: `services/quality_gate_runner/screaming_frog.py:309`.

## Test Gaps And Unverified Claims

- No test proves the preflight reads the true path declared by `storage_key`; the current positive CLI test intentionally uses a temporary copied inventory file: `tests/test_step1_contract_v2.py:419`.
- No test invokes `run_crawl()` with hostile paths, symlinks, or overwrite against a fake binary. Current command tests cover URL syntax and argument-list construction only: `tests/test_screaming_frog_quality_gate.py:48`.
- No test covers persisted idempotency across two CLI invocations. The only replay test supplies its ledger directly to the second function call: `tests/test_transition_service.py:196`.
- No test exercises a real Screaming Frog binary, actual crawl exports, provider, AHD runtime, release consumer, or external approval store. Assertions about those integrations remain unverified.
- Policy and registry JSON are exercised by fixture tests, but this audit did not verify a real AHD Crawl 005 lineage or waiver approval. Candidate classification still lists that gate as blocked: `00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md:35`.

## Final Gate Decision

REQUEST_CHANGES

Sprint 1 must not advance until P1-01 and P1-02 are fixed and regression-tested. Passing local tests are positive regression evidence only and do not override the demonstrated storage and filesystem-boundary failures.
