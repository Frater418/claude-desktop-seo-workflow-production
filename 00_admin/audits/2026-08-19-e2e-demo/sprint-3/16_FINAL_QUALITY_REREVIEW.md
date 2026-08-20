# Sprint 3 Final Quality Re-review

Date: 2026-08-19

Scope: Independent read-only re-review of Sprint 3 Tasks 3.1 through 3.10. This review read the governing instructions, plan and prior audit material only for scope navigation, then verified the current schemas, prompts, validators, renderers, portable JSON-LD adapter, controlled path layer, fixtures, tests, and current worktree directly. No source, test, fixture, state, configuration, or git metadata was modified.

## Verdict

REQUEST_CHANGES

## Findings

### P0

No P0 finding verified.

### P1

1. Step 4B does not reject all `data:` URLs and renders an accepted one into the customer page. The unsafe-markup guard only matches `data:text/html` and `data:application/javascript`, so the required general data-URL prohibition is not implemented. [services/step4b_preflight/validator.py:36](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:36) [services/step4b_preflight/validator.py:37](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:37) [services/step4b_preflight/render.py:45](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:45) A read-only in-memory probe replaced valid fixture HTML with `<a href="data:text/plain,probe">probe</a>` and obtained `valid=True`, no error codes, and `data_url_emitted=True`. This is a renderer trust-boundary failure for a prohibited URL scheme.

2. Step 4B emits JSON-LD metadata rather than a JSON-LD graph, producing an extractable but locally invalid script block. The page schema only permits `level` and `graph_hash` for `jsonld`, with no graph to validate or render. [standards/outputs/step-4b-page-spec.schema.json:9](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4b-page-spec.schema.json:9) [standards/outputs/step-4b-page-spec.schema.json:13](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4b-page-spec.schema.json:13) The renderer serializes that metadata in an `application/ld+json` script. [services/step4b_preflight/render.py:30](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:30) [services/step4b_preflight/render.py:42](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:42) Validating rendered positive-fixture HTML through the repository-local adapter returned `valid=False`, `blocks_found=1`, and `ERROR_SCHEMA_TYPE_MISSING`.

3. Step 4B treats two caller-provided hashes as evidence without computing a hash of the current page content. The validator compares `page.content_sha256` only to `staging.content_sha256`; it never derives a digest from `page.html` or the rendered output. [services/step4b_preflight/validator.py:34](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:34) [services/step4b_preflight/validator.py:35](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:35) A read-only probe changed valid fixture HTML to safe different content while retaining the original matching hashes. The candidate still returned `valid=True` with no errors. Staging evidence can therefore be asserted for content other than the rendered content.

4. The Step 3 renderer bypasses the closed candidate contract and renders a `completed` artifact. Its candidate validator checks plan semantics and solver payload hashes but does not validate the Step 3 schema or `candidate_status`; the renderer calls that weaker entrypoint instead of the public preflight boundary. [services/step3_preflight/validator.py:36](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:36) [services/step3_preflight/validator.py:65](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:65) [services/step3_preflight/validator.py:78](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:78) [services/step3_preflight/render.py:15](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:15) [services/step3_preflight/render.py:17](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:17) A read-only probe changed the positive candidate status to `completed`; `validate_step3_candidate` returned `valid=True` and `render_step3` produced Markdown. This contradicts the Step 3 awaiting-gate contract. [standards/outputs/step-3-plan.schema.json:3](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-3-plan.schema.json:3)

### P2

1. The regression named as a forged-Hash test does not mutate the hash fields validated by the current Step 3 implementation, then calls the public preflight without supplying its required lineage bundle. It changes legacy `input_sha256` and `output_sha256` fields, while production validates `solver_input_sha256` and `solver_output_sha256`; any rejection can be caused by missing lineage instead of forged actual hashes. [tests/test_cross_step_safety.py:33](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_cross_step_safety.py:33) [tests/test_cross_step_safety.py:35](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_cross_step_safety.py:35) [tests/test_cross_step_safety.py:38](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_cross_step_safety.py:38) [services/step3_preflight/validator.py:54](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:54) [services/step3_preflight/validator.py:59](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:59) This is a marker-style negative test and does not prove the behavior named by the test.

### P3

No P3 finding verified.

## Verified Controls

