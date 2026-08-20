# Sprint 3 Final Quality Approval

Date: 2026-08-19
Reviewer: Reviewer B
Scope: Fresh read-only audit of Sprint 3 Tasks 3.1 through 3.10. I read `AGENTS.md`, the Sprint 3 task matrix in report 07, reports 15 and 16, and fix report 17 only for navigation. Findings and command results below come from the current workspace. No network, provider, crawl, deployment, commit, push, reset, checkout, source, test, fixture, state, or prior-report mutation was performed.

## Final Verdict

REQUEST_CHANGES

Two P1 renderer trust-boundary bypasses permit derived Step 2 and Step 3 artifacts to be emitted without the operational evidence that their public preflights require. The current tracked diff also fails the required whitespace integrity check.

## Findings

### P0

No P0 finding verified.

### P1

1. **The Step 2 renderer bypasses exact provider-evidence cardinality and identity validation.** `render_step2` calls `validate_step2_candidate`, which checks only candidate-local row declarations, then emits every verified row. It never calls `validate_step2_preflight` or `_provider_records_valid`. The latter is the only current implementation that requires one unique record for each referenced evidence ID, schema-valid provider request and response objects, matching project, deployment, language and geo, and validated provider plus raw-response hash identity. [services/step2_preflight/render.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/render.py:17) [services/step2_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:79) [services/step2_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:114)

   Independent in-memory probe: a closed, `awaiting_gate` non-AHD Step 2 candidate with 25 declared verified rows rendered 25 CSV rows through `render_step2({"candidate": candidate})`; the same bundle returned `valid=False` from `validate_step2_preflight` because it had no `provider_evidence_records`. The renderer CLI accepts JSON input directly, so this is an actual artifact-emission bypass, not merely a unit-level distinction.

2. **The Step 3 renderer bypasses released Step 2 lineage and solver-input binding.** `render_step3` validates only the candidate-local schema and solver hashes. The operational preflight separately requires exact canonical released Step 2 bytes, verifies those bytes against the predecessor artifact hash, validates the released Step 2 candidate, and requires `solver_input` to equal its deterministic verified-row projection. [services/step3_preflight/render.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:15) [services/step3_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:54) [services/step3_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:99)

   Independent in-memory probe: an otherwise closed `awaiting_gate` Step 3 candidate with canonical `{"rows":[]}` solver input, matching SHA-256 values, and no lineage bundle returned `candidate_only=True` and produced Markdown through `render_step3`. The same input returned `public_without_lineage=False` from `validate_step3_preflight`. This allows a user of the renderer CLI to emit a plan whose input has not been bound to released Step 2 evidence.

### P2

1. **The required `git diff --check` result is currently false.** Independent execution reported trailing-whitespace diagnostics throughout the tracked diff, including [tests/fixtures/sample_manifest.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/fixtures/sample_manifest.json:1), [tests/acceptance-tests.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/acceptance-tests.md:54), and [tests/run_acceptance_tests.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/run_acceptance_tests.py:1). This contradicts the supplied controller claim of exit code 0. It is a submission-integrity defect, even though the cited files are outside the two P1 renderer paths.

### P3

No P3 finding verified.

## Verified Controls

- The inspected production schema set is Draft 2020-12 and top-level closed. A local schema scan checked 28 schemas under `standards/outputs`, `standards/providers`, `standards/runtime`, and `standards/domain` with no failures. Candidate and lineage paths construct `Draft202012Validator` with `FormatChecker`. [services/preflight_common/boundary.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:18) [services/step4a_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:16) [services/step4b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:18)
- Public preflights enforce Project V2 identity, `awaiting_gate`, exact released predecessor artifact and release bindings, and required source artifact identity. [services/preflight_common/boundary.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:25)
- Step 3 candidate validation closes its contract, rejects premature completion, and computes SHA-256 values over canonical solver bytes. The focused regression verifies extra-field and completed-candidate rejection. [services/step3_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:23) [tests/test_final_review_fixes.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_final_review_fixes.py:59)
- Step 3B compares source plan artifact ID, revision and hash with the released Step 3 predecessor. [services/step3b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3b_preflight/validator.py:27)
- Step 4A requires a canonical-hash-correct graph, local JSON-LD validity, and exactly one claim binding per ledger claim to a real graph node. [services/step4a_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:40)
- Step 4B hashes actual canonical page payload bytes, binds staging evidence to that hash, rejects case-insensitive `data:` URLs plus script, iframe, object, embed, event handlers and `javascript:`, and renders the actual graph that local validation accepted. [services/step4b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:23) [services/step4b_preflight/validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:47) [services/step4b_preflight/render.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/render.py:23)
- Controlled destinations reject unknown steps, unsafe identifiers, invalid roots, root escapes, symlink or reparse components, and pre-existing outputs. Stable operator error routing and the repository-local Windows-safe JSON-LD adapter are covered by passing tests. [services/preflight_common/output_paths.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:33) [tests/test_operator_error_routing.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_operator_error_routing.py:1) [tests/test_step4a_import_portability.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/test_step4a_import_portability.py:1)
- The full suite exercises generic non-AHD fixtures. A source scan found no forbidden U+2013 or U+2014 characters in Sprint 3 services, output schemas, or prompts, and no AHD-specific production constant in those paths. The legacy generic kickoff prompt contains a simCura example, but it is outside the Sprint 3 runtime paths and was not treated as an AHD runtime dependency.

## Independently Reproduced Checks

1. `PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`: PASS. Acceptance 7, root discovery 165, contract discovery 37, total 209.
2. Focused contract command from report 17: PASS, 34 tests.
3. Focused renderer and routing command from report 17: PASS, 17 tests. The two commands overlap on five cross-step tests, yielding the controller's stated 46 unique focused tests.
4. Direct Step 2 and Step 3 in-memory renderer versus public-preflight probes: reproduced both P1 bypasses above.
5. `git diff --check`: FAIL, as described in P2-1.
6. `python3.11 --version`: unavailable in this Linux environment. The supplied Windows Python 3.11 209-pass claim was not independently reproducible here.

## Residual Limits

- No external provider, crawler, deployment, browser, network service, or Rich Results service was used by constraint.
- Passing local tests do not remove the P1 findings because the existing renderer tests intentionally exercise candidate-only input and do not require each renderer CLI to invoke the operational preflight boundary.

REQUEST_CHANGES
