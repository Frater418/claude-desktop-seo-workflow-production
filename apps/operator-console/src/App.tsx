import { useEffect, useState } from "react"
import { createOperatorApiClient, OperatorApiError } from "./api/client"
import {
  baselineComparisonRows,
  demoIntegrations,
  demoTaskQueue,
  demoTasks,
  neutralDemoProject,
  reviewDecisionIds,
  taskIds,
  type DemoTaskId,
  type ReviewDecisionId,
  type WorkflowStep,
} from "./dev/neutralDemo"
import { ArtifactPreview, defaultDemoArtifact, demoArtifacts } from "./features/artifacts/ArtifactPreview"
import { RevisionDiff } from "./features/artifacts/RevisionDiff"
import { IntegrationStatus } from "./features/integrations/IntegrationStatus"
import { BaselineComparison } from "./features/presentation/BaselineComparison"
import { WorkflowMatrix } from "./features/presentation/WorkflowMatrix"
import { ProjectDashboard } from "./features/projects/ProjectDashboard"
import { ReviewCenter } from "./features/reviews/ReviewCenter"
import { ContextPackageSummary } from "./features/runs/ContextPackageSummary"
import { RevisionRunPreview } from "./features/runs/RevisionRunPreview"
import { RunHistory } from "./features/runs/RunHistory"
import { TaskQueue } from "./features/tasks/TaskQueue"
import { TicketDetail } from "./features/tasks/TicketDetail"
import { StepDetail } from "./features/workflow/StepDetail"
import { WorkflowTimeline } from "./features/workflow/WorkflowTimeline"

const apiClient = createOperatorApiClient({
  baseUrl: import.meta.env["VITE_OPERATOR_API_BASE_URL"] ?? "",
  tenantId: import.meta.env["VITE_OPERATOR_TENANT_ID"] ?? "tenant-local",
})

type RealApiState =
  | { readonly kind: "loading" }
  | { readonly kind: "available" }
  | { readonly kind: "unavailable"; readonly message: string }

type AppProps = {
  readonly search?: string
}

type DemoWorkspace = "workflow" | "artifacts" | "operations" | "presentation"

function isDemoSearch(search: string): boolean {
  return search === "?mode=demo"
}

function selectedDemoStep(stepId: string): WorkflowStep {
  if (stepId === neutralDemoProject.sideflow.id) {
    return neutralDemoProject.sideflow
  }
  const fallbackStep = neutralDemoProject.steps[0]
  if (fallbackStep === undefined) {
    throw new Error("The local simulation requires an initial workflow step.")
  }
  return neutralDemoProject.steps.find((step) => step.id === stepId) ?? fallbackStep
}

