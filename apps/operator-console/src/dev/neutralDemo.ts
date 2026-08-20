export const workflowStates = {
  released: "released",
  awaitingGate: "awaiting gate",
  blocked: "blocked",
  locked: "locked",
  notDue: "not_due",
} as const

export type WorkflowState = (typeof workflowStates)[keyof typeof workflowStates]

export type WorkflowStep = {
  readonly id: string
  readonly label: string
  readonly objective: string
  readonly status: WorkflowState
  readonly statusSummary: string
  readonly inputs: readonly string[]
  readonly tools: readonly string[]
  readonly outputSummary: string
  readonly gates: readonly string[]
  readonly machineGate: string
  readonly humanGate: string
  readonly findings: readonly string[]
  readonly contextSummary: string
  readonly workerProfile: string
  readonly promptVersion: string
  readonly llmState: string
  readonly checklist: readonly string[]
  readonly actionPreview: string
  readonly technicalId: string
}

export type NeutralDemoProject = {
  readonly id: string
  readonly title: string
  readonly owner: string
  readonly targetDate: string
  readonly currentStep: string
  readonly progress: string
  readonly blockerCount: number
  readonly taskCount: number
  readonly reviewCount: number
  readonly artifactCount: number
  readonly nextAction: string
  readonly integrations: readonly string[]
  readonly steps: readonly WorkflowStep[]
  readonly sideflow: WorkflowStep
}

