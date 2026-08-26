# Repository master integration checklist

**Author:** Raphael Rechberger
**Status:** Binding integration gate
**Updated:** 2026-08-26
**Authority:** DEC-0031 and DEC-0032

## Purpose

This checklist governs the explicitly authorized consolidation of the complete verified repository state into `master`. It protects source history, current Product State, prompt versions, generated authority views and the later fresh-clone continuation. The Git baseline is not Production Acceptance.

## Preconditions

- mutable Console and Gateway processes are frozen during repository finalization
- a verified external recovery snapshot contains all refs and relevant Working Tree files
- every tracked and untracked path has an explicit repository or external-only disposition
- unique branch content has a path-by-path reconciliation report
- no unresolved P0/P1 repository-integrity or authority contradiction remains
- DEC-0031 provides Raphael's explicit commit, merge, push, branch cleanup and fresh-clone authorization

## Integration sequence

1. Record current branch, local refs, remote refs, HEAD, status and worktrees.
2. Verify the external recovery snapshot and Git bundle before any history change.
3. Exclude only confirmed local-only or regenerable paths from staging.
4. Complete the M08 path reconciliation and preserve its tip in the final graph without replacing the current tree.
5. Reconcile Project State, Decisions, task matrices, backlogs and current architecture.
6. Classify all docs, prompts, Step agents, worker profiles, tool policies, plans, audits and research sources.
7. Commit explicitly staged authored implementation, tests and documentation.
8. Integrate the reconciled M08 tip with a no-tree-change merge commit.
9. Generate `ONBOARDING_REFERENCE.md`, registries, bootstrap and lifecycle indexes from the authored-source parent commit.
10. Run repository-index write and check modes and focused registry tests.
11. Run the affected backend, contract and Console test closure plus the Production build.
12. Run secret scanning, forbidden-dash scanning and `git diff --check`.
13. Run `hermes verify --json` and preserve the exact result.
14. Inspect the generated onboarding, repository, docs, plans, audits and research indexes.
15. Fast-forward local `master` to the verified consolidation commit.
16. Push `master` without force and read back the exact remote SHA and tree.
17. Delete a non-master branch only after its tip is proven reachable from final `master`; then verify local and remote branch lists.
18. Move the old repository directory to the external archive without deleting it.
19. Clone remote `master` freshly at the canonical path and verify HEAD, tree, status and generated-index check.
20. Create and push `feature/production-workflow-continuation` from that exact verified `master` commit.

## Required refresh fields

- current local and remote branch SHAs and reachability proof
- current M10, released Step-0 and open Step-1 state
- current diagnostics, prompt versions, Step agents and tool-policy bindings
- final test evidence references
- first real customer output status
- active decisions and supersession
- active and post-release plan classification
- generated registry source commit

## Hard failures

Stop integration when:

- registry drift remains
- current documents contain broken relative links
- an unclassified document remains
- a historical document appears in Default Retrieval
- AGENTS, CLAUDE, README or Project State contradict active Decisions
- current source state would be overwritten by the older M08 snapshot
- customer data, secrets or absolute private paths enter the registry
- source files change unexpectedly after the verified snapshot or during final staging
- any retired branch tip is not reachable from final `master`
- local, remote or fresh-clone `master` SHAs disagree

## Acceptance

Integration is acceptable only when final remote `master` provides one correct generated read path for new sessions, retains historical Evidence without authority conflict, includes every reconciled branch tip, passes the affected verification closure and is reproduced by a clean clone. This acceptance applies to repository consolidation only, not Production Acceptance.
