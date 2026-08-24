# Documentation branch integration checklist

**Author:** Raphael Rechberger
**Status:** Binding integration gate
**Updated:** 2026-08-22
**Branch:** `docs/repository-authority-index-2026-08-22`

## Purpose

The parallel branch starts from WIP commit `7c844ba1`. It must not be merged directly into the later Feature line without refreshing volatile facts and resolving documentation changes made during Sprint 5E, diagnostics and prompt restoration.

## Preconditions

- active Sisyphus writing wave is complete
- stable Feature commit exists
- Git index is clean
- Production-first scope is unchanged or a new Decision supersedes it
- no unresolved P0/P1 documentation contradiction exists
- Raphael authorizes the integration attempt

## Integration sequence

1. Record stable Feature commit SHA.
2. Fetch current remote refs.
3. Update this branch from the stable Feature commit using the approved Git strategy.
4. Resolve only genuine content conflicts. Preserve active Product State and Decisions from the stable Feature line.
5. Re-read:
   - `00_admin/PROJECT_STATE.md`
   - `00_admin/DECISIONS.md`
   - `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`
   - `00_admin/POST_RELEASE_BACKLOG.md`
   - current Sprint-5E and prompt-restoration evidence
6. Refresh volatile status in README, Project State, CHANGELOG and current architecture.
7. Reclassify every new plan, doc, audit package and research source.
8. Confirm AGENTS and CLAUDE still match active global rules.
9. Preserve and refresh `standards/testing/PROTOTYPE_TEST_POLICY.md`, `00_admin/MASTER_TASK_MATRIX.md` and `00_admin/MASTER_TASK_MATRIX.json` from the stable Feature line.
10. Run `python scripts/build_repository_index.py`.
11. Run `python scripts/build_repository_index.py --check`.
12. Run the focused documentation-registry tests required by the binding prototype test policy.
13. Run scoped Python compile checks and `git diff --check`.
14. Scan current Default-Retrieval Markdown links.
15. Verify no Em Dash or En Dash was introduced.
16. Verify historical and superseded docs remain opt-in.
17. Inspect `00_admin/REPOSITORY_INDEX.md`, `docs/INDEX.md` and `.hermes/plans/INDEX.md` manually.
18. Compare active Sisyphus and documentation worktrees for unintended cross-writes.
19. Request Raphael review and approval.
20. Commit, push or merge only after explicit authorization.

## Required refresh fields

- current branch and release state
- current Sprint-5E completion
- current diagnostic and prompt-restoration state
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
- active Feature state would be overwritten by the older WIP snapshot
- customer data, secrets or absolute private paths enter the registry
- active Sisyphus index or worktree changes unexpectedly

## Acceptance

Integration is acceptable only when the refreshed branch provides one correct read path for new sessions, retains historical evidence without authority conflict and passes all deterministic index and documentation gates.