export const neutralDemoProject: NeutralDemoProject = {
  id: "project-neutral-031",
  title: "Northwind Facilities rollout",
  owner: "Operations lead",
  targetDate: "18 September 2026",
  currentStep: "1b: Information architecture",
  progress: "2 of 8 initial-route steps released",
  blockerCount: 1,
  taskCount: 6,
  reviewCount: 1,
  artifactCount: 4,
  nextAction: "Resolve the navigation conflict, then submit the architecture gate for review.",
  integrations: ["Notion simulated", "n8n simulated"],
  steps: [
    {
      id: "0",
      label: "Project intake",
      objective: "Establish the validated project record and operating scope.",
      status: workflowStates.released,
      statusSummary: "Released after the intake completeness gate.",
      inputs: ["Approved project brief", "Operating scope"],
      tools: ["Project contract validator", "Context builder"],
      outputSummary: "Validated project record and first workflow run are available.",
      gates: ["Intake completeness passed", "Human intake review complete"],
      machineGate: "Intake completeness passed",
      humanGate: "Human intake review complete",
      findings: ["No open findings"],
      contextSummary: "Immutable intake and approved operating scope.",
      workerProfile: "Workflow intake worker",
      promptVersion: "0-kickoff v2",
      llmState: "Completed",
      checklist: ["Scope confirmed", "Identifiers assigned", "Gate released"],
      actionPreview: "Start is unavailable because this released step is historical.",
      technicalId: "step-neutral-000",
    },
    {
      id: "1",
      label: "Topic inventory",
      objective: "Create an evidence-grounded inventory of core themes.",
      status: workflowStates.released,
      statusSummary: "Released with the topic evidence package attached.",
      inputs: ["Validated intake", "Source evidence"],
      tools: ["Topic inventory worker", "Evidence validator"],
      outputSummary: "Approved theme inventory is ready for architecture work.",
      gates: ["Evidence coverage passed", "Human topic review complete"],
      machineGate: "Evidence coverage passed",
      humanGate: "Human topic review complete",
      findings: ["One duplicate theme was merged before release"],
      contextSummary: "Released intake, evidence references, and prior findings.",
      workerProfile: "SEO research worker",
      promptVersion: "1-pillar-identification v2",
      llmState: "Completed",
      checklist: ["Evidence verified", "Duplicates resolved", "Gate released"],
      actionPreview: "Start is unavailable because this released step is historical.",
      technicalId: "step-neutral-010",
    },
    {
      id: "1b",
      label: "Information architecture",
      objective: "Map the approved themes into a usable site structure.",
      status: workflowStates.awaitingGate,
      statusSummary: "Awaiting the architecture gate after one open navigation conflict is resolved.",
      inputs: ["Released topic inventory", "Approved project scope", "Navigation constraints"],
      tools: ["Architecture worker", "URL conflict checker", "Link graph validator"],
      outputSummary: "Draft sitemap, URL schema, and internal-link tree are prepared for review.",
      gates: ["Topic coverage passed", "URL conflict requires resolution", "Human architecture review pending"],
      machineGate: "Topic coverage passed; URL conflict requires resolution",
      humanGate: "Human architecture review pending",
      findings: ["Blocked: two proposed navigation labels would resolve to the same route"],
      contextSummary: "Released topic inventory, route constraints, and current gate findings.",
      workerProfile: "Information architecture worker",
      promptVersion: "1b-site-architecture v2",
      llmState: "Awaiting human gate",
      checklist: ["Coverage checked", "Conflict assigned", "Review package prepared"],
      actionPreview: "Approval remains a Review Center preview until the conflict is resolved.",
      technicalId: "step-neutral-011",
    },
    {
      id: "1c",
      label: "Template system",
      objective: "Translate approved architecture into reusable page-template inputs.",
      status: workflowStates.blocked,
      statusSummary: "Blocked until the information architecture gate releases.",
      inputs: ["Released information architecture", "Brand source material"],
      tools: ["Template worker", "Accessibility checker"],
      outputSummary: "No output can be created before the predecessor gate releases.",
      gates: ["Predecessor release required", "Human template review not started"],
      machineGate: "Predecessor release required",
      humanGate: "Human template review not started",
      findings: ["Blocked by the pending 1b gate"],
      contextSummary: "Will bind the released architecture revision only.",
      workerProfile: "Template system worker",
      promptVersion: "1c-pillar-template v2",
      llmState: "Not started",
      checklist: ["Wait for 1b release", "Build context package", "Run template gates"],
      actionPreview: "Start remains disabled until the predecessor releases.",
      technicalId: "step-neutral-012",
    },
    {
      id: "2",
      label: "Keyword evidence",
      objective: "Collect validated market evidence for the approved architecture.",
      status: workflowStates.locked,
      statusSummary: "Locked until the template system releases.",
      inputs: ["Released templates", "Market configuration"],
      tools: ["Provider gateway", "Coverage validator"],
      outputSummary: "No provider request is authorized yet.",
      gates: ["Predecessor release required", "Geo validation not started"],
      machineGate: "Predecessor release required",
      humanGate: "Human keyword review not started",
      findings: ["No findings because the step is locked"],
      contextSummary: "Will bind only released predecessor evidence.",
      workerProfile: "Keyword research worker",
      promptVersion: "2-cluster-research v2",
      llmState: "Not started",
      checklist: ["Wait for 1c release", "Validate provider access", "Collect evidence"],
      actionPreview: "Start remains disabled until the predecessor releases.",
      technicalId: "step-neutral-020",
    },
    {
      id: "3",
      label: "Rollout plan",
      objective: "Build the capacity-checked operating plan.",
      status: workflowStates.locked,
      statusSummary: "Locked until keyword evidence releases.",
      inputs: ["Released keyword evidence", "Capacity constraints"],
      tools: ["Capacity solver", "Link graph validator"],
      outputSummary: "No plan is available before verified evidence exists.",
      gates: ["Predecessor release required", "Capacity validation not started"],
      machineGate: "Predecessor release required",
      humanGate: "Human plan review not started",
      findings: ["No findings because the step is locked"],
      contextSummary: "Will bind the verified evidence revision and capacity policy.",
      workerProfile: "Planning worker",
      promptVersion: "3-120-day-plan v2",
      llmState: "Not started",
      checklist: ["Wait for evidence", "Run solver", "Review plan"],
      actionPreview: "Start remains disabled until the predecessor releases.",
      technicalId: "step-neutral-030",
    },
    {
      id: "4a",
      label: "Content briefing",
      objective: "Prepare a reviewable editorial briefing from the released plan.",
      status: workflowStates.locked,
      statusSummary: "Locked until the rollout plan releases.",
      inputs: ["Released rollout plan", "Approved research evidence"],
      tools: ["Briefing worker", "Schema checker"],
      outputSummary: "No briefing is available before prioritization is released.",
      gates: ["Predecessor release required", "Human briefing review not started"],
      machineGate: "Predecessor release required",
      humanGate: "Human briefing review not started",
      findings: ["No findings because the step is locked"],
      contextSummary: "Will bind a released priority item and evidence package.",
      workerProfile: "Editorial briefing worker",
      promptVersion: "4a-content-briefing v2",
      llmState: "Not started",
      checklist: ["Wait for plan", "Select item", "Validate briefing"],
      actionPreview: "Start remains disabled until the predecessor releases.",
      technicalId: "step-neutral-040a",
    },
    {
      id: "4b",
      label: "Page specification",
      objective: "Prepare the implementation-ready page specification.",
      status: workflowStates.locked,
      statusSummary: "Locked until the content briefing releases.",
      inputs: ["Released briefing", "Approved template system"],
      tools: ["Page specification worker", "HTML validator"],
      outputSummary: "No page specification is available before briefing approval.",
      gates: ["Predecessor release required", "Human staging review not started"],
      machineGate: "Predecessor release required",
      humanGate: "Human staging review not started",
      findings: ["No findings because the step is locked"],
      contextSummary: "Will bind the released briefing and template revision.",
      workerProfile: "Page implementation worker",
      promptVersion: "4b-landingpage-html v2",
      llmState: "Not started",
      checklist: ["Wait for briefing", "Generate specification", "Run staging checks"],
      actionPreview: "Start remains disabled until the predecessor releases.",
      technicalId: "step-neutral-040b",
    },
  ],
  sideflow: {
    id: "3b",
    label: "Performance check",
    objective: "Review post-publication measurements and propose controlled adjustments.",
    status: workflowStates.notDue,
    statusSummary: "Not due until post-publication checkpoints are available.",
    inputs: ["Published baseline", "Day 30, 60, or 90 measurements"],
    tools: ["Measurement import", "Adjustment proposal worker"],
    outputSummary: "No adjustment proposal is permitted before a measurement checkpoint.",
    gates: ["Publication required", "Measurement completeness required"],
    machineGate: "Publication and measurement completeness required",
    humanGate: "Human adjustment review not started",
    findings: ["Not due: no post-publication measurement checkpoint exists"],
    contextSummary: "Will bind immutable source-plan and measured checkpoint evidence.",
    workerProfile: "Performance analysis worker",
    promptVersion: "3b-performance-check v2",
    llmState: "Not started",
    checklist: ["Wait for publication", "Import checkpoint", "Review adjustment"],
    actionPreview: "Start and approval remain disabled until a checkpoint is due.",
    technicalId: "step-neutral-031b",
  },
}

