# Step 1 Foundation and Readiness Specification Review

- Author: Raphael Rechberger
- Audit date: 2026-08-19
- Scope: Foundation Gate A, Step 1 V2 contract, AHD sidecar lineage, quality gates, and readiness criteria.
- Method: Read-only inspection of the required plan, master audit, Prompt 1 V2, Foundation schemas and registries, services, tests, AHD staging data, and recorded evidence. No provider, deployment, or mutation was performed.

## Acceptance Basis

The implementation must preserve the immutable AHD baseline, provide a validating V2 sidecar, prevent Step 1 completion before the external Gate 1, provide the required crawl or an explicit blocker, enforce the Step 1 output and prompt contracts, and have green Host and OMO verification with no open P0 or P1 findings. These requirements are specified at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/.hermes/plans/2026-08-19-foundation-gates-step1-readiness.md:162-173`. The master audit additionally requires that only a domain transition service changes workflow status and that no step reaches approved or completed without the released predecessor, required artifact, and gate record at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-18-fundamental-workflow-audit/00_MASTER_AUDIT.md:199-218` and `:578-586`.

## Evidence Reviewed

### Executed in this audit

- `python tests/run_full_suite.py` completed successfully: the acceptance runner reported 7 of 7 and unittest discovery reported 52 passing tests. The runner invokes both commands at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/run_full_suite.py:24-28`.
- `validate_step1_preflight()` returned `{"valid": true, "errors": []}` for the current AHD bundle. The validator's submission checks are implemented at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:195-442`.
- SHA-256 and byte-count comparison of all four baseline files returned no mismatch. The immutable set and sidecar-only rule are recorded at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-18-fundamental-workflow-audit/AHD_STEP0_IMMUTABLE_BASELINE.json:7-30`.

### Inspected recorded evidence

- The AHD V2 project records the legacy manifest SHA-256 `d925...98ab` at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/project.v2.json:6-9`, and the preflight source artifact binds the same hash at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/preflight/step1-submission.bundle.json:193-206`.
- Run `run-ahd-step1-crawl-004` is the canonical crawl: the decision record identifies it as the only accepted crawl at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/preflight/step1-submission.bundle.json:178`, its runtime gate binds its hash at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/preflight/step1-submission.bundle.json:303-326`, and its source evidence points to the run-004 evidence file at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/preflight/step1-submission.bundle.json:359-369`.
- The recorded crawl passed with 167 URLs, 18 HTML URLs, and no URL limit hit at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/crawl-evidence.json:12-18`. The exported files and their hashes are recorded at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/crawl-evidence.json:18-93`.
- No fresh OMO execution evidence was available for independent inspection. The current audit did execute the local Host suite, but it cannot represent an OMO run.

## Findings

### P0-01: No transition service enforces Gate 1 approval before Step 1 becomes approved or completed

