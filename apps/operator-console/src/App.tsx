import { useEffect, useState } from "react"
import { createOperatorApiClient, OperatorApiError } from "./api/client"
import { neutralDemoProject, type WorkflowStep } from "./dev/neutralDemo"
import { ProjectDashboard } from "./features/projects/ProjectDashboard"
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

  return (
    <main className="app-shell">
      <header className="project-bar">
        <div><p className="eyebrow">Heartweb Operator Console</p><h1>{neutralDemoProject.title}</h1></div>
        <div className="mode-stack"><span className="simulation-label">Local simulation</span><span>Notion simulated</span><span>n8n simulated</span></div>
      </header>
      <ProjectDashboard project={neutralDemoProject} />
      <div className="console-grid">
        <WorkflowTimeline onSelect={setSelectedStepId} selectedStepId={selectedStepId} sideflow={neutralDemoProject.sideflow} steps={neutralDemoProject.steps} />
        <StepDetail projectId={neutralDemoProject.id} step={selectedStep} />
      </div>
    </main>
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