export const taskKinds = {
  missingInput: "missing input",
  blockerResolution: "blocker resolution",
  revisionRequest: "revision request",
  workflowDefect: "workflow defect",
  escalation: "escalation",
  waiverRequest: "waiver request",
} as const

export type TaskKind = (typeof taskKinds)[keyof typeof taskKinds]

export const taskSeverities = {
  critical: "critical",
  high: "high",
  medium: "medium",
} as const

export type TaskSeverity = (typeof taskSeverities)[keyof typeof taskSeverities]

export type DemoSourceLink = {
  readonly label: string
  readonly href: string
}

export const taskIds = {
  missingInput: "task-northwind-missing-input",
  routeConflict: "task-northwind-route-conflict",
  revisionRequest: "task-northwind-accessibility-revision",
  workflowDefect: "task-northwind-predecessor-defect",
  escalation: "task-northwind-route-escalation",
  waiverRequest: "task-northwind-evidence-waiver",
} as const

export type DemoTaskId = (typeof taskIds)[keyof typeof taskIds]

export type DemoTask = {
  readonly id: DemoTaskId
  readonly title: string
  readonly type: TaskKind
  readonly severity: TaskSeverity
  readonly status: string
  readonly ownerRole: string
  readonly assignee: string
  readonly dueDate: string
  readonly sourceStep: string
  readonly nextAction: string
  readonly dependency: string
  readonly routeClass: string
  readonly evidence: readonly string[]
  readonly remediationChecklist: readonly string[]
  readonly expectedResolution: string
  readonly escalationPath: string
  readonly sourceLinks: readonly DemoSourceLink[]
  readonly technical: {
    readonly taskId: string
    readonly correlationId: string
    readonly rawRoute: string
  }
}

