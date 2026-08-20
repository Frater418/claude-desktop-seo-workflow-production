# Sprint 3 Ultimate Specification Approval Review A

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Fresh independent read-only final review of Sprint 3 Tasks 3.1 through 3.10. Reports 18, 19, and 20 were used only to locate the current scope. Findings and outcomes below are based on the current repository, read-only local commands, and in-memory probes. No network, provider, crawl, deployment, browser, commit, push, source, test, fixture, schema, prompt, state, configuration, or existing-report mutation was performed.

## Final Verdict

APPROVED

The previously reported P1 evidence-hash and renderer-boundary defects are closed in the current production paths. The provider gateway computes the canonical raw-response SHA-256 itself and rejects stale declarations. Step 2 requires one completed, gateway-validated provider exchange for each verified row. Public Step 2 and Step 3 rendering and writing require complete operational bundles. Step 3 binds both the exact released Step 2 canonical bytes and their deterministic solver projection.

## Findings

### P0

No P0 findings verified.

### P1

No P1 findings verified.

### P2

No P2 findings verified.

### P3

No P3 findings verified.

## Directly Reproduced Controls

1. Provider raw-response hash binding: [`validate_exchange`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/provider_gateway/core.py:73) canonicalizes `raw_response` with sorted keys, compact ASCII JSON, and UTF-8 bytes, computes SHA-256, rejects a differing declared digest with `raw_response_hash_mismatch`, and returns the computed digest. Direct in-memory tampering changed only `raw_response` while retaining its prior declared digest. Command outcome: `{'gateway_outcome': 'ERROR_PROVIDER_GATEWAY', 'gateway_violations': ['raw_response_hash_mismatch']}`.

2. Step 2 exact exchange binding: [`_provider_records_valid`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:79) requires a record set with exactly the candidate's distinct evidence IDs, validates both provider schemas, validates every exchange through the gateway, and requires exactly one matching row with the gateway-computed provider and raw-response hash. Directly changing the first complete-bundle response payload caused public preflight rejection: `{'valid': False, 'codes': ['ERROR_STEP2_PREFLIGHT']}`.

3. Step 2 public renderer and writer boundary: [`render_step2`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/render.py:25) and [`write_step2`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/render.py:35) call [`validate_step2_preflight`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:114) before deriving data or resolving a destination. Direct candidate-only calls produced `RendererError`; direct write probes reported `('step2', 'RendererError', False)`, where `False` confirms the controlled CSV did not exist afterward.

4. Step 3 released bytes and solver projection: [`validate_step3_preflight`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:99) hashes exact `predecessor_content`, requires canonical valid Step 2 JSON, and compares `solver_input` with [`step2_solver_projection`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:44). A complete bundle returned `complete_bundle_valid: True`. Replacing solver input with canonical `{"rows":[]}` and recomputing its candidate hash returned `tampered_valid: False` with `ERROR_STEP3_PREFLIGHT`.

5. Step 3 public renderer and writer boundary: [`render_step3`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:22) and [`write_step3`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:40) call the operational preflight before rendering or resolving an output path. Direct candidate-only rendering produced `RendererError`; the direct write probe reported `('step3', 'RendererError', False)`, where `False` confirms the controlled Markdown did not exist afterward.

6. Shared lineage and controlled paths: [`validate_lineage`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/boundary.py:25) requires Project V2 identity, `awaiting_gate`, a released predecessor with exact artifact ID, revision, and hash, plus source-artifact membership. [`resolve_step_output`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/preflight_common/output_paths.py:33) restricts output steps to the V2 path map, rejects unsafe identifiers, root escapes, symlink or reparse components, and existing outputs.

7. Prior Sprint 3 controls remain present: Step 3B rejects source-plan overwrites, non-incremented revisions, and reused hashes in [`validate_step3b_candidate`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3b_preflight/validator.py:10). Step 4A requires canonical locally valid JSON-LD and one valid graph-node binding per ledger claim in [`validate_step4a_candidate`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:26). Step 4B binds canonical page and staging hashes, validates the actual JSON-LD graph, rejects embedded or executable markup including case-insensitive `data:`, and binds service areas to Project V2 in [`validate_step4b_candidate`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:30).

## Task Resolution Matrix

