import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import type { OperatorApiClient, ProjectDeletionPreview, ProjectDeletionResult } from "../api/client"
import type { ProjectSummary } from "../api/readModels"
import { ProjectsWorkspace } from "./ProjectsWorkspace"


afterEach(() => cleanup())

const project: ProjectSummary = {
  tenantId: "tenant-heartweb",
  projectId: "project-delete-ui",
  name: "Delete UI Project",
  customer: "Delete UI GmbH",
  currentStep: "0",
  progress: "1 von 8 Schritten",
  blockerCount: 0,
  owner: "Heartweb Admin Operator",
  nextAction: "GATE-0 prüfen",
}

const preview: ProjectDeletionPreview = {
  tenant_id: project.tenantId,
  project_id: project.projectId,
  project_name: project.name,
  customer_name: project.customer,
  current_step: "0",
  file_count: 12,
  total_bytes: 4096,
  run_count: 1,
  artifact_count: 1,
  release_count: 0,
  active_run_ids: [],
  active_execution_ids: [],
  allowed: true,
  blockers: [],
  preview_hash: "a".repeat(64),
  workspace_sha256: "b".repeat(64),
  previewed_at: "2026-08-26T01:00:00Z",
}

const deletionResult: ProjectDeletionResult = {
  tenant_id: project.tenantId,
  project_id: project.projectId,
  project_name: project.name,
  deletion_id: "project-deletion-000000000001",
  deleted_at: "2026-08-26T01:01:00Z",
  deleted: true,
  replay: false,
  deleted_file_count: preview.file_count,
  deleted_total_bytes: preview.total_bytes,
  readback_urls: ["/v1/tenants/tenant-heartweb/projects", "/v1/tenants/tenant-heartweb/projects/project-delete-ui"],
}

describe("ProjectsWorkspace project deletion", () => {
  it("requires the delete action and exact LOESCHEN confirmation before calling confirm", async () => {
    const previewProjectDeletion = vi.fn().mockResolvedValue(preview)
    const confirmProjectDeletion = vi.fn().mockResolvedValue(deletionResult)
    const onProjectDeleted = vi.fn().mockResolvedValue(undefined)
    const api = { previewProjectDeletion, confirmProjectDeletion } as unknown as OperatorApiClient

    render(<ProjectsWorkspace api={api} projects={[project]} selectedProjectId={null} openProject={vi.fn()} onCreate={vi.fn()} onProjectDeleted={onProjectDeleted} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete UI Project löschen" }))

    expect(await screen.findByRole("dialog", { name: "Projekt löschen" })).toBeTruthy()
    expect(previewProjectDeletion).toHaveBeenCalledWith(project.projectId, expect.any(AbortSignal))
    expect(screen.getByText("12 Dateien", { exact: false })).toBeTruthy()
    const confirmButton = screen.getByRole("button", { name: "Projekt endgültig löschen" }) as HTMLButtonElement
    expect(confirmButton.disabled).toBe(true)

    fireEvent.change(screen.getByLabelText("Zur Bestätigung LOESCHEN eingeben"), { target: { value: "loeschen" } })
    expect(confirmButton.disabled).toBe(true)
    fireEvent.change(screen.getByLabelText("Zur Bestätigung LOESCHEN eingeben"), { target: { value: "LOESCHEN" } })
    expect(confirmButton.disabled).toBe(false)
    fireEvent.click(confirmButton)

    await vi.waitFor(() => expect(confirmProjectDeletion).toHaveBeenCalledWith(
      project.projectId,
      {
        preview_hash: preview.preview_hash,
        idempotency_key: `idem-project-delete-${preview.preview_hash.slice(0, 24)}`,
        confirmed: true,
        confirmation_text: "LOESCHEN",
      },
      expect.any(AbortSignal),
    ))
    expect(onProjectDeleted).toHaveBeenCalledWith(project.projectId)
  })

  it("shows an active-run blocker and never enables final deletion", async () => {
    const blockedPreview: ProjectDeletionPreview = {
      ...preview,
      allowed: false,
      active_run_ids: ["run-delete-ui"],
      blockers: [{ code: "ERROR_PROJECT_DELETE_ACTIVE_RUN", message: "Ein Lauf ist aktiv.", remediation: "Warte auf das Ende des Laufs." }],
    }
    const previewProjectDeletion = vi.fn().mockResolvedValue(blockedPreview)
    const confirmProjectDeletion = vi.fn()
    const api = { previewProjectDeletion, confirmProjectDeletion } as unknown as OperatorApiClient

    render(<ProjectsWorkspace api={api} projects={[project]} selectedProjectId={null} openProject={vi.fn()} onCreate={vi.fn()} onProjectDeleted={vi.fn()} />)
    fireEvent.click(screen.getByRole("button", { name: "Delete UI Project löschen" }))

    expect(await screen.findByText("Ein Lauf ist aktiv.")).toBeTruthy()
    fireEvent.change(screen.getByLabelText("Zur Bestätigung LOESCHEN eingeben"), { target: { value: "LOESCHEN" } })
    expect((screen.getByRole("button", { name: "Projekt endgültig löschen" }) as HTMLButtonElement).disabled).toBe(true)
    expect(confirmProjectDeletion).not.toHaveBeenCalled()
  })
})