export const demoTasks: Readonly<Record<DemoTaskId, DemoTask>> = {
  [taskIds.missingInput]: {
    id: taskIds.missingInput,
    title: "Confirm missing service-area input",
    type: taskKinds.missingInput,
    severity: taskSeverities.high,
    status: "awaiting project input",
    ownerRole: "Operations lead",
    assignee: "Project coordinator",
    dueDate: "21 August 2026",
    sourceStep: "0: Project intake",
    nextAction: "Capture the approved service-area contact and attach it to the intake record.",
    dependency: "Scope validation cannot continue while the regional service-area owner is unconfirmed.",
    routeClass: "input completeness route",
    evidence: ["Project brief identifies the service area but not its accountable contact.", "Intake completeness gate remains traceable to the missing owner."],
    remediationChecklist: ["Request the named service-area contact", "Record the approved scope owner", "Recheck intake completeness"],
    expectedResolution: "After the accountable contact is recorded, the intake record can be reviewed without changing the approved project scope.",
    escalationPath: "Operations lead to project sponsor if the accountable contact is not supplied by the due date.",
    sourceLinks: [{ label: "Project intake brief", href: "#northwind-project-intake" }],
    technical: {
      taskId: "operator-task-northwind-001",
      correlationId: "corr-northwind-intake-001",
      rawRoute: "/v1/tenants/northwind/projects/facilities/tasks/operator-task-northwind-001",
    },
  },
  [taskIds.routeConflict]: {
    id: taskIds.routeConflict,
    title: "Resolve duplicate primary navigation route",
    type: taskKinds.blockerResolution,
    severity: taskSeverities.critical,
    status: "assigned",
    ownerRole: "Information architecture owner",
    assignee: "Information architect",
    dueDate: "22 August 2026",
    sourceStep: "1b: Information architecture",
    nextAction: "Choose distinct primary labels before the architecture gate can proceed.",
    dependency: "The template system remains blocked until the architecture gate receives a conflict-free candidate.",
    routeClass: "navigation ownership conflict",
    evidence: ["Route checker found two proposed primary labels targeting one canonical destination.", "Topic coverage remains valid in the released predecessor."],
    remediationChecklist: ["Select one owner for the duplicate destination", "Rename the competing primary label", "Generate a fresh validation candidate"],
    expectedResolution: "A fresh architecture candidate can be reviewed with distinct route ownership and unchanged approved topic coverage.",
    escalationPath: "Information architecture owner to Operations lead, then project sponsor if ownership remains unresolved.",
    sourceLinks: [{ label: "Architecture review checklist", href: "#northwind-architecture-review" }, { label: "Released topic inventory", href: "#northwind-topic-inventory" }],
    technical: {
      taskId: "operator-task-northwind-002",
      correlationId: "corr-northwind-architecture-003",
      rawRoute: "/v1/tenants/northwind/projects/facilities/tasks/operator-task-northwind-002",
    },
  },
  [taskIds.revisionRequest]: {
    id: taskIds.revisionRequest,
    title: "Request revised accessibility route notes",
    type: taskKinds.revisionRequest,
    severity: taskSeverities.medium,
    status: "ready for review routing",
    ownerRole: "Accessibility review lead",
    assignee: "Information architect",
    dueDate: "23 August 2026",
    sourceStep: "1b: Information architecture",
    nextAction: "Prepare revision 4 notes after the duplicate route owner is selected.",
    dependency: "A revision cannot be requested until the route conflict has a human-owned resolution.",
    routeClass: "revision control route",
    evidence: ["Revision 3 retained accessibility notes alongside the rejected route candidate.", "The previous revision cannot be overwritten."],
    remediationChecklist: ["Use the released predecessor as context", "Add route-specific accessibility notes", "Create a new revision identity"],
    expectedResolution: "A revision request can define a new candidate without modifying revision 3.",
    escalationPath: "Accessibility review lead to Operations lead if the review deadline conflicts with the blocker deadline.",
    sourceLinks: [{ label: "Revision comparison", href: "#northwind-revision-comparison" }],
    technical: {
      taskId: "operator-task-northwind-003",
      correlationId: "corr-northwind-revision-004",
      rawRoute: "/v1/tenants/northwind/projects/facilities/tasks/operator-task-northwind-003",
    },
  },
  [taskIds.workflowDefect]: {
    id: taskIds.workflowDefect,
    title: "Correct released predecessor evidence link",
    type: taskKinds.workflowDefect,
    severity: taskSeverities.high,
    status: "triage required",
    ownerRole: "Workflow reliability owner",
    assignee: "Workflow engineer",
    dueDate: "24 August 2026",
    sourceStep: "1b: Information architecture",
    nextAction: "Confirm the candidate references the released topic inventory before any new run is proposed.",
    dependency: "Review evidence is incomplete if the candidate does not name its immutable predecessor.",
    routeClass: "released predecessor integrity route",
    evidence: ["Candidate documentation describes approved topics but omits the released predecessor reference.", "The current review package must preserve its source lineage."],
    remediationChecklist: ["Trace the released predecessor", "Attach the canonical evidence reference", "Re-run the lineage check"],
    expectedResolution: "A review package can identify its released predecessor without changing any released artifact.",
    escalationPath: "Workflow reliability owner to Transition Service owner if the lineage check cannot be reproduced.",
    sourceLinks: [{ label: "Context package summary", href: "#northwind-context-package" }],
    technical: {
      taskId: "operator-task-northwind-004",
      correlationId: "corr-northwind-lineage-001",
      rawRoute: "/v1/tenants/northwind/projects/facilities/tasks/operator-task-northwind-004",
    },
  },
  [taskIds.escalation]: {
    id: taskIds.escalation,
    title: "Escalate unresolved route ownership",
    type: taskKinds.escalation,
    severity: taskSeverities.high,
    status: "waiting on owner decision",
    ownerRole: "Operations lead",
    assignee: "Project sponsor",
    dueDate: "25 August 2026",
    sourceStep: "1b: Information architecture",
    nextAction: "Decide the accountable owner if the architecture team cannot select one primary route label.",
    dependency: "The open blocker must either be resolved or escalated before the human architecture gate can advance.",
    routeClass: "human escalation route",
    evidence: ["The duplicate label affects navigation ownership, not approved topic coverage.", "The review center identifies the escalation path before any canonical decision."],
    remediationChecklist: ["Review both ownership candidates", "Name the accountable route owner", "Return the decision to the architecture review"],
    expectedResolution: "The architecture review receives a human ownership decision or an explicit request for a fresh revision.",
    escalationPath: "Project sponsor decision returns to the Information architecture owner for a fresh candidate.",
    sourceLinks: [{ label: "Route ownership decision record", href: "#northwind-route-ownership" }],
    technical: {
      taskId: "operator-task-northwind-005",
      correlationId: "corr-northwind-escalation-001",
      rawRoute: "/v1/tenants/northwind/projects/facilities/tasks/operator-task-northwind-005",
    },
  },
  [taskIds.waiverRequest]: {
    id: taskIds.waiverRequest,
    title: "Request temporary evidence waiver",
    type: taskKinds.waiverRequest,
    severity: taskSeverities.medium,
    status: "draft only",
    ownerRole: "Governance reviewer",
    assignee: "Operations lead",
    dueDate: "26 August 2026",
    sourceStep: "1b: Information architecture",
    nextAction: "Document why a temporary waiver is requested and retain the unresolved evidence as an open finding.",
    dependency: "A waiver does not remove the route conflict or release the blocked template system.",
    routeClass: "governance waiver route",
    evidence: ["The route conflict remains an active machine and human review finding.", "No release evidence supports bypassing the conflict."],
    remediationChecklist: ["State the requested waiver scope", "Name the responsible reviewer", "Preserve the blocker in the review package"],
    expectedResolution: "A waiver request can be considered without representing the blocker as resolved.",
    escalationPath: "Governance reviewer to project sponsor for waiver consideration; Transition Service remains the decision authority.",
    sourceLinks: [{ label: "Gate finding summary", href: "#northwind-gate-finding" }],
    technical: {
      taskId: "operator-task-northwind-006",
      correlationId: "corr-northwind-waiver-001",
      rawRoute: "/v1/tenants/northwind/projects/facilities/tasks/operator-task-northwind-006",
    },
  },
}