export function App({ search = window.location.search }: AppProps): JSX.Element {
  const demoMode = isDemoSearch(search)
  const [selectedStepId, setSelectedStepId] = useState("1b")
  const [demoWorkspace, setDemoWorkspace] = useState<DemoWorkspace>("workflow")
  const [selectedArtifactId, setSelectedArtifactId] = useState(defaultDemoArtifact.id)
  const [selectedTaskId, setSelectedTaskId] = useState<DemoTaskId>(taskIds.missingInput)
  const [selectedReviewDecisionId, setSelectedReviewDecisionId] = useState<ReviewDecisionId>(reviewDecisionIds.requestInput)
  const [realApiState, setRealApiState] = useState<RealApiState>({ kind: "loading" })

  useEffect(() => {
    if (demoMode) {
      return
    }

    const controller = new AbortController()
    let active = true

    void (async () => {
      try {
        await apiClient.readyz(controller.signal)
        const projects = await apiClient.listProjects(controller.signal)
        if (!Array.isArray(projects.data)) {
          throw new OperatorApiError({
            kind: "unparseable",
            status: 200,
            message: "The local Operator API project list is unavailable or unparseable.",
          })
        }
        if (active) {
          setRealApiState({ kind: "available" })
        }
      } catch (error) {
        if (error instanceof OperatorApiError) {
          if (active) {
            setRealApiState({ kind: "unavailable", message: error.message })
          }
          return
        }
        if (error instanceof DOMException && error.name === "AbortError") {
          return
        }
        throw error
      }
    })()

    return () => {
      active = false
      controller.abort()
    }
  }, [demoMode])

  if (!demoMode) {
    return <RealApiSurface state={realApiState} />
  }

  const selectedStep = selectedDemoStep(selectedStepId)
  const selectedArtifact = demoArtifacts.find((artifact) => artifact.id === selectedArtifactId) ?? defaultDemoArtifact
  const selectedTask = demoTasks[selectedTaskId]

  return (
    <main className="app-shell">
      <header className="project-bar">
        <div><p className="eyebrow">Heartweb Operator Console</p><h1>{neutralDemoProject.title}</h1></div>
        <div className="mode-stack"><span className="simulation-label">Local simulation</span><span>Notion simulated</span><span>n8n simulated</span></div>
      </header>
      <DemoWorkspaceSwitch onSelect={setDemoWorkspace} selectedWorkspace={demoWorkspace} />
      {demoWorkspace === "workflow" ? (
        <section aria-labelledby="workflow-workspace-tab" className="workflow-workspace" id="workflow-workspace" role="tabpanel" tabIndex={0}>
          <ProjectDashboard project={neutralDemoProject} />
          <div className="console-grid">
            <WorkflowTimeline onSelect={setSelectedStepId} selectedStepId={selectedStepId} sideflow={neutralDemoProject.sideflow} steps={neutralDemoProject.steps} />
            <StepDetail projectId={neutralDemoProject.id} step={selectedStep} />
          </div>
        </section>
      ) : demoWorkspace === "artifacts" ? (
        <section aria-labelledby="artifacts-workspace-tab" className="artifact-run-workspace" id="artifacts-workspace" role="tabpanel" tabIndex={0}>
          <div className="workspace-heading"><p className="eyebrow">Artifact and run workspace</p><h2>Artifacts &amp; runs</h2><p>Immutable outputs, revision evidence, and replaceable technical-session cache state.</p></div>
          <div className="artifact-run-grid">
            <div className="artifact-column">
              <ArtifactPreview onSelectArtifact={setSelectedArtifactId} selectedArtifact={selectedArtifact} />
              <RevisionDiff artifact={selectedArtifact} />
            </div>
            <div className="run-column">
              <RunHistory />
              <ContextPackageSummary />
              <RevisionRunPreview />
            </div>
          </div>
        </section>
      ) : demoWorkspace === "operations" ? (
        <section aria-labelledby="operations-workspace-tab" className="operations-workspace" id="operations-workspace" role="tabpanel" tabIndex={0}>
          <div className="workspace-heading"><p className="eyebrow">Operator action workspace</p><h2>Operations</h2><p>Local task, review, and integration previews remain non-authoritative until Transition Service records an authorized outcome.</p></div>
          <div className="operations-grid">
            <TaskQueue onSelectTask={setSelectedTaskId} selectedTaskId={selectedTaskId} tasks={demoTaskQueue} />
            <TicketDetail task={selectedTask} />
            <ReviewCenter onSelectDecision={setSelectedReviewDecisionId} selectedDecisionId={selectedReviewDecisionId} />
            <IntegrationStatus integrations={demoIntegrations} />
          </div>
        </section>
      ) : (
        <section aria-labelledby="presentation-workspace-tab" className="presentation-workspace" id="presentation-workspace" role="tabpanel" tabIndex={0}>
          <div className="workspace-heading"><p className="eyebrow">Decision support workspace</p><h2>Presentation</h2><p>Readable capability and workflow evidence for local operator orientation.</p></div>
          <div className="presentation-grid">
            <WorkflowMatrix sideflow={neutralDemoProject.sideflow} steps={neutralDemoProject.steps} />
            <BaselineComparison rows={baselineComparisonRows} />
          </div>
        </section>
      )}
    </main>
  )
}

type DemoWorkspaceSwitchProps = {
  readonly selectedWorkspace: DemoWorkspace
  readonly onSelect: (workspace: DemoWorkspace) => void
}

function DemoWorkspaceSwitch({ selectedWorkspace, onSelect }: DemoWorkspaceSwitchProps): JSX.Element {
  return (
    <nav aria-label="Demo workspace" className="workspace-switch">
      <div aria-label="Demo workspace" className="workspace-tabs" role="tablist">
        <button aria-controls="workflow-workspace" aria-selected={selectedWorkspace === "workflow"} id="workflow-workspace-tab" onClick={() => onSelect("workflow")} role="tab" type="button">Workflow</button>
        <button aria-controls="artifacts-workspace" aria-selected={selectedWorkspace === "artifacts"} id="artifacts-workspace-tab" onClick={() => onSelect("artifacts")} role="tab" type="button">Artifacts &amp; runs</button>
        <button aria-controls="operations-workspace" aria-selected={selectedWorkspace === "operations"} id="operations-workspace-tab" onClick={() => onSelect("operations")} role="tab" type="button">Operations</button>
        <button aria-controls="presentation-workspace" aria-selected={selectedWorkspace === "presentation"} id="presentation-workspace-tab" onClick={() => onSelect("presentation")} role="tab" type="button">Presentation</button>
      </div>
    </nav>
  )
}

function RealApiSurface({ state }: { readonly state: RealApiState }): JSX.Element {
  if (state.kind === "loading") {
    return <main className="api-status"><p className="eyebrow">Heartweb Operator Console</p><h1>Checking local Operator API</h1><p>Readiness and the configured neutral project list are being requested.</p></main>
  }
  if (state.kind === "available") {
    return <main className="api-status"><p className="eyebrow">Heartweb Operator Console</p><h1>Real API connected</h1><p>The project list transport is available. Its generated payload remains unknown, so Package 1 does not invent a projection view.</p></main>
  }
  return <main className="api-status"><p className="eyebrow">Heartweb Operator Console</p><h1>Real API unavailable</h1><p>{state.message}</p><p>No simulation data is shown in real API mode.</p></main>
}
