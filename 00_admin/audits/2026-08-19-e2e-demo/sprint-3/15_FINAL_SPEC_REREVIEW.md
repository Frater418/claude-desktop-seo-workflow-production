# Sprint 3 Final Specification Re-Review

Date: 2026-08-19

Scope: Independent read-only re-review of Tasks 3.1 through 3.10. This review read the current plan, reviews 07 and 08, fixes 09 through 14, current Sprint 3 schemas, prompts, validators, renderers, fixtures, tests, output-path contract, and current worktree state. Earlier reports were used only as navigation. Findings below are based on current source and commands executed in this review.

## Verdict

REQUEST_CHANGES

Open P1 findings prevent final approval. The full local suite is green, but it does not exercise the demonstrated cross-artifact bindings and candidate-only renderer boundary below.

## Findings

### P1

1. **Step 2 accepts provider-row evidence that is not declared or bound by the canonical candidate.** The Step 2 schema permits each row to name an arbitrary `evidence_id` while the candidate has an independent top-level `evidence_ids` list. It does not require row evidence IDs to be declared or to resolve to completed provider-gateway evidence. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-2-keyword-evidence.schema.json:7-8`. The candidate validator returns success immediately after schema acceptance and does not inspect row evidence linkage or raw provider records. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:23-33`. A direct public-preflight probe replaced the otherwise valid candidate's declared evidence with `evidence-unrelated-0001`; it returned `True` with no errors. This violates the required Step 2 provider-evidence boundary.

2. **Step 3 does not validate a closed canonical candidate at the candidate-only renderer boundary, and its solver input is not bound to Step 2 evidence.** `validate_step3_candidate` checks plan fields and hashes but never validates `step-3-plan.schema.json`. It accepts any canonical JSON object as `solver_input`, provided its self-reported hash matches. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:36-75`. `render_step3` calls this incomplete candidate-only validator, so it rendered a candidate changed to `candidate_status: completed`. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:15-24`. The direct probe supplied the exact canonical payload `{}` with its correct SHA-256 and got `step3_arbitrary_input=True`; the completed candidate also rendered. This does not meet the required closed candidate-only renderer validation or exact canonical solver-payload binding to released Step 2 evidence.

3. **Step 3B does not bind `source_plan` revision and hash to the released Step 3 predecessor.** The local immutability check compares source and proposed fields only within the candidate. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3b_preflight/validator.py:17-23`. The shared lineage check binds the released predecessor artifact and release record, but it does not compare that artifact's revision or `content_sha256` with `candidate.source_plan`. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:63-81`. A direct complete public-preflight probe changed `source_plan.content_sha256` from the released predecessor hash to `c` repeated 64 times and returned `True` with no errors. This permits a proposed adjustment to describe a different source plan while still passing the released-predecessor boundary.

4. **Step 4A validates a JSON-LD graph and the claim ledger independently, with no claim-to-graph linkage.** The briefing contract requires an object graph and its hash but contains no claim identifiers or graph-to-ledger reference. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4a-briefing.schema.json:16-18`. The validator checks only the ledger artifact ID, YMYL ledger fields, graph hash, and local graph validity. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:27-49`. A direct probe supplied a valid, hash-correct `Product` graph named `Unlinked graph` alongside the unchanged medical claim ledger; candidate validation returned `True`. This fails the required Step 4A claim linkage despite the now-present actual graph validation.

### P2

1. **Prompt contracts disagree with the implemented V2 lineage and output requirements.** Step 2 declares `previous_step` and its required released predecessor as Step 1, while the public preflight requires released Step 1C and the output contract names Step 1C. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/2-cluster-recherche.xml.md:4-8`, `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:59-63`, and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/dateinamen-und-output-vertrag.md:52`. Step 4A instructs the unsupported JSON-LD level `none`, although its schema permits only `basic` and `enhanced`. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4a-content-briefing-und-schema.xml.md:25-29` and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4a-briefing.schema.json:17`. The 1C, 3B, and 4A prompt output sections omit their exact controlled V2 derived paths that the output contract requires. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1c-pillar-template.xml.md:52-55`, `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3b-performance-check.xml.md:31-34`, `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4a-content-briefing-und-schema.xml.md:38-42`, and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/dateinamen-und-output-vertrag.md:51-56`.