export const demoTaskQueue: readonly DemoTask[] = [
  demoTasks[taskIds.missingInput],
  demoTasks[taskIds.routeConflict],
  demoTasks[taskIds.revisionRequest],
  demoTasks[taskIds.workflowDefect],
  demoTasks[taskIds.escalation],
  demoTasks[taskIds.waiverRequest],
]

export const reviewDecisionIds = {
  approve: "approve",
  reject: "reject",
  requestRevision: "request revision",
  requestInput: "request input",
  escalate: "escalate",
  requestWaiver: "request waiver",
} as const

export type ReviewDecisionId = (typeof reviewDecisionIds)[keyof typeof reviewDecisionIds]

export type ReviewDecision = {
  readonly id: ReviewDecisionId
  readonly label: ReviewDecisionId
  readonly expectedRevision: string
  readonly consequence: string
}

export const reviewDecisions: Readonly<Record<ReviewDecisionId, ReviewDecision>> = {
  [reviewDecisionIds.approve]: {
    id: reviewDecisionIds.approve,
    label: reviewDecisionIds.approve,
    expectedRevision: "3 remains under review",
    consequence: "Approval is only a local preview. The route blocker remains open, so no release or success is represented.",
  },
  [reviewDecisionIds.reject]: {
    id: reviewDecisionIds.reject,
    label: reviewDecisionIds.reject,
    expectedRevision: "3 remains immutable",
    consequence: "The current candidate stays available for comparison and no canonical status changes locally.",
  },
  [reviewDecisionIds.requestRevision]: {
    id: reviewDecisionIds.requestRevision,
    label: reviewDecisionIds.requestRevision,
    expectedRevision: "4 fresh revision candidate",
    consequence: "A fresh revision candidate is expected after route ownership is resolved; revision 3 remains immutable.",
  },
  [reviewDecisionIds.requestInput]: {
    id: reviewDecisionIds.requestInput,
    label: reviewDecisionIds.requestInput,
    expectedRevision: "3 remains under review",
    consequence: "The review waits for the accountable route owner without changing the current candidate.",
  },
  [reviewDecisionIds.escalate]: {
    id: reviewDecisionIds.escalate,
    label: reviewDecisionIds.escalate,
    expectedRevision: "3 remains under review",
    consequence: "Route ownership moves to the project sponsor path while the blocker remains open.",
  },
  [reviewDecisionIds.requestWaiver]: {
    id: reviewDecisionIds.requestWaiver,
    label: reviewDecisionIds.requestWaiver,
    expectedRevision: "3 remains under review",
    consequence: "A waiver request records a governance option but does not resolve the route blocker or release the next step.",
  },
}

