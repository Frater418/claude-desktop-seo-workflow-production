# CLAUDE.md: Instructions for Claude Code & AI Assistants

**Project:** Heartweb Modernized Claude Desktop SEO Workflow Framework  
**Author & Architect:** Raphael Rechberger  
**Version:** 1.2.0  
**Context:** Heartweb SEO Production Infrastructure  

---

## 1. Architectural Model: Framework vs. Client Project Workspace

This project enforces a strict boundary between two layers:

1. **Framework Repository (The Master Blueprint & Tooling Suite):**
   Contains the reusable prompt templates (`prompts/`), schemas (`standards/manifest.schema.json`), global design tokens (`standards/design-system.css`), and deterministic Python tools (`mcp/tools/`).

2. **Client Project Directory (The Local Customer Workspace):**
   A dedicated local Windows folder (e.g. `C:\Users\offic\Documents\Projekte\Kunden\<client-slug>\`) containing the customer's actual project state (`manifest.json`), extracted CSS (`design-system.css`), and all deliverables under `outputs/`.

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
4. **Execution Order:** Always execute in strict sequence: `0-kickoff -> 1-pillar -> 1b-architecture -> 1c-templates -> 2-cluster -> 3-plan -> 4a-briefing -> 4b-html`.
5. **Notion Compatibility:** All step 4a briefings must include structured YAML frontmatter for seamless Notion database synchronization.

---

## 4. Helper Commands

```bash
# Run 120-day capacity matrix solver (v1.2.0)
python mcp/tools/capacity_matrix_solver.py --input tests/fixtures/sample_cluster_keywords.json --output outputs/3-plan.md

# Validate Schema.org JSON-LD blocks
python mcp/tools/validate_schema_jsonld.py
```