2. **The tracked diff fails whitespace integrity.** `git diff --check` reports trailing whitespace in changed tracked files, including `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/manifest.schema.json:707` and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/acceptance-tests.md:1`. This is not a runtime failure, but it leaves the submitted tracked diff failing its standard integrity check.

### P3

No P3 finding verified.

## Task Verification Matrix

| Task | Result | Current evidence |
|---|---|---|
| 3.1 Step 1B architecture | Pass | Closed schema candidate validation, Project V2 and released-predecessor enforcement, and deterministic derived views are implemented. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1b_preflight/validator.py:80-96` and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1b_preflight/render.py:12-28`. |
| 3.2 Step 1C design | Pass | Candidate validation enforces closed design and template contracts, location safety, and common lineage. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/validator.py:62-85`. |
| 3.3 Step 1C templates | Pass | Renderer iterates every template and controlled writer derives one output for each template ID. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/render.py:39-66`. |
| 3.4 Provider contracts | Request changes | Provider schemas and gateway exist, but Step 2 itself does not bind its claimed provider rows to declared and completed evidence. See P1-1. |
| 3.5 Step 2 evidence | Request changes | Canonical candidate shape is used by the renderer, but provider-evidence binding is absent and the prompt names the wrong predecessor. See P1-1 and P2-1. |
| 3.6 Step 3 plan | Request changes | Public lineage checks are present, but closed candidate-only rendering and exact Step 2 solver-input binding are absent. See P1-2. |
| 3.7 Step 4A briefing | Request changes | Actual graph hashing and local validation are present, but graph claims are not linked to the ledger and prompt/schema agreement is incomplete. See P1-4 and P2-1. |
| 3.8 Step 4B page | Pass | Candidate validation binds Project V2 deployment language, locale, service areas, and verified physical locations. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:39-63`. |
| 3.9 Step 3B adjustment | Request changes | New proposed revision and distinct proposal hash are checked, but the stated source plan is not bound to the released predecessor revision and hash. See P1-3. |
| 3.10 V2 integration | Request changes | All seven public preflights call the common lineage boundary and controlled paths are implemented, but the remaining P1 bindings and prompt/path disagreement prevent end-to-end specification closure. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:25-81` and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:11-63`. |

## Required Cross-Cutting Verification

- **Canonical candidates and public preflights:** Pass for released predecessor, Project V2 identity, `awaiting_gate`, source artifact identity, release status, revision, and predecessor hash across all seven operational public preflights. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:34-81`.
- **Candidate-only renderers:** Pass for 1B, 1C, 2, 3B, 4A, and 4B. Step 3 is an exception because its candidate-only validator omits schema and lifecycle validation. See P1-2.
- **All-template Step 1C output:** Pass. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/render.py:39-52`.
- **Step 3 hashes and Step 3B immutability:** Hash syntax, canonical JSON byte hashing, and proposed-plan difference checks are present, but exact released-evidence input binding and source-plan binding are incomplete. See P1-2 and P1-3.
- **Step 4B locale and location binding:** Pass. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:45-63`.
- **Controlled V2 paths:** Pass in renderers. The destinations are fixed and reject invalid roots, identifiers, escapes, and existing outputs. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:33-71`.
- **Human Gate boundary:** Pass. V2 candidates are required to be `awaiting_gate`, and the V2 prompt contract test passed. See `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:54-55`.
- **Generic behavior and AHD hardcoding:** Pass. The full suite exercised non-AHD outdoor, solar, B2B, product, and national B2B fixtures. Direct source search found no AHD or customer-specific production constant in the reviewed Sprint 3 services, schemas, or V2 prompts.

## Commands Executed And Results

1. `git status --short`
   Result: broad dirty worktree with 41 modified tracked files and Sprint 3 runtime, standards, fixtures, and tests present as untracked paths.

2. `git diff --stat` and `git diff --name-only`
   Result: tracked diff contains 41 files, 6,205 insertions, and 5,882 deletions. Untracked Sprint 3 paths are not shown by Git diff but were inspected directly.

