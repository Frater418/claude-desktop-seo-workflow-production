# Documentation Lifecycle Reconciliation

**Author:** Raphael Rechberger
**Date:** 2026-08-26
**Scope:** All 18 `docs/` entries in `00_admin/repository-index/DOCUMENT_REGISTRY.json`

## Result

| Lifecycle | Count |
|---|---:|
| `current_authority` | 4 |
| `current_strategy` | 2 |
| `historical` | 7 |
| `superseded` | 3 |
| `evidence` | 2 |
| **Total** | **18** |

No document was deleted, renamed or silently promoted. Current documents were reconciled with Project State and active Decisions. Historical and superseded Markdown files retain their original content with visible lifecycle banners. Historical status metadata is labeled `Status at capture`. Binary PDFs remain immutable Evidence and are classified through the registry and generated docs index. The historical HTML map now carries a visible lifecycle notice.

## Complete disposition

| Path | Lifecycle | Authority | Default retrieval | Reconciliation action |
|---|---|---:|---|---|
| `docs/00-current-production-architecture.md` | `current_authority` | 94 | yes | Updated current implementation, CL acceptance boundary, M10 remainder and onboarding read order |
| `docs/01-review-abgleich.md` | `historical` | 18 | no | Existing historical banner retained; original status labeled as capture-time status |
| `docs/02-research-und-technische-spezifikation.md` | `historical` | 18 | no | Existing historical banner retained; original status labeled as capture-time status |
| `docs/03-sprint-plan.md` | `superseded` | 15 | no | Existing supersession banner retained; original status labeled as capture-time status |
| `docs/04-entscheidungslog.md` | `superseded` | 15 | no | Current authority remains `00_admin/DECISIONS.md`; active-at-capture metadata clarified |
| `docs/05-human-in-the-loop.md` | `historical` | 18 | no | Existing historical banner points to current gate and Transition authorities |
| `docs/06-pilot-abnahme-checkliste.md` | `historical` | 18 | no | Existing historical banner points to current release and acceptance authorities |
| `docs/07-geo-architecture-specification.md` | `current_strategy` | 76 | yes | Lifecycle updated from active restoration to real-output verification after local PQ-4 closure |
| `docs/07-geo-research-und-copywriter-guidelines.pdf` | `evidence` | 25 | no | Binary Evidence retained unchanged and indexed beside the current Markdown strategy |
| `docs/08-geo-sprint-plan-and-multi-agent-orchestration.md` | `superseded` | 15 | no | Existing supersession banner retained; original status labeled as capture-time status |
| `docs/09-extension-and-evolution-guide.md` | `current_authority` | 90 | yes | Updated deterministic Onboarding Reference generation contract |
| `docs/betriebshandbuch-claude-desktop.md` | `historical` | 18 | no | Old Claude Desktop operating model retained; active-at-capture metadata clarified |
| `docs/copywriter-handoff-guidelines.md` | `current_strategy` | 76 | yes | Current human-Copywriter and Notion boundary reviewed and retained |
| `docs/integrations/n8n-orchestration-model.md` | `current_authority` | 82 | yes | Clarified that n8n is absent from first local release and simulator output is contract Evidence only |
| `docs/integrations/notion-operating-model.md` | `current_authority` | 82 | yes | Current one-way handoff and first-release manual import boundary reviewed and retained |
| `docs/jesse-walkthrough-memo.md` | `historical` | 12 | no | Stakeholder snapshot retained; original publication status labeled as capture-time status |
| `docs/jesse-walkthrough-memo.pdf` | `evidence` | 10 | no | Binary stakeholder Evidence retained unchanged and excluded from default retrieval |
| `docs/operator-workflow-function-map.html` | `historical` | 15 | no | Visible historical Sprint-5 notice and current authority links added |

## Generated view

`docs/INDEX.md` is generated from the registry after source reconciliation. Its lifecycle groups and content hashes must be regenerated and pass `python scripts/build_repository_index.py --check` before the final source commit is integrated into `master`.

## Acceptance boundary

This reconciliation closes documentation lifecycle ambiguity. It does not regenerate historical PDFs, claim M10 completion or change Production Acceptance.
