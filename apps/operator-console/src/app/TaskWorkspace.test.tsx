import { afterEach, describe, expect, it } from "vitest"
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import type { ActionConfirmResult, ActionIntent, ActionPreview } from "../generated/api-types"
import type { CurrentRun, StepRead, TaskRead } from "../api/readModels"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { TaskWorkspace } from "./TaskWorkspace"

const currentRun: CurrentRun = { tenant_id: "tenant-eindeutig", project_id: "projekt-eindeutig", run_id: "lauf-eindeutig", step_id: "0", expected_revision: 1 }

const tasks: readonly TaskRead[] = [
  task({ taskId: "task-low", title: "Niedrige Nacharbeit", status: "erledigt", owner: "Dora", priority: "low", deadline: "2026-08-26", stepId: "2", resolution: "Nachweis ablegen", dependency: "Keine" }),
  task({ taskId: "task-high", title: "Hohe Rueckfrage", status: "wartet", owner: "Bernd", priority: "high", deadline: "2026-08-22", stepId: "1", resolution: "Rueckfrage beantworten", dependency: "Kundenfreigabe" }),
  task({ taskId: "task-critical", title: "Kritische Freigabe", status: "offen", owner: "Anna", priority: "critical", deadline: "2026-08-20", stepId: "0", resolution: "Freigabe erteilen", dependency: "Pruefbericht" }),
  task({ taskId: "task-medium", title: "Mittlere Pruefung", status: "offen", owner: "Clara", priority: "medium", deadline: "2026-08-24", stepId: "1b", resolution: "Struktur pruefen", dependency: "Themeninventar" }),
]

afterEach(cleanup)

function task(overrides: Partial<TaskRead>): TaskRead {
  return { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, taskId: "task", title: "Aufgabe", status: "offen", owner: "Anna", priority: "medium", deadline: "2026-08-20", resolution: "Loesung", dependency: "Keine", ...overrides }
}

function workspace(queue: readonly TaskRead[]): OperatorWorkspaceData {
  const step: StepRead = { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, status: "in_progress", blocker: "Keine", nextAction: "Weiterarbeiten" }
  const intent: ActionIntent = { action: "start", tenant_id: currentRun.tenant_id, project_id: currentRun.project_id, run_id: currentRun.run_id, step_id: currentRun.step_id, expected_revision: currentRun.expected_revision }
  const preview: ActionPreview = { allowed: false, blockers: [], consequence: {}, intent, preview_hash: "preview" }
  const confirmation: ActionConfirmResult = { canonical: {}, preview_hash: "preview", readback_urls: [], replay: false }
  return {
    projectId: currentRun.project_id,
    project: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, name: "Projekt Eindeutig", customer: "Eindeutig GmbH", currentStep: currentRun.step_id, progress: "0 von 8 Schritten", blockerCount: 0, owner: "Heartweb Admin Operator", nextAction: "Weiterarbeiten" },
    currentRun,
    run: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, revision: currentRun.expected_revision, status: "in_progress" },
    workflow: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, initialEdges: [], sideflows: [{ stepId: "3b", status: "not_due" }] },
    steps: [step], tasks: queue, artifacts: [], gates: [], context: [], integrations: [], current: { step, gate: null, context: null, artifact: null },
    actionClient: { previewAdminAction: async (): Promise<ActionPreview> => preview, confirmAdminAction: async (): Promise<ActionConfirmResult> => confirmation },
    reload: async (): Promise<void> => undefined,
  }
}

function expectOnlyTask(title: string): void {
  expect(screen.getByRole("button", { name: title })).toBeInTheDocument()
  for (const taskEntry of tasks) if (taskEntry.title !== title) expect(screen.queryByRole("button", { name: taskEntry.title })).toBeNull()
}

