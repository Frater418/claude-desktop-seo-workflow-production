# Sprint 5 Operator Experience Specification

**Author:** Raphael Rechberger
**Date:** 2026-08-20
**Status:** Mandatory user correction for Sprint 5 completion

## Product Judgment

The current `?mode=demo` interface is only a structural prototype. It is not an acceptable final Operator Console.

It currently behaves too much like a descriptive document:

- too many explanatory text cards
- too much English copy
- too much internal system terminology
- too little direct work interaction
- weak information hierarchy
- no convincing daily operator workspace

Sprint 5 is complete only when the application feels and functions like professional workflow software for an SEO operator.

## Single Admin User

This product has exactly one interface role in the current scope: the Heartweb Admin Operator.

The Admin Operator performs the complete workflow from briefing intake through final handoff. Do not create separate dashboards, navigation, permissions or workspaces for copywriters, developers, reviewers, managers or customers.

Copywriters, developers and Notion operators do not log into this application. They receive exported files, task lists or later Notion records. Assignment fields are handoff metadata only, not a reason to build role-based product behavior.

The interface must help the Admin Operator answer immediately:

1. Which customer project am I working on?
2. Which workflow step is active?
3. What is blocked or awaiting review?
4. What output do I need to inspect or edit?
5. What is the next legal action?
6. What must I do before the workflow can continue?
7. What can I export or hand off now?

Do not add multi-user administration, role switching, access control screens, team inboxes or separate contributor experiences to Sprint 5.

## Language

- Default visible interface language: German.
- Use plain operational German.
- English is allowed only for unavoidable technical names, file names, schema names or external product names.
- Technical English belongs in secondary technical details, not in the main workflow.

## Information Hierarchy

### Primary visible information

- customer and project
- workflow step and status
- next permitted action
- open blocker
- assigned task, owner and deadline
- current artifact and revision
- machine-gate result
- human review state
- export or handoff readiness

### Secondary information

- evidence summary
- source links needed for the current decision
- revision history
- validation findings
- dependencies and escalation path

### Technical details only

- tenant, project, run and event IDs
- hashes and storage keys
- raw JSON
- raw API routes
- provider session IDs
- model routing
- Context Package internals
- idempotency keys
- event payloads
- simulator transport details
- diagnostic logs

Do not show generic internet information merely because it exists. Show external research or evidence only when it is directly relevant to the operator's current decision.

## Required Application Shell

The final Operator Console must use a real work-oriented application structure.

### Left navigation

- Projects
- Workflow
- Tasks
- Artifacts
- Reviews and approvals
- Delivery and export

### Project header

- project name
- customer
- current step
- overall progress
- active blocker count
- current owner
- next action

### Main work area

The center of the screen is reserved for the task the operator is currently performing:

- briefing intake
- artifact review
- artifact editing
- revision comparison
- gate report
- task resolution
- approval decision
- delivery preview

### Context and evidence panel

Use a collapsible side panel or drawer for:

- relevant evidence
- findings
- dependencies
- revision lineage
- technical details

### Persistent action area

The currently permitted actions must remain clear and close to the work:

- Start next step
- Save as new revision
- Request revision
- Request input
- Approve
- Reject
- Escalate
- Request waiver
- Export checkpoint
- Prepare handoff

Disabled actions must state the exact blocker. Do not display disabled preview buttons without explaining how the operator unlocks them.

## Required Workflows

### Project intake

- upload or paste a Markdown briefing
- review extracted project fields
- correct fields before acceptance
- accept project intake
- see Step 0 readiness

### Workflow operation

- see the current step and next legal step
- inspect required inputs and missing items
- start the step through a typed command
- see progress and result
- see machine-gate report
- move to human review only when ready

### Artifact work

- open the current artifact in a readable format
- edit a draft in a real editor
- save only as a new immutable revision
- compare old and new revision
- re-run validation
- never overwrite a released artifact

### Task work

- use a compact sortable and filterable task queue
- filter by status, owner, priority, deadline and workflow step
- open task detail without losing queue context
- see required resolution and dependency

### Review and approval

- review exact artifact revision and gate evidence
- choose a permitted decision
- preview the concrete consequence
- explicitly confirm the command
- read back canonical state after submission

### Delivery

- preview included and missing handoff items
- open the local project folder
- download checkpoint ZIP
- download final handoff ZIP
- download copywriter package
- download developer package
- download manual Notion import pack

## Visual and Interaction Standard

Use established professional workflow products as quality references for interaction density and clarity, not as visual copies:

- Linear for task and status handling
- Notion for readable structured content
- Contentful or modern CMS tools for artifact editing
- professional operations dashboards for project and gate visibility

Avoid:

- long explanatory paragraphs as the main UI
- large stacks of passive cards
- raw JSON as a primary workspace
- decorative dashboard metrics without an operator action
- duplicated status explanations
- presentation content mixed into daily task execution
- developer vocabulary in primary labels

## Acceptance Tests

Sprint 5 frontend completion requires task-based browser QA, not only visual overflow checks.

A trained operator must be able to complete these tasks without technical documentation:

1. identify the active project, step, blocker and next action within ten seconds
2. open the current task and understand its required resolution
3. open and edit a draft artifact
4. save and compare a new revision
5. inspect a gate report
6. request a revision
7. approve an eligible artifact
8. understand why an illegal action is blocked
9. locate the copywriter or developer handoff
10. export a checkpoint package

Verify desktop, tablet and mobile. Desktop is the primary productivity surface. Mobile must support review and status work but does not need to reproduce every dense desktop editing interaction.

## Authority Boundary

This specification changes the operator experience, not the domain architecture.

- The Local Core remains authoritative.
- Transition Service remains the only workflow-status authority.
- UI actions send typed commands.
- No frontend state may claim canonical success before API readback.
- Existing artifact, revision, gate, event and delivery contracts remain authoritative.

## Completion Evidence

The final Sprint 5 audit must include:

- screenshots of the real work-oriented shell
- task-based browser QA evidence
- German interface copy review
- operator journey test from intake through handoff
- explicit comparison against the rejected descriptive demo pattern

The final audit must not approve Sprint 5 merely because components exist, tests are green or the layout has no overflow.
