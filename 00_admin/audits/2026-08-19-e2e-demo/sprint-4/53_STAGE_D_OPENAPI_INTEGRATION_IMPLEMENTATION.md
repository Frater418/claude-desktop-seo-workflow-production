# Sprint 4 Stage D OpenAPI and Integration Implementation

Date: 2026-08-20
Author: Raphael Rechberger
Status: complete

## Scope

Stage D adds one standard-library generator, the deterministic FastAPI OpenAPI snapshot, generated TypeScript API types, and local integration/codegen tests. No Stage A2, B, C, schema, contract, workflow, UI, dependency, package, provider, network, socket, subprocess, deployment, customer workspace, or git-write behavior changed.

`scripts/generate_operator_api_contracts.py` obtains the document only through `create_app(WorkspaceRegistry(()), ROOT, AppConfig(ROOT, allow_unready=True)).openapi()`. The registry is empty and server-owned. Snapshot generation has no fixture registration, customer content, path, credential, or network input.

The generator emits both artifacts with one command:

```text
PYTHONDONTWRITEBYTECODE=1 python scripts/generate_operator_api_contracts.py
```

The snapshot is ASCII JSON with sorted keys, two-space indentation, and one trailing newline. `--check` rebuilds both values in memory and exits nonzero when either committed artifact differs. TypeScript is generated only from the snapshot and contains named component types, literal unions, readonly arrays, required and optional properties, refs, unions, and the `ApiOperationMap` method/path/request/response map. It contains no `any`, ignored diagnostics, or hand-authored endpoint statuses.

## TDD Evidence

RED ran before the generator existed:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api_codegen tests.test_sprint4_integration -v
Ran 2 tests in 0.000s
FAILED (errors=2)
ModuleNotFoundError: No module named 'scripts.generate_operator_api_contracts'
```

The error was the intended missing public generator module in both new suites.

GREEN after implementation:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api_codegen tests.test_sprint4_integration -v
Ran 6 tests in 43.573s
OK
```

The codegen tests compare the committed document to the exact FastAPI application document, require ASCII canonical serialization, assert every one of the 21 operation IDs occurs exactly once, verify the ten-command literal enum, verify real emitted response models, and exercise `--check`.

The one parameterized local integration suite runs project reads, n8n dispatch, task assignment, day-30 Step 3b checkpoint, and Notion projection for all ten neutral domain archetypes in temporary workspaces. Additional cases use real Stage B TestClient/EventStore/Repository plus Stage A2 and Stage C public APIs for idempotent replay, changed-key conflict, no mutation on failed transition input, lost-session recover-fresh, wait, bounded retry and DLQ provenance, day 30/60/90 acceptance, explicit day-120 rejection, and immutable Step 3b source behavior.

## Artifact Hashes

```text
b3aa1f968236cf63b54615b29bc4acaf59950abe377b54437f02f6fe6d504a8f  scripts/generate_operator_api_contracts.py
bc1d82a113730fb585112ad97dfed7f30bcc73e7016878f22f8fb8b998bb2ff4  standards/api/operator-api.openapi.json
3fb0c9111868badabbfc3462d92b7e41b9eb263d170e9ddfcd8237da2e4c7a76  apps/operator-console/src/generated/api-types.ts
e3800c7038758fb238e70d97460e52a160d617632f3c1bd62cc424da631c54d8  tests/test_operator_api_codegen.py
57693ac0bf15a9e97d69fc45ae0fcde76b09d615b1196d263df4a9a3be50ab50  tests/test_sprint4_integration.py
```

The generated TypeScript header records the OpenAPI input SHA-256 `bc1d82a113730fb585112ad97dfed7f30bcc73e7016878f22f8fb8b998bb2ff4` and `DO NOT EDIT`.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python scripts/generate_operator_api_contracts.py --check
Exit 0

tsc --noEmit --strict --noUncheckedIndexedAccess --exactOptionalPropertyTypes --verbatimModuleSyntax --noFallthroughCasesInSwitch --noPropertyAccessFromIndexSignature apps/operator-console/src/generated/api-types.ts
Exit 0

PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
Exit 0. Acceptance 7, root 247, contracts 59, total 313 tests.

docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py'
Exit 0. Acceptance 7, root 247, contracts 59, total 313 tests.
```

The manual surface gate is satisfied by the real in-process FastAPI TestClient in both the generator and integration suites. All generated and integration output is observed through temporary neutral workspaces or in-memory values. The controller completed the final cross-runtime verification after the delegated worker stopped. No internal Stage D task remains.

## Integration Coverage Correction

The Stage D integration suite was strengthened after controller inspection. It now has an explicit subtest matrix that drives the real local boundaries rather than relying on previous unit coverage:

- All ten neutral archetypes execute API project read, n8n dispatch, four-role Notion assignment source relations, and days 30, 60, and 90 checkpoints with correct tenant and project identities.
- The typed operator matrix executes the golden real `start` transition through `process_transition`, revision preview, missing-input blocker, workflow defect, escalation, waiver, exact replay, changed-key conflict, and a failed stale transition with no event or run mutation.
- The direct A2 matrix calls `build_context_package`, `validate_context_package`, and `build_llm_request` without using the Stage C request wrapper. It proves byte-identical rebuild, immutable input, revision preview, stale package rejection, cross-tenant rejection, Context Package and LLM policy traceability through the actual API projection response and n8n dispatch result, lost session recovery, gate wait, bounded retry and DLQ, immutable Step 3b, and day-120 rejection.
- Test-local guards reject outbound `socket.create_connection`, `urllib.request.urlopen`, `subprocess.run`, and `os.getenv` calls while allowing FastAPI TestClient's in-process event loop. All writes are beneath `TemporaryDirectory` roots.

Correction RED and GREEN evidence:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api_codegen tests.test_sprint4_integration -v
Initial strengthened run: Ran 15 tests in 33.179s, FAILED (11 failures, 1 error).
Cause: an over-broad socket guard intercepted TestClient's internal socketpair. The guard was narrowed to outbound socket creation.

PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api_codegen tests.test_sprint4_integration.Sprint4LocalIntegrationTests -v
GREEN: Ran 6 tests in 44.086s, OK.

PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
GREEN: acceptance 7, root 247, contracts 59, total 313 tests.

docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py'
GREEN: acceptance 7, root 247, contracts 59, total 313 tests.
```

The codegen suite additionally derives the actual FastAPI route-method-operation map from `APIRoute`, proves one unique emitted operation ID per route-method, confirms every emitted response status and component model appears in generated types, and temporarily drifts each committed artifact to prove `--check` exits nonzero before restoring the exact original bytes.

## Controller Final Verification

The stable workspace was verified after all Stage D writes completed:

```text
python scripts/generate_operator_api_contracts.py --check
Exit 0

python -m unittest tests.test_operator_api_codegen tests.test_sprint4_integration -v
Host Python 3.11.15: 6 tests, OK
OMO Python 3.12.3: 6 tests, OK

python tests/run_full_suite.py
Host Python 3.11.15: Acceptance 7, root 247, contracts 59, total 313, OK
OMO Python 3.12.3: Acceptance 7, root 247, contracts 59, total 313, OK

tsc --noEmit --strict ... apps/operator-console/src/generated/api-types.ts
OMO: Exit 0
Host: no global tsc executable on PATH

hermes verify --json
ok: true, Acceptance 7/7

git diff --check
Exit 0
```

## Limitations And Sprint 5 Readiness

- The Windows host runs Python 3.11.15 and passed the focused and full suites. OMO runs Python 3.12.3 and passed the same suites.
- The Windows host has Node.js but no global `tsc` executable. OMO provides `tsc` at `/home/coder/.config/opencode/node_modules/.bin/tsc`; its strict standalone `tsc --noEmit` command passed. No package was installed for Stage D.
- `tests/test_sprint4_integration.py` is in the 200 to 250 pure-LOC warning band because it is the mandated single explicit local scenario matrix. It owns only Stage D cross-boundary assertions and is not split to preserve that required evidence surface.
- FastAPI's current API models expose projection values through the existing `JsonValue` component. Stage D deliberately does not alter Stage B response models or invent richer UI contracts.
- The existing FastAPI TestClient Starlette HTTPX deprecation warning appeared during tests and did not affect outcomes.
- `hermes verify --json` was run by the controller and returned `ok: true` with 7/7 acceptance tests.

Sprint 5 may consume `apps/operator-console/src/generated/api-types.ts` directly. It should not create duplicate API contracts, change the generator, or hand-edit the generated file.