3. `git diff --check`
   Result: failed with trailing-whitespace diagnostics, including the P2-2 paths above.

4. `env PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: passed. Acceptance runner 7, root discovery 158, contract discovery 37, total 202 tests. This independently reproduces the controller-reported 202 total on local Python 3.12.

5. `env PYTHONDONTWRITEBYTECODE=1 python -c "import json,hashlib; from pathlib import Path; from services.step2_preflight.validator import validate_step2_candidate; from services.step3_preflight.validator import validate_step3_candidate; from services.step3_preflight.render import render_step3; root=Path('.'); step2=json.loads((root/'tests/fixtures/step2/non-ahd-solar-fr-ca.json').read_text())['candidate']; step2['candidate_status']='awaiting_gate'; step2['evidence_ids']=['evidence-unrelated-0001']; print(validate_step2_candidate(step2)['valid']); step3=json.loads((root/'tests/fixtures/step3/non-ahd-solar-fr-ca.json').read_text())['candidate']; step3['candidate_status']='completed'; output=json.dumps({key:step3[key] for key in ('weeks','mandatory_item_ids','backlog_item_ids','vertical_links','horizontal_links')},ensure_ascii=False,separators=(',',':'),sort_keys=True); step3.update({'solver_input':'{}','solver_output':output,'solver_input_sha256':hashlib.sha256(b'{}').hexdigest(),'solver_output_sha256':hashlib.sha256(output.encode()).hexdigest()}); step3.pop('input_sha256'); step3.pop('output_sha256'); print(validate_step3_candidate(step3)['valid'],bool(render_step3(step3)))"`
   Result: `step2_unbound_row_evidence=True`, `step3_arbitrary_input=True`, and `step3_renderer_completed=True`.

6. `env PYTHONDONTWRITEBYTECODE=1 python -c "import copy,runpy; from services.step3b_preflight.validator import validate_step3b_preflight; helpers=runpy.run_path('tests/test_preflight_common.py'); bundle=copy.deepcopy(helpers['_fixture']('tests/fixtures/step3b/non-ahd-product-bundle.json')); helpers['_bind_candidate'](bundle['adjustment']); bundle['adjustment'].pop('deployment_id',None); bundle['adjustment']['source_artifact_ids']=['artifact-predecessor-0001']; bundle['adjustment']['source_plan'].update({'artifact_id':'artifact-predecessor-0001','revision':1,'content_sha256':'c'*64}); artifact,release=helpers['_predecessor']('3','GATE-3'); bundle.update({'project':helpers['_project'](),'predecessor_artifact':artifact,'predecessor_release':release}); print(validate_step3b_preflight(bundle)['valid'])"`
   Result: `step3b_public_preflight_unbound_source_hash=True` with no errors.

7. `env PYTHONDONTWRITEBYTECODE=1 python -c "import hashlib,json; from pathlib import Path; from services.step4a_preflight.validator import validate_step4a_candidate; bundle=json.loads(Path('tests/fixtures/step4a/positive-bundle.json').read_text()); graph={'@context':'https://schema.org','@graph':[{'@type':'Product','name':'Unlinked graph'}]}; canonical=json.dumps(graph,ensure_ascii=False,separators=(',',':'),sort_keys=True); bundle['briefing']['jsonld']={'level':'basic','graph':graph,'graph_hash':hashlib.sha256(canonical.encode()).hexdigest()}; print(validate_step4a_candidate(bundle)['valid'])"`
   Result: `step4a_unlinked_graph=True`.

8. Read-only source searches for `AHD|simCura|Pflegedienst|ambulante` in `services/**/*.py`, `standards/outputs/*.json`, and `prompts/*.md`.
   Result: no matches in the reviewed production services, output schemas, or prompts.

No network, provider, crawl, deployment, commit, or external side-effect operation was run. The independent controller evidence of Windows Python 3.11 full-suite success was noted. This reviewer could execute only local Python 3.12, where the 202-test full suite also passed.

## Residual Limits

- This review did not run an external provider, crawler, deployment, or Rich Results service by constraint.
- The local environment did not provide Python 3.11 for a second direct execution. Windows Python 3.11 success is controller evidence, not locally reproduced execution.

REQUEST_CHANGES
