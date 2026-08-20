# Step 1 Foundation and Readiness Quality Review

## Scope and Evidence Method

This was a read-only audit of the Step 1 Foundation contracts, registries, Prompt 1 v2, preflight implementation, Screaming Frog adapter, relevant tests, and AHD staging lineage. The implementation declares a closed canonical inventory, an awaiting-gate submission, and revision-bound approvals in [03_STEP1_CONTRACT_IMPLEMENTATION.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/03_STEP1_CONTRACT_IMPLEMENTATION.md:7), [03_STEP1_CONTRACT_IMPLEMENTATION.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/03_STEP1_CONTRACT_IMPLEMENTATION.md:22), and [03_STEP1_CONTRACT_IMPLEMENTATION.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/03_STEP1_CONTRACT_IMPLEMENTATION.md:32).

Executed evidence in this audit:

- `python tests/run_full_suite.py` completed successfully: acceptance runner 7 of 7 and unittest discovery 52 tests.
- `validate_step1_preflight()` returned `{"errors": [], "valid": true}` for the AHD v2 submission bundle.

Inspected recorded evidence:

- AHD run 004 is the recorded crawl for `dep-ahd-de-munich`, with 167 URLs, 18 HTML URLs, no reached URL limit, and a recorded `passed` status in [crawl-evidence.json](/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/crawl-evidence.json:3) and [crawl-evidence.json](/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/crawl-evidence.json:12).
- The same recorded evidence reports one internal 4xx, three non-indexable URLs, and title, meta, H1, and canonical findings in [crawl-evidence.json](/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/crawl-evidence.json:95). The generated issue report classifies the internal 4xx as High severity in [issues_overview_report.csv](/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/issues_overview_report.csv:25).

No fresh persisted OMO test-run artifact was present in the inspected audit path. The executed Host evidence above is therefore the current executable verification, while the crawl and AHD submission are recorded evidence only.

## Findings

### P1-01: The blocking crawl gate can pass despite a recorded High severity internal 4xx

The registry calls `qg-step1-crawl-snapshot` blocking, but its requirements only require a successful crawl, present exports, no URL-limit hit, and hashes in [quality-gate-registry.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/quality/quality-gate-registry.json:18). The adapter sets `passed` unless the URL limit is reached, without evaluating `findings` in [screaming_frog.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/quality_gate_runner/screaming_frog.py:367). The Step 1 preflight likewise accepts a snapshot by `status: passed`, counts greater than zero, exports, and a passed gate record, without applying a finding threshold in [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:349) and [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:380). This permits the recorded AHD 4xx to produce a green preflight.

Required fix:

1. Version a Step 1 crawl disposition policy that maps each finding class and severity to pass, block, or explicit approved waiver.
2. Make `build_evidence` and the Step 1 preflight apply that policy, block unwaived internal 4xx and any other configured blocking condition, and carry the policy version and disposition in the crawl evidence and quality-gate record.
3. Add negative tests using a nonzero internal 4xx and each configured blocking class, proving that a `passed` status and submission cannot be manufactured from the affected evidence.

### P1-02: Prompt 1 retains an unconstrained direct AgentSEO execution path

Prompt 1 directs the operator to use direct AgentSEO MCP tools or web search for competitor analysis in [1-pillar-identifikation.xml.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1-pillar-identifikation.xml.md:40), but does not require `location`, `location_code`, `language`, `sync: false`, or job-status collection. Those fields and asynchronous handling are mandatory repository rules in [AGENTS.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/AGENTS.md:56) and [AGENTS.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/AGENTS.md:72). The AHD deployment records provider location verification as `unknown` in [step1-submission.bundle.json](/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/v2/preflight/step1-submission.bundle.json:95), so the prompt does not have a verified provider location code to bind to such a call.

Required fix:

1. Remove direct provider invocation from Prompt 1, or require the versioned provider gateway contract before a provider call is permitted.
2. Require an explicit verified provider-location binding, `location`, `location_code`, `language`, `sync: false`, provider job ID, raw-response hash, and retrieved timestamp before provider-derived competitor evidence can enter the inventory.
3. Add contract tests for missing or unknown provider-location verification and for each required request field, including a test that rejects direct prompt-created provider evidence.

### P2-01: Security export is retained but omitted from machine-readable crawl findings

The adapter requires the `Security:All` export in [screaming_frog.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/quality_gate_runner/screaming_frog.py:24), but its summarized finding categories omit security in [screaming_frog.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/quality_gate_runner/screaming_frog.py:282). The crawl evidence schema has no security finding field in [screaming-frog-crawl.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/quality/screaming-frog-crawl.schema.json:44). The recorded AHD report includes missing Content-Security-Policy on 166 URLs in [issues_overview_report.csv](/workspace/heartweb-data/Workflow-Lab/ahd-hausbesuch/STAGING-20260818-001/evidence/step-1/screaming-frog/run-ahd-step1-crawl-004/issues_overview_report.csv:22), but the Step 1 evidence cannot represent, disposition, or trend that result.

Recommended follow-up: Add versioned security finding categories and disposition rules to the crawl contract. Keep them advisory for Step 1 unless policy identifies a specific blocking condition.

## Positive Controls Observed

- The inventory contract fixes the Step 1 identity, canonical serialization, evidence references, 3 to 8 pillar range, and 8 to 15 cluster range in [step-1-topic-inventory.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-1-topic-inventory.schema.json:7), [step-1-topic-inventory.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-1-topic-inventory.schema.json:19), and [step-1-topic-inventory.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-1-topic-inventory.schema.json:37).
- The preflight binds the Step 0 approval and predecessor release to the current tenant, artifact, hash, and approval time window in [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:260). It also rejects a prompt-created Gate 1 approval in [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1_preflight/validator.py:436).
- No P0 finding was identified in the audited Step 1 Foundation implementation.

## Overall Verdict

REQUEST_CHANGES