export const reviewDecisionOptions: readonly ReviewDecision[] = [
  reviewDecisions[reviewDecisionIds.approve],
  reviewDecisions[reviewDecisionIds.reject],
  reviewDecisions[reviewDecisionIds.requestRevision],
  reviewDecisions[reviewDecisionIds.requestInput],
  reviewDecisions[reviewDecisionIds.escalate],
  reviewDecisions[reviewDecisionIds.requestWaiver],
]

export type DemoReview = {
  readonly title: string
  readonly status: string
  readonly artifactLabel: string
  readonly artifactRevision: number
  readonly artifactHash: string
  readonly reviewerRole: string
  readonly deadline: string
  readonly machineGateEvidence: readonly string[]
  readonly humanFindings: readonly string[]
  readonly escalationPath: string
  readonly sourceLinks: readonly DemoSourceLink[]
  readonly technical: {
    readonly reviewId: string
    readonly rawEvent: string
    readonly rawRoute: string
  }
}

export const activeGateReview: DemoReview = {
  title: "Architecture gate review",
  status: "active human gate",
  artifactLabel: "Navigation resolution package",
  artifactRevision: 3,
  artifactHash: "a7cbe64019f5c66d975cb5d8d8c71fd49bc0207c2fe4d28d69eb1cc1936e2f40",
  reviewerRole: "Information architecture reviewer",
  deadline: "22 August 2026, 16:00 local time",
  machineGateEvidence: ["Topic coverage passed against the released topic inventory.", "Route checker found two primary labels targeting one canonical destination."],
  humanFindings: ["Keep the approved service-area grouping visible.", "Select one accountable owner for the duplicate primary route before approving any revision."],
  escalationPath: "Information architecture owner to Operations lead, then project sponsor for unresolved route ownership.",
  sourceLinks: [{ label: "Architecture review checklist", href: "#northwind-architecture-review" }, { label: "Revision comparison", href: "#northwind-revision-comparison" }],
  technical: {
    reviewId: "gate-review-northwind-architecture-r3",
    rawEvent: "gate.review.requested",
    rawRoute: "/v1/tenants/northwind/projects/facilities/gates/architecture/reviews",
  },
}

