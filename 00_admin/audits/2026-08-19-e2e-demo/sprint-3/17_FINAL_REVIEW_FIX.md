# Sprint 3 Final Review Fix

Date: 2026-08-19
Author: Raphael Rechberger

## Scope

This fix resolves every verified P1 and P2 item in Sprint 3 reports 15 and 16 within the approved Sprint 3 contracts, preflights, renderers, prompts, tests, operator routes and output-contract documentation.

## RED Evidence

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_final_review_fixes
```

Initial result: 7 tests ran. Five assertions failed and one test errored before the corrections. The failures demonstrated arbitrary Step 3 solver input and schema bypass, Step 3 completed rendering, released Step 3B source-hash mismatch, unlinked Step 4A graph, and case-insensitive Step 4B data URL with stale content evidence. The error demonstrated the missing actual Step 4B graph contract and renderer path.

The Step 2 undeclared-row-evidence negative assertion and the original incomplete Step 3B fixture did not provide valid RED isolation. The regressions were corrected to use closed candidates and complete released lineage. The final Step 3B regression has complete Project V2, predecessor artifact and release records, and changes only `source_plan.content_sha256`. The forged-hash regression now has complete Step 2 released content and changes only `solver_input_sha256` and `solver_output_sha256`.

## GREEN Evidence

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_final_review_fixes tests.test_step2_contract tests.test_step3_contract tests.test_step3b_contract tests.test_step4a_contract tests.test_step4b_contract tests.test_cross_step_safety tests.test_preflight_common
```

Result: 34 tests passed.

Renderer and routing command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_step2_renderer tests.test_step3_renderer tests.test_step4a_renderer tests.test_step4b_renderer tests.test_cross_step_safety tests.test_operator_error_routing
```

Result: 17 tests passed.

Full OMO command:

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Result: PASS. Acceptance runner: 7 tests. Root unittest discovery: 165 tests. Contract unittest discovery: 37 tests. Total: 209 tests.

## Changed Behavior

- Step 2 candidates declare `language` and `geo`; each verified row has a distinct declared evidence ID. Operational preflight requires exactly one typed, schema-valid provider request and completed response per row, validates through `provider_gateway`, and binds project, deployment, language, geo, provider and raw-response hash.
- Step 3 candidate validation runs the closed Draft 2020-12 schema with `FormatChecker` before semantics. Rendering accepts only `awaiting_gate` candidates. Operational preflight validates canonical released Step 2 bytes against the predecessor artifact hash and requires the documented sorted verified-row projection as solver input.
- Step 3B binds source plan artifact ID, revision and content hash to the exact released predecessor record while preserving the distinct proposed artifact rule.
- Step 4A requires closed claim bindings. Every linked ledger claim has exactly one binding to a real graph node. YMYL, actual graph hashing and local JSON-LD validation remain mandatory.
- Step 4B rejects every case-insensitive `data:` URL. It requires and locally validates the actual graph, renders only that graph in `application/ld+json`, and binds page plus staging evidence to one deterministic canonical page payload hash.
- Prompts and the output contract use Step 1C and GATE-1C for Step 2, exact controlled derived paths, and supported JSON-LD levels. The two reported tracked whitespace defects were removed without content changes.

## Limitations

- Only local deterministic tests were run. No provider, network, crawl, deployment, browser, external JSON-LD service, commit or push was run.
- This environment executed Python 3.12. Python 3.11 and Windows portability were preserved by existing syntax and portability coverage but were not locally executed.
- The injected Python programming reference path was unavailable in this environment, so no external reference file could be read.
- `git diff --check` was run. It still reports broad pre-existing CRLF and trailing-whitespace diagnostics in tracked files outside this scoped repair, including the already dirty manifests and acceptance artifacts. No unrelated cleanup was performed.