describe("TaskWorkspace queue", () => {
  it.each([
    ["Status filtern", "wartet", "Hohe Rueckfrage"],
    ["Verantwortung filtern", "Bernd", "Hohe Rueckfrage"],
    ["Prioritaet filtern", "medium", "Mittlere Pruefung"],
    ["Faellig bis", "2026-08-20", "Kritische Freigabe"],
    ["Schritt filtern", "1b", "Mittlere Pruefung"],
  ] as const)("filters by %s independently", (label, value, expectedTitle) => {
    // Given: a queue with distinct values for every operational filter.
    render(<TaskWorkspace data={workspace(tasks)} />)

    // When: one filter is changed.
    fireEvent.change(screen.getByLabelText(label), { target: { value } })

    // Then: only the matching queue context remains visible.
    expectOnlyTask(expectedTitle)
  })

  it.each([
    ["Status filtern", "wartet", "Hohe Rueckfrage", "Rueckfrage beantworten", "Kundenfreigabe"],
    ["Verantwortung filtern", "Bernd", "Hohe Rueckfrage", "Rueckfrage beantworten", "Kundenfreigabe"],
    ["Prioritaet filtern", "medium", "Mittlere Pruefung", "Struktur pruefen", "Themeninventar"],
    ["Faellig bis", "2026-08-20", "Kritische Freigabe", "Freigabe erteilen", "Pruefbericht"],
    ["Schritt filtern", "1b", "Mittlere Pruefung", "Struktur pruefen", "Themeninventar"],
  ] as const)("keeps the selected task context for %s", (label, value, title, resolution, dependency) => {
    render(<TaskWorkspace data={workspace(tasks)} />)
    fireEvent.click(screen.getByRole("button", { name: title }))

    fireEvent.change(screen.getByLabelText(label), { target: { value } })

    expect(screen.getByRole("heading", { name: title })).toBeInTheDocument()
    expect(screen.getByText(resolution)).toBeInTheDocument()
    expect(screen.getByText(dependency)).toBeInTheDocument()
  })

  it("combines all queue filters without dropping the matching task detail", () => {
    // Given: the critical task uniquely matches every filter.
    render(<TaskWorkspace data={workspace(tasks)} />)

    // When: the operator combines status, owner, priority, due date, and step.
    fireEvent.change(screen.getByLabelText("Status filtern"), { target: { value: "offen" } })
    fireEvent.change(screen.getByLabelText("Verantwortung filtern"), { target: { value: "Anna" } })
    fireEvent.change(screen.getByLabelText("Prioritaet filtern"), { target: { value: "critical" } })
    fireEvent.change(screen.getByLabelText("Faellig bis"), { target: { value: "2026-08-20" } })
    fireEvent.change(screen.getByLabelText("Schritt filtern"), { target: { value: "0" } })

    // Then: the exact task and its operator context remain available.
    expectOnlyTask("Kritische Freigabe")
    expect(screen.getByText("Freigabe erteilen")).toBeInTheDocument()
    expect(screen.getByText("Pruefbericht")).toBeInTheDocument()
  })

  it("keeps a visible selection and chooses the first visible task only after it is filtered out", () => {
    // Given: a selected critical task that remains visible after a status filter.
    render(<TaskWorkspace data={workspace(tasks)} />)
    fireEvent.click(screen.getByRole("button", { name: "Kritische Freigabe" }))

    // When: the status filter preserves it, then the owner filter excludes it.
    fireEvent.change(screen.getByLabelText("Status filtern"), { target: { value: "offen" } })
    expect(screen.getByRole("heading", { name: "Kritische Freigabe" })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText("Verantwortung filtern"), { target: { value: "Clara" } })

    // Then: the first visible task replaces the hidden selection with its full detail.
    expect(screen.getByRole("heading", { name: "Mittlere Pruefung" })).toBeInTheDocument()
    expect(screen.getByText("Struktur pruefen")).toBeInTheDocument()
  })

  it("exposes deterministic priority and due-date sorting and distinguishes both empty states", () => {
    // Given: an unsorted queue and a canonical non-empty task collection.
    const view = render(<TaskWorkspace data={workspace(tasks)} />)
    const list = screen.getByRole("list", { name: "Gefilterte Aufgaben" })

    // When: the operator applies the two accessible sorts and a date that excludes every task.
    expect(screen.getByRole("button", { name: "Nach Prioritaet sortieren" })).toHaveAttribute("aria-description", "Aktuell: hoechste zuerst")
    expect(within(list).getAllByRole("button").map((entry) => entry.textContent)).toEqual(expect.arrayContaining([expect.stringContaining("Kritische Freigabe")]))
    fireEvent.click(screen.getByRole("button", { name: "Nach Faelligkeit sortieren" }))
    fireEvent.click(screen.getByRole("button", { name: "Nach Faelligkeit sortieren" }))
    expect(screen.getByRole("button", { name: "Nach Faelligkeit sortieren" })).toHaveAttribute("aria-description", "Aktuell: spaeteste zuerst")
    fireEvent.change(screen.getByLabelText("Faellig bis"), { target: { value: "2026-08-01" } })

    // Then: filtered-empty and canonical-empty have different operational guidance.
    expect(screen.getByText("Keine Aufgaben entsprechen den aktuellen Filtern.")).toBeInTheDocument()
    view.unmount()
    render(<TaskWorkspace data={workspace([])} />)
    expect(screen.getByText("Keine Aufgaben vorhanden.")).toBeInTheDocument()
  })
})
