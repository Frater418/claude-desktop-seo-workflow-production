# Sprint 3 Quality and Safety Review

**Review date:** 2026-08-19

**Scope:** Fresh read-only review of the current worktree, including changed and untracked Sprint 3 runtime contracts, schemas, renderers, provider integration, error routing, and tests. No prior audit was used as evidence.

## Verdict

`REQUEST_CHANGES`

## Evidence Executed

| Command | Result |
|---|---|
| `git status --short` | The worktree contains 41 modified tracked files and the new `services/`, `standards/outputs/`, runtime, workflow, and contract-test surfaces. |
| `git diff --stat` | 41 tracked files changed: 6,205 insertions and 5,882 deletions. |
| `git diff --check` | Failed with trailing-whitespace findings, including [`standards/manifest.schema.json:682`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/manifest.schema.json:682) and [`tests/acceptance-tests.md:1`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/acceptance-tests.md:1). |
| `python tests/run_full_suite.py` | Passed: acceptance 7, root discovery 143, contracts 37, total 187 tests. This reproduces the aggregate 187 claim locally, not a Windows execution. |
| `python -m unittest tests.test_step1_renderer ... tests.test_step4b_renderer -v` | Passed 8 renderer tests. The supplied 7/7 renderer claim is not the current count because [`tests/test_step1c_renderer.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_step1c_renderer.py:1) contains two tests. |
| `python --version` | Python 3.12.3. `python3.11 --version` was unavailable, so Python 3.11 execution was not verified. |
| In-memory malicious-render check | Step 4B accepted an injected `<script>` string and emitted it verbatim: `step4b_valid=True`, `raw_script_emitted=True`. |
| In-memory preflight checks | Empty Step 2 input returned `valid=True`; Step 3 input with `z` repeated 64 times for both hashes returned `valid=True`; invalid Step 4B canonical URL returned `valid=True`. |
| In-memory Step 4A render check | The rendered briefing failed the local JSON-LD validator: `valid=False`, `blocks_found=0`, `ERROR_SCHEMA_JSONLD_MISSING`. |

## Findings

### P0

No finding verified.

### P1

1. **Step 4B emits untrusted raw HTML into the page body.** [`render_step4b`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:44) inserts `page["html"]` without sanitization or an explicit trusted-HTML boundary. The closed schema permits every nonempty string for that field in [`step-4b-page-spec.schema.json`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4b-page-spec.schema.json:9). The in-memory check replaced the valid fixture's HTML with `<script>window.audit_marker=1</script>` and both preflight and renderer accepted it. This is a stored script-injection path for a rendered customer page.

2. **Step 4A labels JSON-LD metadata as JSON-LD while carrying no JSON-LD graph.** The Step 4A contract permits only `level` and `graph_hash` in its `jsonld` object, not a graph or source artifact reference in [`step-4a-briefing.schema.json`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4a-briefing.schema.json:17). The renderer serializes that metadata beneath a `## JSON-LD` heading in [`render.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/render.py:39). The validator correctly rejects a document with no extractable graph at [`validate_schema_jsonld.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/mcp/tools/validate_schema_jsonld.py:264). Rendering the positive Step 4A fixture then calling that validator produced `blocks_found=0` and `ERROR_SCHEMA_JSONLD_MISSING`. Thus the 4A derived view cannot carry the validated JSON-LD it claims to provide.

3. **Step 2 can approve an empty evidence submission.** [`validate_step2_preflight`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:18) converts a missing or non-list `approved_pillar_ids` to an empty list at lines 20-22 and returns valid when the resulting `missing` list is empty at lines 30-41. It neither validates the closed candidate schema nor binds submitted rows to its candidate object, although the actual output contract requires approved pillars and rows in [`step-2-keyword-evidence.schema.json`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-2-keyword-evidence.schema.json:6). The in-memory empty bundle returned `valid=True`, creating a false green before a gate transition.

4. **Step 3 accepts forged, non-SHA-256 lineage hashes.** [`validate_step3_preflight`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:35) validates only that two values are strings of length 64 at line 36. It does not require hexadecimal values, calculate either digest, validate a closed Step 3 candidate, or bind the values to Step 2 evidence. A structurally minimal 17-week bundle with both hashes set to `"z" * 64` returned `valid=True`. This permits a plan to pass the preflight without authentic artifact lineage.

### P2

1. **Step 4B schema format constraints are inactive, allowing invalid URLs through preflight.** [`step-4b-page-spec.schema.json`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4b-page-spec.schema.json:9) declares `canonical_url` and sibling links as URI formats. The validator constructs `Draft202012Validator(schema)` without `FormatChecker` in [`validator.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:13), unlike the explicit format-checking Step 1B validator in [`services/step1b_preflight/validator.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1b_preflight/validator.py:19). Replacing the positive fixture's canonical URL with `not-a-uri` returned `valid=True` and no errors.

2. **Rendered-output failures are not guaranteed to have an operator route.** The routing completeness test only inventories literal `ERR_` and `ERROR_` strings extracted from the `services` AST in [`test_operator_error_routing.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_operator_error_routing.py:29), then compares them with the manual canonical set at [`router.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/operator_routing/router.py:8). Step 4A renderer failure instead raises an unstructured `RendererError` at [`services/step4a_preflight/render.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/render.py:10) and [`services/step4a_preflight/render.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/render.py:16), with no routable error code. The passing completeness test therefore does not prove routing for this runtime failure mode.

3. **Step 4B always produces an English document language.** [`render_step4b`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:33) hardcodes `<html lang="en">`; the closed page specification has no locale field in [`step-4b-page-spec.schema.json`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4b-page-spec.schema.json:6). The renderer cannot preserve a deployment's validated language, which is a correctness and SEO regression for non-English customer workspaces.

### P3

1. **The submitted diff has unresolved whitespace defects.** `git diff --check` reports trailing whitespace across changed content, including [`standards/manifest.schema.json:682`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/manifest.schema.json:682) and [`tests/acceptance-tests.md:1`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/acceptance-tests.md:1). This does not change runtime behavior, but it obscures the already broad 41-file tracked diff and should be resolved before approval.

2. **Transition processing is an oversized maintenance unit.** [`services/transition_service/service.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:1) is 401 lines and owns locking, persistence, idempotency, transition state, approval evaluation, release construction, and CLI orchestration. This makes the safety-critical path harder to review and evolve independently. No behavior failure was reproduced from this structure.

## Verified Strengths

- Step 1 performs canonical-byte hashing, binds current and predecessor artifacts, validates typed runtime records, and verifies evidence references in [`services/step1_preflight/validator.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:205).
- Provider requests include location, location code, and language in both keyword and SERP payload builders in [`services/agentseo_gateway/core.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/agentseo_gateway/core.py:114) and [`services/agentseo_gateway/core.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/agentseo_gateway/core.py:144), and queue requests explicitly send `sync=false` in [`services/agentseo_gateway/core.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/agentseo_gateway/core.py:355).
- The provider routing, domain, runtime, and output contract suites passed in the reproduced 187-test run. The output-contract test also rejects AHD and client identifiers in output schemas at [`tests/contracts/test_output_contracts_v2.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_output_contracts_v2.py:62). The read-only source scan found AHD text only in tests and fixtures, not production `services`, `standards`, or prompts.

## Residual Risks and Limits

- Python 3.11 portability remains unverified because only Python 3.12.3 is installed in this review environment. The reviewed source uses Python 3.11-compatible syntax, but that is not execution evidence.
- No live provider request, crawl, deployment, or external Rich Results check was run, by review constraint. Provider behavior is verified only against local fixtures and unit tests.
- LSP diagnostics were unavailable because no configured language server is installed. Test execution and direct source review were used instead.
- The passing renderer tests establish deterministic output, but [`tests/test_step4a_renderer.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_step4a_renderer.py:14) checks the graph hash rather than JSON-LD validity, and [`tests/test_step4b_renderer.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_step4b_renderer.py:14) does not exercise hostile HTML or URL values.

REQUEST_CHANGES
