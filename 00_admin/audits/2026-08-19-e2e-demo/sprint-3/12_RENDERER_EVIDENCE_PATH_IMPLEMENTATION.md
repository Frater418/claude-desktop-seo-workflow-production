# Renderer Evidence Path Implementation

Date: 2026-08-19

## RED Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_controlled_output_paths -v
```

Result before implementation: 1 module import error because `services.preflight_common.output_paths` did not exist.

Regression RED command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_controlled_output_paths tests.test_step1c_renderer -v
```

Result before the final correction: 4 tests passed, 1 failure, 1 error. A missing workspace root raised raw `FileNotFoundError`; Step 1C derived `pillar-kayaks.v1.html` from `content_id` instead of `template-outdoor-kayaks-0001.v1.html` from `template_id`.

## Implemented Scope

- Added controlled V2 paths and workspace-root-only writers for Steps 1C, 2, 3, 3B, 4A, and 4B. Existing outputs, unsafe identifiers, and escapes fail with routed `ERROR_OUTPUT_*` codes.
- Replaced Step 3 generic hashes with canonical UTF-8 solver input and output payloads, calculated SHA-256 values, and solver output to candidate plan binding.
- Added Step 4A JSON-LD graph carriage, canonical graph hashing, local validator enforcement, and extractable JSON rendering while retaining Notion frontmatter.
- Bound Step 4B to Project V2 validation, deployment identity, language, locale, supported service areas, verified physical locations, URI validation, and safe markup.
- Updated V2 output-path documentation and Step 2 and Step 3 candidate prompt outputs.

## GREEN Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_controlled_output_paths -v
```

Result: 2 tests passed.

Final direct regression command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_controlled_output_paths tests.test_step1c_renderer -v
```

Result: 6 tests passed.

## Final GREEN Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_controlled_output_paths tests.test_step1c_renderer tests.test_step2_renderer tests.test_step3_renderer tests.test_step3b_renderer tests.test_step4a_renderer tests.test_step4b_renderer tests.test_step3_contract tests.test_step4a_contract tests.test_step4b_contract tests.test_cross_step_safety tests.test_operator_error_routing -v
```

Result: 35 tests passed.

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Result: acceptance 7/7, root discovery 154, contract discovery 37, total 198 tests passed.

## Files Changed

- `services/preflight_common/output_paths.py`
- `services/preflight_common/__init__.py`
- `standards/outputs/step-3-plan.schema.json`
- `services/step3_preflight/validator.py`
- `standards/outputs/step-4a-briefing.schema.json`
- `services/step4a_preflight/validator.py`
- `services/step4a_preflight/render.py`
- `services/step4b_preflight/validator.py`
- `services/step4b_preflight/render.py`
- `services/step1c_preflight/render.py`
- `services/step2_preflight/render.py`
- `services/step3_preflight/render.py`
- `services/step3b_preflight/render.py`
- `standards/outputs/step-4b-page-spec.schema.json`
- `standards/dateinamen-und-output-vertrag.md`
- `prompts/2-cluster-recherche.xml.md`
- `prompts/3-120-tage-plan.xml.md`
- `services/operator_routing/router.py`
- `standards/operator/error-routing-policy.json`
- `tests/test_controlled_output_paths.py`
- `tests/test_step3_contract.py`
- `tests/test_step3_renderer.py`
- `tests/test_step4a_contract.py`
- `tests/test_step4a_renderer.py`
- `tests/test_step4b_contract.py`
- `tests/test_step4b_renderer.py`

## Environment Limitations

- Python 3.12 was available. Python 3.11 was not available.
- `basedpyright` was unavailable, so LSP diagnostics could not run.
- No network, provider, crawl, deployment, git commit, or push operation was performed.

## Verified Acceptance Items

- Controlled renderer destinations derive only the declared V2 output paths and refuse overwrite.
- Solver evidence, JSON-LD graph evidence, Project V2 deployment locale binding, unsafe markup rejection, and error-route completeness are exercised by the focused suite.
- No network, provider, crawl, deployment, git commit, or push operation was performed.
