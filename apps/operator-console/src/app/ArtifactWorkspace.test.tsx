import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import type { ArtifactRecord, ArtifactRevisionListResponse } from "../generated/api-types"
import type { ReleaseRead } from "../api/readModels"
import { createOperatorApiClient } from "../api/client"
import { ArtifactWorkspace } from "./ArtifactWorkspace"
import type { ArtifactRevisionApi, ArtifactRevisionData } from "./useArtifactRevision"
import { releasedArtifactRemediation } from "./useArtifactRevision"

const parentArtifact: ArtifactRecord = { artifact_id: "artifact-parent", content_sha256: "a".repeat(64), created_at: "2026-08-21T10:00:00Z", input_hash: "b".repeat(64), project_id: "project-1", revision: 17, run_id: "run-current", step_id: "1b", storage_key: "outputs/themenstruktur.md", tenant_id: "tenant-1" }
const savedArtifact: ArtifactRecord = { ...parentArtifact, artifact_id: "artifact-new", content_sha256: "c".repeat(64), parent_artifact_ids: [parentArtifact.artifact_id], revision: 18 }
const currentData: ArtifactRevisionData = { projectId: "project-1", currentRun: { tenant_id: "tenant-1", project_id: "project-1", run_id: "run-current", step_id: "1b", expected_revision: 17 }, current: { artifact: parentArtifact } }
const initialRevisions: ArtifactRevisionListResponse = { artifacts: [parentArtifact] }
const savedRevisions: ArtifactRevisionListResponse = { artifacts: [parentArtifact, savedArtifact] }

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function json(payload: unknown): Response {
  return new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json" } })
}

function createApi(responses: readonly [ArtifactRevisionListResponse | Promise<ArtifactRevisionListResponse>, ...(ArtifactRevisionListResponse | Promise<ArtifactRevisionListResponse>)[]], releases: readonly ReleaseRead[] = []): { readonly api: ArtifactRevisionApi; readonly compare: ReturnType<typeof vi.fn>; readonly validate: ReturnType<typeof vi.fn> } {
  let revisionRequest = 0
  const compare = vi.fn(async () => ({ left_artifact: parentArtifact, right_artifact: savedArtifact, unified_diff: "+ Neue Themenstruktur" }))
  const validate = vi.fn(async () => ({ result: "passed", report: "Maschinenpruefung bestanden" }))
  const api = {
    getArtifactContent: vi.fn(async () => ({ artifact: parentArtifact, content_base64: "IyBUaGVtZW5zdHJ1a3R1cg==" })),
    saveArtifactRevision: vi.fn(async () => ({ data: savedArtifact })),
    listArtifactRevisions: vi.fn(async () => responses[Math.min(revisionRequest++, responses.length - 1)] ?? responses[0]),
    listReleases: vi.fn(async () => releases),
    compareArtifactRevisions: compare,
    validateArtifactRevision: validate,
  } satisfies ArtifactRevisionApi
  return { api, compare, validate }
}

async function renderEditor(api: ArtifactRevisionApi): Promise<void> {
  render(<ArtifactWorkspace api={api} data={currentData} />)
  await waitFor(() => expect(within(screen.getByLabelText("Ausgangsrevision")).getByRole("option", { name: "Revision 17" })).toBeInTheDocument())
}

async function saveRevision(): Promise<void> {
  fireEvent.click(screen.getByRole("button", { name: "outputs/themenstruktur.md, Revision 17" }))
  const editor = await screen.findByLabelText("Artefaktinhalt bearbeiten")
  fireEvent.change(editor, { target: { value: "# Neue Themenstruktur" } })
  fireEvent.click(within(screen.getByLabelText("Artefaktaktionen")).getByRole("button", { name: "Als neue Revision speichern" }))
}

