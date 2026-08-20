# Sprint 3 Final Specification Approval Review A

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Fresh read-only review of Sprint 3 Tasks 3.1 through 3.10 and the P1/P2 items from reports 15 and 16. Reports 15, 16, and 17 were used only to locate scope. Findings below are based on current repository artifacts and locally executed read-only checks.

## Final Verdict

REQUEST_CHANGES

The Step 2 public preflight accepts tampered raw provider content while retaining an arbitrary declared raw-response hash. This fails the required every-row provider-evidence binding and blocks Tasks 3.4, 3.5, and consequently 3.10. The claimed clean `git diff --check` result was also not reproducible in the current workspace.

## Findings

### P0

No P0 findings verified.

### P1

1. Step 2 does not cryptographically bind `raw_response_sha256` to the actual `raw_response` payload. The gateway verifies only that the field is non-empty, then returns its asserted value without computing a digest. [services/provider_gateway/core.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/provider_gateway/core.py:46) [services/provider_gateway/core.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/provider_gateway/core.py:67) Step 2 then compares the row to that asserted response field, rather than a computed raw-content hash. [services/step2_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:104) [services/step2_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:108) The typed response contract likewise only constrains the field shape. [standards/providers/research-response.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/providers/research-response.schema.json:7) [standards/providers/research-response.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/providers/research-response.schema.json:10)

   Reproduction: I constructed the repository's complete non-AHD Step 2 public-preflight bundle, changed only the first completed response from its fixture payload to `{"keyword":"tampered evidence"}`, and retained its declared `raw_response_sha256` of 64 `a` characters. `validate_step2_preflight` returned `{'valid': True, 'errors': []}`. Therefore a row can be declared, unique, typed, completed, and metadata-matched while its claimed raw evidence is not bound to the raw bytes. The required exact provider/raw-hash evidence boundary is not resolved.

   Recommendation: compute the canonical raw-response digest at the provider boundary, reject mismatches before returning exchange evidence, and cover it with a complete public-preflight regression.

### P2

1. The controller claim that `git diff --check` exits 0 is not reproducible in the current workspace. The command reports trailing whitespace in tracked files, including [standards/manifest.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/manifest.schema.json:116) and [tests/fixtures/sample_manifest.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/fixtures/sample_manifest.json:135). The report-15 specifically cited whitespace items were repaired, but the current tracked diff still fails the required integrity command. This is an unresolved final quality condition, not a source-code behavior finding.

### P3

No P3 findings verified.

## Task Resolution Matrix

| Task | Result | Independently verified current evidence |
| --- | --- | --- |
| 3.1 Step 1B architecture | Pass | Closed candidate schema, common released-predecessor validation, deterministic views, and focused contract coverage are present. |
| 3.2 Step 1C design | Pass | Closed design/template contracts, location safety, lineage checks, and controlled rendering are present. |
| 3.3 Step 1C templates | Pass | The renderer produces per-template views and controlled destinations use `v2/outputs/step1c/templates/{identifier}.v1.html`. [services/preflight_common/output_paths.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:12) |
| 3.4 Provider contracts | Request changes | Typed request/response schemas and completed-status checks exist, but P1 permits an asserted raw hash that does not identify the supplied raw response. |
| 3.5 Step 2 evidence | Request changes | Declared, distinct row evidence and exact one-record coverage are enforced. [services/step2_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:47) [services/step2_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:79) P1 leaves the required raw-evidence binding incomplete. |
| 3.6 Step 3 plan | Pass | The candidate validator applies the closed schema and awaiting-gate status. The public preflight verifies exact canonical released Step 2 bytes and the sorted deterministic solver projection. [services/step3_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:54) [services/step3_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:105) |
| 3.7 Step 4A briefing | Pass | Canonical graph hashing, local graph validation, and exactly one claim binding per ledger claim to an existing graph node are enforced. [services/step4a_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:40) [services/step4a_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:55) |
| 3.8 Step 4B page | Pass | Every case-insensitive `data:` URL is rejected, actual JSON-LD graph is locally validated and rendered, and page plus staging hashes derive from the canonical page payload. [services/step4b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:23) [services/step4b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:44) [services/step4b_preflight/render.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:32) |
| 3.9 Step 3B adjustment | Pass | Source artifact ID, revision, and content hash must equal the exact released Step 3 artifact. [services/step3b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3b_preflight/validator.py:31) |
| 3.10 V2 integration | Request changes | Prompt predecessor, controlled V2 path, JSON-LD, and awaiting-gate contracts agree with the current implementation. The P1 Step 2 evidence gap and P2 diff-integrity failure prevent final end-to-end specification closure. |

## Prior Findings Status

- Report 15 P1 Step 3, Step 3B, and Step 4A findings: resolved by current schema, candidate validation, predecessor binding, graph, and claim-binding controls.
- Report 15 P2 prompt/path agreement: resolved. Step 2 names Step 1C and GATE-1C, and 1C, 3B, and 4A publish their exact controlled derived paths. [prompts/2-cluster-recherche.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/2-cluster-recherche.xml.md:4) [prompts/3b-performance-check.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3b-performance-check.xml.md:31) [prompts/4a-content-briefing-und-schema.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4a-content-briefing-und-schema.xml.md:38)
- Report 16 P1 Step 4B and Step 3 findings: resolved by current data-URL, graph, page-hash, schema, and renderer controls.
- Report 16 P2 forged-hash test finding: resolved. The current regression builds a complete lineage bundle and changes `solver_input_sha256` and `solver_output_sha256`. [tests/test_cross_step_safety.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_cross_step_safety.py:33)
- Report 15 P1 Step 2 evidence finding: partially resolved. Declaration, uniqueness, typed requests/responses, completed status, and field equality are enforced, but P1 remains open because the raw hash is asserted rather than bound to raw content.

## Checks Executed

1. `env PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: PASS on local Python 3.12. Acceptance: 7. Root discovery: 165. Contract discovery: 37. Total: 209 tests.

2. Step 2 in-memory tampered-raw-response public-preflight probe.
   Result: PASS when it should fail, as described in P1. No source, test, fixture, or state file was changed.

3. `git diff --check`
   Result: non-zero with tracked trailing-whitespace diagnostics, as described in P2.

4. Production source scan for `AHD`, `simCura`, `Pflegedienst`, and `ambulante` in `services`, `standards/outputs`, and `prompts`.
   Result: no matches.

5. Forbidden U+2013/U+2014 scan of Sprint 3 services, output schemas, and prompts.
   Result: 0 matches.

6. `python3.11 --version`
   Result: unavailable locally. The supplied Windows Python 3.11 209-pass claim is controller evidence and was not independently reproduced.

## Limits

- No network, provider, crawl, deployment, browser, commit, or external validator was accessed.
- The passed local suite demonstrates regression coverage but does not overturn the P1 direct acceptance probe.

REQUEST_CHANGES
