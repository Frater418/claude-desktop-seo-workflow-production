import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"
import { flushSync } from "react-dom"
import type { ArtifactRecord } from "../generated/api-types"
import { OperatorReadModelError, selectCanonicalCurrentArtifact, validateCurrentEvidence } from "../api/readModels"
import type { AcceptedIntakeRead, ContextRead, CurrentRun, GateRead, IntegrationRead, ProjectSummary, ReleaseRead, RunRead, StepRead, TaskRead, WorkflowRead } from "../api/readModels"
import { OperatorApiError, type OperatorApiClient } from "../api/client"
import type { AdminActionClient } from "./useAdminAction"

export type OperatorWorkspaceData = {
  readonly projectId: string
  readonly project: ProjectSummary
  readonly currentRun: CurrentRun
  readonly run: RunRead
  readonly workflow: WorkflowRead
  readonly steps: readonly StepRead[]
  readonly tasks: readonly TaskRead[]
  readonly artifacts: readonly ArtifactRecord[]
  readonly gates: readonly GateRead[]
  readonly context: readonly ContextRead[]
  readonly integrations: readonly IntegrationRead[]
  readonly intake?: AcceptedIntakeRead
  readonly releases?: readonly ReleaseRead[]
  readonly current: CurrentWorkspaceRecords
  readonly actionClient: AdminActionClient
  readonly reload: () => Promise<void>
}

export type CurrentWorkspaceRecords = {
  readonly step: StepRead | null
  readonly gate: GateRead | null
  readonly context: ContextRead | null
  readonly artifact: ArtifactRecord | null
}

export type OperatorWorkspaceState =
  | { readonly kind: "loading" }
  | { readonly kind: "ready"; readonly data: OperatorWorkspaceData }
  | { readonly kind: "overview" }
  | { readonly kind: "empty" }
  | { readonly kind: "error"; readonly title: string; readonly message: string }

export type OperatorWorkspace = {
  readonly state: OperatorWorkspaceState
  readonly projects: readonly ProjectSummary[]
  readonly selectedProjectId: string | null
  readonly deselectProject: () => void
  readonly selectProject: (projectId: string) => Promise<CurrentRun>
  readonly reload: (projectId?: string) => Promise<void>
}

type PendingCommit = { readonly controller: AbortController; readonly resolve: () => void; readonly reject: (reason: unknown) => void }

function abortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError"
}