describe("ArtifactWorkspace revision lane", () => {
  it("Given equal comparison selections, when comparison is requested, then no comparison request is sent", async () => {
    const fixture = createApi([initialRevisions, savedRevisions])
    await renderEditor(fixture.api)
    await saveRevision()
    await screen.findByText(`Revision ${savedArtifact.revision} wurde unveraenderlich gespeichert.`)

    fireEvent.change(screen.getByLabelText("Neue Revision"), { target: { value: parentArtifact.artifact_id } })
    const compareButton = screen.getByRole("button", { name: "Revisionen vergleichen" })
    expect(compareButton).toBeDisabled()
    fireEvent.click(compareButton)
    expect(fixture.compare).not.toHaveBeenCalled()
  })

  it("Given a saved artifact awaiting canonical readback, when the readback resolves, then success is shown only afterwards", async () => {
    let resolveReadback: (value: ArtifactRevisionListResponse) => void = () => undefined
    const readback = new Promise<ArtifactRevisionListResponse>((resolve) => { resolveReadback = resolve })
    const fixture = createApi([initialRevisions, readback])
    await renderEditor(fixture.api)
    await saveRevision()

    expect(screen.queryByText(`Revision ${savedArtifact.revision} wurde unveraenderlich gespeichert.`)).toBeNull()
    expect(await screen.findByText("Kanonische Revisionsliste wird geladen.")).toBeInTheDocument()
    resolveReadback(savedRevisions)
    expect(await screen.findByText(`Revision ${savedArtifact.revision} wurde unveraenderlich gespeichert.`)).toBeInTheDocument()
  })

  it("Given a save readback without the returned artifact, when saving completes, then the lane fails", async () => {
    const fixture = createApi([initialRevisions, initialRevisions])
    await renderEditor(fixture.api)
    await saveRevision()

    expect(await screen.findByRole("alert")).toHaveTextContent("Die gespeicherte Artefaktrevision fehlt im kanonischen Readback.")
  })

  it("Given a verified new revision, when comparison is requested, then parent and new artifact IDs are sent", async () => {
    const fixture = createApi([initialRevisions, savedRevisions])
    await renderEditor(fixture.api)
    await saveRevision()
    await screen.findByText(`Revision ${savedArtifact.revision} wurde unveraenderlich gespeichert.`)

    fireEvent.click(screen.getByRole("button", { name: "Revisionen vergleichen" }))
    await waitFor(() => expect(fixture.compare).toHaveBeenCalledWith("project-1", { left_artifact_id: parentArtifact.artifact_id, right_artifact_id: savedArtifact.artifact_id }, expect.any(AbortSignal)))
  })

  it("Given a verified new revision, when validation is requested, then validation targets the new artifact", async () => {
    const fixture = createApi([initialRevisions, savedRevisions])
    await renderEditor(fixture.api)
    await saveRevision()
    await screen.findByText(`Revision ${savedArtifact.revision} wurde unveraenderlich gespeichert.`)

    fireEvent.click(screen.getByRole("button", { name: "Erneut pruefen" }))
    await waitFor(() => expect(fixture.validate).toHaveBeenCalledWith("project-1", savedArtifact.artifact_id, { content_sha256: savedArtifact.content_sha256, revision: savedArtifact.revision }, expect.any(AbortSignal)))
  })

  it("Given canonical released evidence for the selected artifact, when the editor opens, then editing and saving are blocked with remediation", async () => {
    const fetch: typeof globalThis.fetch = (input) => {
      const url = input.toString()
      if (url.endsWith("/artifact-revisions")) return Promise.resolve(json(initialRevisions))
      if (url.endsWith("/releases")) return Promise.resolve(json({ data: [{ release_id: "release-1", tenant_id: "tenant-1", project_id: "project-1", run_id: "run-current", step_id: "1b", gate_id: "GATE-1B", artifact_id: parentArtifact.artifact_id, artifact_sha256: parentArtifact.content_sha256, artifact_revision: parentArtifact.revision, approval_id: "approval-1", policy_version: "1.0.0", status: "released", released_at: "2026-08-21T10:00:00Z" }] }))
      return Promise.reject(new Error(`Unexpected request: ${url}`))
    }
    vi.stubGlobal("fetch", fetch)
    await renderEditor(createOperatorApiClient({ baseUrl: "", tenantId: "tenant-1" }))

    expect(await screen.findByText(releasedArtifactRemediation)).toBeInTheDocument()
    expect(screen.getByLabelText("Artefaktinhalt bearbeiten")).toBeDisabled()
    expect(screen.getByRole("button", { name: "Als neue Revision speichern" })).toBeDisabled()
  })

  it("Given a revision list containing another run, when revisions are loaded, then the lane rejects it", async () => {
    const fixture = createApi([{ artifacts: [parentArtifact, { ...savedArtifact, run_id: "run-other" }] }])
    render(<ArtifactWorkspace api={fixture.api} data={currentData} />)

    expect(await screen.findByRole("alert")).toHaveTextContent("Die Revisionsliste enthaelt ein Artefakt aus einem anderen Lauf.")
    expect(screen.getByRole("button", { name: "Als neue Revision speichern" })).toBeDisabled()
  })
})