| Task | Result | Independently verified current evidence |
| --- | --- | --- |
| 3.1 Step 1B architecture | Pass | Closed architecture candidate, exact decision coverage, URL and canonical conflict checks, link-graph checks, released Step 1 lineage, and deterministic Markdown and HTML views are present. |
| 3.2 Step 1C design | Pass | Closed design and template candidates, Step 1B lineage, accessibility and JSON-LD references, plus service-area and physical-location claim protections are present. |
| 3.3 Step 1C templates | Pass | Renderer iterates every template and controlled writes target `v2/outputs/step1c/templates/{identifier}.v1.html`. |
| 3.4 Provider contracts | Pass | Closed provider request and response contracts support provider-neutral evidence. Gateway validation is contract-only and now cryptographically binds raw evidence bytes. |
| 3.5 Step 2 evidence | Pass | Closed awaiting-gate candidate validation enforces declared distinct evidence and at least 25 verified rows per approved pillar. Operational preflight additionally enforces exact completed provider records and gateway-computed raw hashes. |
| 3.6 Step 3 plan | Pass | Closed 17-week candidate and canonical solver hashes are enforced. Operational preflight binds exact released Step 2 bytes and the sorted verified-row projection. |
| 3.7 Step 4A briefing | Pass | Claim ledger, YMYL policy, gateway SERP boundary, canonical graph hash, local JSON-LD validation, exact claim binding, and Step 3 lineage are enforced. |
| 3.8 Step 4B page | Pass | Project V2 deployment, locale, service area, safe markup, content and staging hash, actual graph validation, and Step 4A lineage are enforced. |
| 3.9 Step 3B adjustment | Pass | Exact released Step 3 source binding and immutable distinct proposed artifact, revision, and hash are enforced. |
| 3.10 V2 integration | Pass | The V2 prompts, closed output contracts, shared lineage boundary, controlled path map, generic fixtures, and production renderer paths agree with the current implementation. |

## Commands And Observed Outcomes

1. `env PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: PASS. Acceptance 7, root discovery 171, contract discovery 37, total 215 tests.

2. `env PYTHONDONTWRITEBYTECODE=1 python -c 'from tests.test_provider_gateway import load_fixture; from services.provider_gateway.core import ProviderGatewayError, validate_exchange; fixture=load_fixture(); fixture["response"]["raw_response"]={"tampered":"direct"}; validate_exchange(fixture["request"], fixture["response"])'`
   Result: `ERROR_PROVIDER_GATEWAY` with `raw_response_hash_mismatch`.

3. `env PYTHONDONTWRITEBYTECODE=1 python -c 'from tests.test_step2_renderer import _operational_bundle; from services.step2_preflight.validator import validate_step2_preflight; bundle=_operational_bundle(); bundle["provider_evidence_records"][0]["response"]["raw_response"]={"tampered":"direct"}; print(validate_step2_preflight(bundle))'`
   Result: public Step 2 preflight returned invalid with `ERROR_STEP2_PREFLIGHT`.

4. `env PYTHONDONTWRITEBYTECODE=1 python -c 'from tests.test_step2_renderer import _operational_bundle as s2; from tests.test_step3_renderer import _operational_bundle as s3; from services.step2_preflight.render import render_step2; from services.step3_preflight.render import render_step3; render_step2({"candidate":s2()["candidate"]}); render_step3({"candidate":s3()["candidate"]})'`
   Result: `[('step2', 'RendererError'), ('step3', 'RendererError')]`.

5. `env PYTHONDONTWRITEBYTECODE=1 python -c 'from pathlib import Path; from tests.test_step2_renderer import _operational_bundle as s2; from tests.test_step3_renderer import _operational_bundle as s3; from services.step2_preflight.render import write_step2; from services.step3_preflight.render import write_step3; root=Path(".").resolve(); write_step2({"candidate":s2()["candidate"]}, root); write_step3({"candidate":s3()["candidate"]}, root)'`
   Result: `[('step2', 'RendererError', False), ('step3', 'RendererError', False)]`. Neither controlled target existed after rejection.

6. `env PYTHONDONTWRITEBYTECODE=1 python -c 'import copy, hashlib, json; from tests.test_step3_renderer import _operational_bundle; from services.step3_preflight.validator import validate_step3_preflight; bundle=_operational_bundle(); tampered=copy.deepcopy(bundle); tampered["candidate"]["solver_input"]=json.dumps({"rows":[]}, separators=(",", ":"), sort_keys=True); tampered["candidate"]["solver_input_sha256"]=hashlib.sha256(tampered["candidate"]["solver_input"].encode()).hexdigest(); print(validate_step3_preflight(tampered))'`
   Result: complete bundle accepted, tampered canonical solver input rejected with `ERROR_STEP3_PREFLIGHT`.

7. `git diff --check`
   Result: exit 0. Git emitted CRLF conversion warnings only and no whitespace-error diagnostics. [`.gitattributes`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/.gitattributes:1) declares LF for the relevant text formats.

8. `env PYTHONDONTWRITEBYTECODE=1 python -c '<read-only recursive scan of services, standards/outputs, and prompts for AHD terms and U+2013/U+2014>'`
   Result: no `AHD`, `simCura`, `Pflegedienst`, or `ambulante` matches in `services`, `standards/outputs`, or `prompts`, and no U+2013 or U+2014 matches in the scanned text paths.

## Limits

- This review intentionally did not access a network, provider, crawler, deployment, browser, external validator, commit, or push surface.
- Python 3.11 was not available in this Linux environment. The supplied Windows Python 3.11 result was not used as proof.
- The full local suite and direct in-memory probes establish the inspected contract behavior. They do not constitute external provider, crawl, deployment, or Rich Results validation.

APPROVED
