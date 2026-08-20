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
  taskCount: 3,
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