- All eleven current output schemas use Draft 2020-12 and close top-level objects. The focused validators and common lineage boundary construct `Draft202012Validator` with `FormatChecker`. [services/preflight_common/boundary.py:18](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:18) [services/step4a_preflight/validator.py:16](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:16) [services/step4b_preflight/validator.py:15](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:15)
- Public preflights require Project V2 identity, an awaiting-gate candidate, and an exact released predecessor artifact and release record. [services/preflight_common/boundary.py:42](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:42) [services/preflight_common/boundary.py:54](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:54) [services/preflight_common/boundary.py:56](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:56) [services/preflight_common/boundary.py:79](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:79)
- Step 4A carries a graph, computes its canonical SHA-256 hash, validates it through the local adapter, and turns adapter unavailability into `ERROR_JSONLD_VALIDATOR_UNAVAILABLE`. [services/step4a_preflight/validator.py:35](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:35) [services/step4a_preflight/validator.py:37](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:37) [services/step4a_preflight/validator.py:45](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:45) The adapter loads the repository-local file path and does not import through the external `mcp` namespace. [services/jsonld_validation.py:53](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/jsonld_validation.py:53) [services/jsonld_validation.py:55](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/jsonld_validation.py:55)
- Step 3 computes and verifies canonical solver input and output SHA-256 values. [services/step3_preflight/validator.py:21](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:21) [services/step3_preflight/validator.py:54](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:54)
- Controlled output paths reject unknown steps, unsafe identifiers, missing roots, root escapes, intermediate symlink or reparse components, and pre-existing destinations. [services/preflight_common/output_paths.py:33](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:33) [services/preflight_common/output_paths.py:49](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:49) [services/preflight_common/output_paths.py:54](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:54) [services/preflight_common/output_paths.py:66](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:66)
- Step 4B rejects script, iframe, object, embed, event-handler, and `javascript:` markup patterns, checks URL formats, and binds language, locale, service areas, and physical locations to Project V2. [services/step4b_preflight/validator.py:24](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:24) [services/step4b_preflight/validator.py:37](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:37) [services/step4b_preflight/validator.py:45](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:45)
- A source scan found no AHD or customer-specific production constants in Sprint 3 services, schemas, or prompts. The current Sprint 3 services, output schemas, and V2 prompts contained no U+2013 or U+2014 dash characters.

## Commands And Results

1. `PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: PASS. Acceptance 7, root discovery 158, contract discovery 37, total 202 tests.

2. `python3.11 --version`
   Result: not available in this review environment (`command not found`). Python 3.11 execution was not independently reproduced here. Controller evidence supplied for this final checkpoint reports Windows Python 3.11 full suite 202 PASS; the OMO Python 3.12 result was independently reproduced above as 202 PASS.

3. Read-only Step 4B data-URL driver using the current positive fixture.
   Result: `valid=True`, no errors, and `data_url_emitted=True` for `data:text/plain,probe`.

4. Read-only Step 4B rendered-output JSON-LD driver using `validate_local_jsonld_text`.
   Result: `valid=False`, `blocks_found=1`, `ERROR_SCHEMA_TYPE_MISSING`.

5. Read-only Step 4B stale-content-hash driver.
   Result: changed safe HTML with the prior page and staging hashes returned `valid=True` and no errors.

6. Read-only Step 3 renderer driver.
   Result: a candidate changed to `candidate_status=completed` returned `valid=True` from the renderer entrypoint and rendered Markdown.

7. `git status --short`, `git diff --stat`, and `git diff --check`.
   Result: the shared worktree remains broadly dirty. `git diff --check` reports existing trailing whitespace in tracked non-Sprint-3 files, including `standards/manifest.schema.json` and `tests/acceptance-tests.md`. This review did not modify those files.

## Required Resolution

1. Reject every `data:` URL at the Step 4B untrusted-markup boundary and add a direct negative regression.
2. Carry and locally validate an actual Step 4B JSON-LD graph, then render that graph rather than hash metadata.
3. Compute the Step 4B content hash from canonical content or the final deterministic rendering and bind staging evidence to that computed value.
4. Make the Step 3 renderer enforce the closed awaiting-gate candidate contract, and correct the stale forged-hash test so it mutates current hash fields within a complete lineage bundle.

REQUEST_CHANGES