The master audit requires a domain transition service as the sole status writer and requires artifact, hash, policy, reviewer, approval, and revision binding before state changes. The implementation exposes only a preflight validator that accepts the `awaiting_gate` state and explicitly rejects any embedded Gate 1 approval at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:410-439`. The transition schema declares `approve` and `complete`, but is declarative only at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/runtime/transition-command.schema.json:5-18`; it cannot itself prevent a caller from writing a `run-envelope` status. The recorded AHD bundle is consequently only a submitted `awaiting_gate` run at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/preflight/step1-submission.bundle.json:179-191`, not a demonstrably enforced Gate 1 lifecycle.

Required fix: implement and test a single transition service that loads the workflow graph, validates expected revision, predecessor release, current artifact hash and revision, matching passed quality gates, and a current external Gate 1 approval before it writes `approved` or `completed`. Reject direct state changes with the stable error-envelope codes. Add positive and negative Step 1 completion tests, including stale approval and changed artifact cases.

### P1-01: The required Step 1 preflight CLI is absent

Wave 2 explicitly requires a Step 1 preflight CLI at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/.hermes/plans/2026-08-19-foundation-gates-step1-readiness.md:67-75`. The validator provides a library function beginning at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:195` and ends after returning its result at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:441-442`; unlike the domain validator CLI at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/domain_contract/validator.py:219-240`, it has no argument parser, JSON output option, or exit-code entrypoint. During this audit, `python -m services.step1_preflight.validator --input ... --json-out` exited without producing a validation result.

Required fix: provide a fail-fast CLI that requires a bundle path, emits the structured result, returns nonzero for invalid input, and is covered by positive and negative CLI tests.

### P1-02: Crawl-gate enforcement does not implement all required Step 1 crawl checks

The plan requires at least start URL and final URL, status codes, indexability, canonicals, titles, meta descriptions, H1/H2, internal links, hreflang, structured data, redirects and broken links, plus crawl and export hashes at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/.hermes/plans/2026-08-19-foundation-gates-step1-readiness.md:95-108`. The crawl evidence schema includes `start_url` but has no final URL field at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/quality/screaming-frog-crawl.schema.json:7-13`; its findings contain no H2, internal-link, or redirect/broken-link fields at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/quality/screaming-frog-crawl.schema.json:44-58`. The adapter computes only the listed issue sets at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/quality_gate_runner/screaming_frog.py:280-343`, and the Step 1 preflight accepts a passed crawl without evaluating those omitted checks at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:327-392`.

Required fix: extend the crawl contract and adapter to record final URL and explicit H2, internal-link, redirect, and broken-link findings. Define blocking thresholds or an explicit reviewed-warning policy, then require the resulting fields in Step 1 preflight and add negative tests for each required criterion.

### P1-03: Blocking registry policy is not evaluated by Step 1 preflight

The quality registry defines three blocking Step 1 gates, including independent configured-source verification and the human artifact gate at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/quality/quality-gate-registry.json:18-51`. The registry schema permits the `when_configured` applicability used by that gate at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/quality/quality-gate-registry.schema.json:21-44`. Step 1 preflight does not load the registry. It only searches hard-coded records for `qg-domain-contract` and `qg-step1-crawl-snapshot` at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:268-280` and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:394-408`. Thus a configured Ahrefs or GSC source cannot cause the registry's required blocker, and no implementation evaluates the registered Gate 1 artifact approval after submission.

Required fix: make preflight and the transition service resolve applicable gates from the versioned registry, require evidence and failure handling for every blocking gate, and test configured-source absence, not-applicable decisions, passed independent evidence, and the external Gate 1 approval gate.

### P1-04: The AHD canonical artifact path diverges from the Prompt 1 output contract and preflight validates copied bytes rather than the stored artifact

Prompt 1 requires canonical output at `outputs/1-topic-inventory.json`, derives Markdown from it, and binds the exact canonical bytes to the artifact record, gate run, and run output hash at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1-pillar-identifikation.xml.md:55-64` and `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1-pillar-identifikation.xml.md:75-90`. The AHD sidecar instead stores the canonical JSON at `/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/outputs/step1/topic-inventory.v1.json:1`, while the preflight accepts an `inventory_bytes` string from the submission bundle at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:152-162` and hashes that in-memory value at `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:227-258`. It never resolves the artifact `storage_key` or proves the bytes at the stored canonical location equal the submitted bytes.

Required fix: reconcile Prompt 1 and the sidecar storage convention in a single versioned contract. The CLI must read the canonical artifact from its declared storage key, verify its SHA-256 against the artifact record and all dependent runtime records, and render Markdown only from those verified bytes.

## No Lower-Severity Findings

No P2 or P3 findings are reported. The immutable baseline, domain-sidecar validation, canonical inventory schema, hash lineage, and current local test suite provide useful readiness evidence, but do not resolve the open P0 and P1 findings above.

## Overall Verdict

REQUEST_CHANGES
