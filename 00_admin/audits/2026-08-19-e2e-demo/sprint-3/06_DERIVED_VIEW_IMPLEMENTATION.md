# Sprint 3 Derived View Implementation

## Scope

Implemented deterministic, validator-backed derived-view renderers only for Steps 1c, 2, 3, 3b, 4a, and 4b.

- `services/step1c_preflight/render.py`: customer token CSS and standalone template HTML.
- `services/step2_preflight/render.py`: verified provider-row UTF-8 CSV.
- `services/step3_preflight/render.py`: 17-week Markdown plan with capacity, backlog, and link graphs.
- `services/step3b_preflight/render.py`: immutable source and proposed-plan adjustment Markdown.
- `services/step4a_preflight/render.py`: Notion-compatible frontmatter, claim/evidence references, and canonical JSON-LD data.
- `services/step4b_preflight/render.py`: standalone responsive HTML with canonical metadata, forms, consent, tracking slots, service areas, links, and JSON-LD data.

Every renderer invokes its existing step validator before generating output. Every CLI requires `--input` and `--output`, rejects an existing target unless `--overwrite` is supplied, and writes only after validation succeeds.

## TDD Evidence

RED command:

```text
python -m unittest tests.test_step1c_renderer tests.test_step2_renderer tests.test_step3_renderer tests.test_step3b_renderer tests.test_step4a_renderer tests.test_step4b_renderer -v
```

Result: 6 import errors because the six renderer modules did not yet exist.

GREEN command:

```text
python -m unittest tests.test_step1c_renderer tests.test_step2_renderer tests.test_step3_renderer tests.test_step3b_renderer tests.test_step4a_renderer tests.test_step4b_renderer -v
```

Result: 7 tests passed. Coverage includes deterministic output, non-AHD tokens, no CDN marker, service-area safety, CSV columns and verified-row filtering, immutable adjustment references, canonical claim/evidence and JSON-LD data, and invalid-input no-write behavior.

## Full Verification

Command:

```text
python tests/run_full_suite.py
```

Result: passed.

- Acceptance runner: 7 tests.
- Root unittest discovery: 143 tests.
- Contract unittest discovery: 37 tests.
- Total: 187 tests.

## Environment Limits

`lsp_diagnostics` was requested for all six new renderer modules. The configured Python server, `basedpyright`, is not installed and had previously been declined, so no LSP diagnostics could run. No network, provider, crawl, deployment, schema, prompt, validator, runtime, routing, state, AHD, or plan changes were made.
