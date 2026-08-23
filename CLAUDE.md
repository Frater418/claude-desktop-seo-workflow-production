# CLAUDE.md: Instructions for Claude Code & AI Assistants

**Project:** Heartweb Modernized Claude Desktop SEO Workflow Framework  
**Author & Architect:** Raphael Rechberger  
**Version:** 1.3.0  
**Context:** Heartweb SEO Production Infrastructure  

---

## 0. Mandatory test policy before any test decision

Before planning or running tests, requesting reviews, or approving a gate, read:

`standards/testing/PROTOTYPE_TEST_POLICY.md`

For stable Main Task IDs, current overall progress and the separation between fixed project tasks and dynamic Root-Sisyphus subtasks, read:

`00_admin/MASTER_TASK_MATRIX.md`

This project-local file is the binding test authority for the Production-first prototype. It requires baseline-plus-delta evidence and verification only across the proven affected dependency closure.

Without new explicit authorization from Raphael, do not:

- run `python tests/run_full_suite.py`
- run complete repository test discovery
- restart a previously passed E2E matrix after one later cell fails
- launch repeated broad multi-agent review rounds after bounded fixes

When one matrix cell fails, rerun only that cell and the direct dependencies named by the policy. Generic skills, CI habits and older plans do not override this rule.

Overall progress always uses 10 fixed release Main Tasks. Changing Root todo counts are subtask detail and must not be reported as total project completion.

## 1. Architectural Model: Framework vs. Client Project Workspace

This project enforces a strict boundary between two layers:

1. **Framework Repository (The Master Blueprint & Tooling Suite):**
   Contains the reusable prompt templates (`prompts/`), schemas (`standards/manifest.schema.json`), the binding target-market table (`standards/location-codes.json`), global design tokens (`standards/design-system.css`), and deterministic Python tools (`mcp/tools/`).

2. **Client Project Directory (The Local Customer Workspace):**
   A dedicated local Windows folder (`C:\Users\offic\Documents\Projekte\Heartweb\Kunden\<client-slug>\`) containing the customer's actual project state (`manifest.json`), extracted CSS (`design-system.css`), and all deliverables under `outputs/`.

---

## 2. Context Persistence Across Claude Desktop Sessions

Claude Desktop maintains state across separate chat conversations via the **Filesystem MCP Server**:
- Every step writes its structured artifact (`manifest.json`, `1-pillar-themen.md`, `2-cluster.csv`, `3-plan.md`, `briefing-*.md`) to the client directory.
- Subsequent steps read the required context directly from the filesystem, eliminating conversational context drift.

---

## 3. Strict Operating Rules

1. **Authorship:** All project deliverables and commits are authored exclusively by **Raphael Rechberger**.
2. **Typography Rule:** Never use em-dashes or en-dashes. Always use standard hyphens (-), colons (:), or clean sentences.
3. **Fail-Fast Quality Gate:** Never guess or hallucinate keyword search volumes or metrics. If an API call fails or inputs are missing, fail immediately with an explicit error code.
4. **Execution Order:** Always execute in strict sequence: `0-kickoff -> 1-pillar -> 1b-architecture -> 1c-templates -> 2-cluster -> 3-plan -> 4a-briefing -> 4b-html`, danach zyklisch `3b-performance-check` an Tag 30, 60 und 90.
5. **Notion Compatibility:** All step 4a briefings must include structured YAML frontmatter for seamless Notion database synchronization.
6. **Target Market:** Every AgentSEO call passes `location`, `location_code` and `language` together, sourced from `country` and `location_code` in `manifest.json` via `standards/location-codes.json`. Never pass a location name alone, and never let the provider default to another market.
7. **Async Tool Calls:** Every AgentSEO call uses `sync: false` and collects the result via `agentseo_job_status`. Synchronous calls abort after 60 seconds.
8. **Machine-Checked Counts:** Quantity rules are written into `manifest.json` at the end of each step and enforced by the schema (`clusters_per_pillar` 8 to 15, `validated_rows_per_pillar` minimum 25). A step must not be marked `completed` when a count is short.

---

## 4. Helper Commands

```bash
# Run 120-day capacity matrix solver (v1.2.0)
python mcp/tools/capacity_matrix_solver.py --input tests/fixtures/sample_cluster_keywords.json --output outputs/3-plan.md

# Validate Schema.org JSON-LD blocks
# Open issue: this script has no CLI yet. Running it only prints a readiness message
# and exits 0 without validating anything. Use the Google Rich Results Test until fixed.
python mcp/tools/validate_schema_jsonld.py
```