export const integrationLabels = {
  notion: "Notion simulated",
  n8n: "n8n simulated",
  production: "Production disabled",
} as const

export type IntegrationLabel = (typeof integrationLabels)[keyof typeof integrationLabels]

export type DemoIntegration = {
  readonly label: IntegrationLabel
  readonly latestSource: string
  readonly delivery: string
  readonly replay: string
  readonly conflict: string
  readonly retry: string
  readonly deadLetterQueue: string
  readonly waitResume: string
  readonly nextAction: string
  readonly technical: {
    readonly rawEvent: string
    readonly rawRoute: string
    readonly deliveryReference: string
  }
}

export const demoIntegrations: readonly DemoIntegration[] = [
  {
    label: integrationLabels.notion,
    latestSource: "Architecture review preview event, revision 3",
    delivery: "Simulated projection is waiting for an authorized decision.",
    replay: "No replay is requested in this local preview.",
    conflict: "No simulated projection conflict is recorded.",
    retry: "No retry is scheduled.",
    deadLetterQueue: "No simulated DLQ entry.",
    waitResume: "Wait for a canonical gate decision; resume remains unavailable.",
    nextAction: "Retain the preview until Transition Service records an authorized outcome.",
    technical: {
      rawEvent: "notion.projection.previewed",
      rawRoute: "/simulated/notion/architecture/revision/3",
      deliveryReference: "notion-sim-northwind-r3",
    },
  },
  {
    label: integrationLabels.n8n,
    latestSource: "Architecture gate review event, revision 3",
    delivery: "Simulated queue is paused at the human gate.",
    replay: "Replay is visible as a simulation state only.",
    conflict: "No simulated idempotency conflict is recorded.",
    retry: "No retry attempt is pending.",
    deadLetterQueue: "No simulated DLQ entry.",
    waitResume: "Waiting for the gate event; resume requires a Transition Service decision.",
    nextAction: "Keep the workflow paused and preserve the current review evidence.",
    technical: {
      rawEvent: "gate.review.waiting",
      rawRoute: "/simulated/n8n/workflows/architecture-gate",
      deliveryReference: "n8n-sim-northwind-gate-r3",
    },
  },
  {
    label: integrationLabels.production,
    latestSource: "No production source event",
    delivery: "Production delivery is disabled.",
    replay: "Production replay is unavailable.",
    conflict: "No production conflict state is claimed.",
    retry: "Production retry is unavailable.",
    deadLetterQueue: "No production DLQ state is claimed.",
    waitResume: "No production wait or resume action is available.",
    nextAction: "Use Transition Service in an authorized environment; this console does not dispatch production actions.",
    technical: {
      rawEvent: "production.disabled",
      rawRoute: "/production/disabled",
      deliveryReference: "production-disabled",
    },
  },
]

export type BaselineComparisonRow = {
  readonly capability: string
  readonly manualBaseline: string
  readonly currentContract: string
}

export const baselineComparisonRows: readonly BaselineComparisonRow[] = [
  {
    capability: "Context",
    manualBaseline: "Context depended on chat recall and handoffs.",
    currentContract: "Core-backed context packages identify released inputs and revisions.",
  },
  {
    capability: "Gates",
    manualBaseline: "Review evidence could be separated from the decision discussion.",
    currentContract: "Machine and human gate evidence remain explicit for operator review.",
  },
  {
    capability: "Tasks",
    manualBaseline: "Follow-up work could be spread across messages and informal notes.",
    currentContract: "Task records identify ownership, due date, dependency, and next action.",
  },
  {
    capability: "Contracts",
    manualBaseline: "Outputs and revisions could be described without a shared execution contract.",
    currentContract: "Core-backed contracts keep revisions, inputs, and gate boundaries reproducible.",
  },
  {
    capability: "Integration simulation",
    manualBaseline: "External handoffs could be assumed from chat status alone.",
    currentContract: "Notion and n8n are explicitly simulated while Transition Service remains the authority.",
  },
]
