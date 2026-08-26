import { describe, expect, it } from "vitest"

import { createOperatorApiClient } from "./client"
import { selectCanonicalCurrentArtifact, validateCurrentEvidence } from "./readModels"

const environment = (globalThis as { readonly process?: { readonly env?: Readonly<Record<string, string | undefined>> } }).process?.env ?? {}
const liveEnabled = environment["HEARTWEB_LIVE_WORKSPACE_CONTRACT"] === "1"
const liveDescribe = liveEnabled ? describe : describe.skip

liveDescribe("live Operator workspace contract", () => {
  it("parses every endpoint loaded for one canonical production project", async () => {
    const baseUrl = environment["HEARTWEB_OPERATOR_API_BASE_URL"]
    const tenantId = environment["HEARTWEB_OPERATOR_TENANT_ID"]
    const projectId = environment["HEARTWEB_OPERATOR_PROJECT_ID"]
    if (baseUrl === undefined || tenantId === undefined || projectId === undefined) {
      throw new Error("Live workspace contract requires API base URL, tenant ID and project ID.")
    }

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 30_000)
    try {
      const api = createOperatorApiClient({ baseUrl, tenantId })
      await api.readyz(controller.signal)
      const projects = await api.listProjects(controller.signal)
      expect(projects.some((project) => project.projectId === projectId)).toBe(true)

      const currentRun = await api.getCurrentRun(projectId, controller.signal)
      const [project, run, workflow, steps, tasks, artifacts, releases, gates, context, integrations, intake] = await Promise.all([
        api.getProject(projectId, controller.signal),
        api.getRun(projectId, currentRun.run_id, controller.signal),
        api.getWorkflow(projectId, controller.signal),
        api.listSteps(projectId, controller.signal),
        api.listTasks(projectId, controller.signal),
        api.listArtifacts(projectId, controller.signal),
        api.listReleases(projectId, controller.signal),
        api.listGates(projectId, controller.signal),
        api.listContextPackages(projectId, controller.signal),
        api.getIntegrationStatus(projectId, controller.signal),
        api.getMarkdownIntake(projectId, controller.signal),
      ])

      validateCurrentEvidence(currentRun, artifacts, gates)
      const currentArtifact = selectCanonicalCurrentArtifact(currentRun, artifacts, gates)
      expect(project).toMatchObject({ tenantId, projectId })
      expect(run).toMatchObject({ tenantId, projectId, runId: currentRun.run_id, stepId: currentRun.step_id })
      expect(workflow).toMatchObject({ tenantId, projectId })
      expect(steps.some((step) => step.runId === currentRun.run_id && step.stepId === currentRun.step_id)).toBe(true)
      expect(currentArtifact).not.toBeNull()
      expect(gates.some((gate) => gate.runId === currentRun.run_id && gate.stepId === currentRun.step_id)).toBe(true)
      expect(context.some((entry) => entry.runId === currentRun.run_id && entry.stepId === currentRun.step_id)).toBe(true)
      expect(intake).toMatchObject({ tenantId, projectId })
      expect(Array.isArray(tasks)).toBe(true)
      expect(Array.isArray(releases)).toBe(true)
      expect(Array.isArray(integrations)).toBe(true)
    } finally {
      clearTimeout(timeout)
    }
  }, 35_000)
})
