# CLAUDE.md: Instructions for Claude Code & AI Assistants

**Project:** Heartweb Modernized Claude Desktop SEO Workflow  
**Author & Architect:** Raphael Rechberger  
**Version:** 1.2.0  
**Context:** Heartweb SEO Production Infrastructure  

---

## 1. Project Overview

This repository contains the production framework for scaling SEO rollouts (Pillars, Clusters, 120-day roadmaps, Local Landing Pages).
It bridges local Claude Desktop workflows with structured database architectures (Notion) and automated MCP tools (AgentSEO).

---

## 2. Directory Navigation

- `prompts/`: Standardized XML workflow prompts (Steps 0 to 4b).
- `standards/`: JSON schemas (`manifest.schema.json`), CSS design tokens (`design-system.css`), and filename contracts.
- `mcp/`: Configuration template (`claude_desktop_config.template.json`), Python tools (`capacity_matrix_solver.py`, `validate_schema_jsonld.py`), and JSON tool contracts (`mcp/tool-contracts/`).
- `docs/`: Operations manual, review comparison, ADR decision log, quality gates, copywriter guidelines, and Jesse walkthrough memo.
- `tests/`: Acceptance tests and fixtures (`sample_manifest.json`, `sample_cluster_keywords.json`).

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
# Run 120-day capacity matrix solver
python mcp/tools/capacity_matrix_solver.py --input tests/fixtures/sample_cluster_keywords.json

# Validate Schema.org JSON-LD blocks
python mcp/tools/validate_schema_jsonld.py
```
