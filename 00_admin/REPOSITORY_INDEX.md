# Repository authority index

**Author:** Raphael Rechberger
**Indexed snapshot:** `703392570aeb76d5fe6a81a8f00b8c72042ee6d1`
**Generated:** deterministic from repository sources

## Start here

1. [`ONBOARDING_REFERENCE.md`](ONBOARDING_REFERENCE.md)
2. [`SESSION_BOOTSTRAP.md`](SESSION_BOOTSTRAP.md)
3. [`PROJECT_STATE.md`](PROJECT_STATE.md)
4. [`DECISIONS.md`](DECISIONS.md)
5. Select the active plan for the current task from [`.hermes/plans/INDEX.md`](../.hermes/plans/INDEX.md)
6. Before test or review decisions, read [`standards/testing/PROTOTYPE_TEST_POLICY.md`](../standards/testing/PROTOTYPE_TEST_POLICY.md)
7. Use `repository-index/DOCUMENT_REGISTRY.jsonl` for filtered RAG ingestion

## Default retrieval set

| Document | Lifecycle | Authority | Default |
|---|---|---:|---|
| [`00_admin/PROJECT_STATE.md`](../00_admin/PROJECT_STATE.md) | `current_authority` | 100 | yes |
| [`00_admin/MASTER_TASK_MATRIX.md`](../00_admin/MASTER_TASK_MATRIX.md) | `current_authority` | 99 | yes |
| [`00_admin/DECISIONS.md`](../00_admin/DECISIONS.md) | `current_authority` | 98 | yes |
| [`standards/testing/PROTOTYPE_TEST_POLICY.md`](../standards/testing/PROTOTYPE_TEST_POLICY.md) | `current_authority` | 97 | yes |
| [`AGENTS.md`](../AGENTS.md) | `current_authority` | 96 | yes |
| [`.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md`](../.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md) | `active_plan` | 95 | yes |
| [`CLAUDE.md`](../CLAUDE.md) | `current_authority` | 94 | yes |
| [`docs/00-current-production-architecture.md`](../docs/00-current-production-architecture.md) | `current_authority` | 94 | yes |
| [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`](../.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md) | `active_plan` | 92 | yes |
| [`.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`](../.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md) | `active_plan` | 92 | yes |
| [`.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md`](../.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md) | `active_plan` | 90 | yes |
| [`docs/09-extension-and-evolution-guide.md`](../docs/09-extension-and-evolution-guide.md) | `current_authority` | 90 | yes |
| [`.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md`](../.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md) | `active_plan` | 88 | yes |
| [`.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md`](../.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md) | `current_strategy` | 88 | yes |
| [`00_admin/DEFERRED_INTEGRATION_BACKLOG.md`](../00_admin/DEFERRED_INTEGRATION_BACKLOG.md) | `current_strategy` | 88 | yes |
| [`00_admin/POST_RELEASE_BACKLOG.md`](../00_admin/POST_RELEASE_BACKLOG.md) | `current_strategy` | 87 | yes |
| [`README.md`](../README.md) | `current_authority` | 86 | yes |
| [`00_admin/repository-index/INTEGRATION_CHECKLIST.md`](../00_admin/repository-index/INTEGRATION_CHECKLIST.md) | `current_strategy` | 84 | yes |
| [`docs/integrations/n8n-orchestration-model.md`](../docs/integrations/n8n-orchestration-model.md) | `current_authority` | 82 | yes |
| [`docs/integrations/notion-operating-model.md`](../docs/integrations/notion-operating-model.md) | `current_authority` | 82 | yes |
| [`docs/07-geo-architecture-specification.md`](../docs/07-geo-architecture-specification.md) | `current_strategy` | 76 | yes |
| [`docs/copywriter-handoff-guidelines.md`](../docs/copywriter-handoff-guidelines.md) | `current_strategy` | 76 | yes |

## Lifecycle counts

- `active_plan`: 5
- `current_authority`: 123
- `current_strategy`: 8
- `evidence`: 177
- `historical`: 8
- `superseded`: 12

## Reconciliation warnings

- None

## Retrieval rule

Filter by lifecycle and authority before semantic ranking. Historical, superseded and evidence records are opt-in only.