export function useOperatorWorkspace(api: OperatorApiClient): OperatorWorkspace {
  const [state, setState] = useState<OperatorWorkspaceState>({ kind: "loading" })
  const stateRef = useRef<OperatorWorkspaceState>(state)
  stateRef.current = state
  const [projects, setProjects] = useState<readonly ProjectSummary[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const selectedProjectRef = useRef<string | null>(null)
  const requestRef = useRef<AbortController | null>(null)
  const pendingCommitRef = useRef<PendingCommit | null>(null)

  useLayoutEffect(() => {
    const pendingCommit = pendingCommitRef.current
    if (pendingCommit !== null && requestRef.current === pendingCommit.controller) {
      pendingCommitRef.current = null
      pendingCommit.resolve()
    }
  })

  const reload = useCallback(async (requestedProjectId?: string): Promise<void> => {
    requestRef.current?.abort()
    const pendingCommit = pendingCommitRef.current
    if (pendingCommit !== null) {
      pendingCommitRef.current = null
      pendingCommit.reject(new DOMException("Kanonische Aktualisierung wurde ersetzt.", "AbortError"))
    }
    const controller = new AbortController()
    requestRef.current = controller
    if (stateRef.current.kind !== "ready") setState({ kind: "loading" })
    try {
      await api.readyz(controller.signal)
      const canonicalProjects = await api.listProjects(controller.signal)
      if (canonicalProjects.length === 0) {
        selectedProjectRef.current = null
        setProjects(canonicalProjects)
        setSelectedProjectId(null)
        setState({ kind: "empty" })
        return
      }
      const projectId = requestedProjectId ?? selectedProjectRef.current
      if (projectId === null) {
        selectedProjectRef.current = null
        setProjects(canonicalProjects)
        setSelectedProjectId(null)
        setState({ kind: "overview" })
        return
      }
      if (!canonicalProjects.some((project) => project.projectId === projectId)) throw new OperatorReadModelError("Das ausgewaehlte Projekt ist nicht in der kanonischen Projektliste enthalten.")
      const currentRun = await api.getCurrentRun(projectId, controller.signal)
      const [project, run, workflow, steps, tasks, artifacts, gates, context, integrations, intake, releases] = await Promise.all([
        api.getProject(projectId, controller.signal), api.getRun(projectId, currentRun.run_id, controller.signal), api.getWorkflow(projectId, controller.signal), api.listSteps(projectId, controller.signal), api.listTasks(projectId, controller.signal), api.listArtifacts(projectId, controller.signal), api.listGates(projectId, controller.signal), api.listContextPackages(projectId, controller.signal), api.getIntegrationStatus(projectId, controller.signal), api.getMarkdownIntake(projectId, controller.signal), api.listReleases(projectId, controller.signal),
      ])
      validateCurrentEvidence(currentRun, artifacts, gates)
      if (run.stepId !== currentRun.step_id) throw new OperatorReadModelError("Der geladene Lauf stimmt nicht mit dem aktuellen Schritt ueberein.")
      if (requestRef.current !== controller) throw new DOMException("Kanonische Aktualisierung wurde ersetzt.", "AbortError")
      const current: CurrentWorkspaceRecords = {
        step: steps.find((step) => step.tenantId === currentRun.tenant_id && step.projectId === currentRun.project_id && step.runId === currentRun.run_id && step.stepId === currentRun.step_id) ?? null,
        gate: gates.find((gate) => gate.tenantId === currentRun.tenant_id && gate.projectId === currentRun.project_id && gate.runId === currentRun.run_id && gate.stepId === currentRun.step_id) ?? null,
        context: context.find((entry) => entry.tenantId === currentRun.tenant_id && entry.projectId === currentRun.project_id && entry.runId === currentRun.run_id && entry.stepId === currentRun.step_id) ?? null,
        artifact: selectCanonicalCurrentArtifact(currentRun, artifacts, gates),
      }
      const data: OperatorWorkspaceData = { projectId, project, currentRun, run, workflow, steps, tasks, artifacts, gates, context, integrations, intake, releases, current, actionClient: api, reload: () => reload(projectId) }
      await new Promise<void>((resolve, reject) => {
        pendingCommitRef.current = { controller, resolve, reject }
        flushSync(() => {
          selectedProjectRef.current = projectId
          setProjects(canonicalProjects)
          setSelectedProjectId(projectId)
          setState({ kind: "ready", data })
        })
      })
    } catch (error) {
      if (abortError(error)) throw error
      if (error instanceof Error) {
        const title = error instanceof OperatorReadModelError
          ? "Projekt-Daten nicht lesbar"
          : error instanceof OperatorApiError && error.kind === "network"
            ? "Lokale Operator-API nicht erreichbar"
            : "Projekt konnte nicht geladen werden"
        setState({ kind: "error", title, message: error.message })
        throw error
      }
      throw error
    }
  }, [api])

  const selectProject = useCallback(async (projectId: string): Promise<CurrentRun> => {
    await reload(projectId)
    const currentState = stateRef.current
    if (currentState.kind === "ready" && currentState.data.projectId === projectId) return currentState.data.currentRun
    throw new OperatorReadModelError("Das ausgewaehlte Projekt wurde nicht kanonisch geladen.")
  }, [reload])

  const deselectProject = useCallback((): void => {
    requestRef.current?.abort()
    requestRef.current = null
    const pendingCommit = pendingCommitRef.current
    if (pendingCommit !== null) {
      pendingCommitRef.current = null
      pendingCommit.reject(new DOMException("Projektansicht wurde geschlossen.", "AbortError"))
    }
    selectedProjectRef.current = null
    setSelectedProjectId(null)
    setState(projects.length === 0 ? { kind: "empty" } : { kind: "overview" })
  }, [projects.length])

  useEffect(() => {
    void reload().catch((error: unknown) => {
      if (!abortError(error)) return
    })
    return () => {
      requestRef.current?.abort()
      requestRef.current = null
      const pendingCommit = pendingCommitRef.current
      if (pendingCommit !== null) {
        pendingCommitRef.current = null
        pendingCommit.reject(new DOMException("Kanonische Aktualisierung wurde beendet.", "AbortError"))
      }
    }
  }, [reload])

  return { state, projects, selectedProjectId, deselectProject, selectProject, reload }
}
