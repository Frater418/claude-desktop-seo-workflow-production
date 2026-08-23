import { afterEach, describe, expect, it, vi } from "vitest"
import { createOperatorApiFixture } from "./operatorApiFixture"

const projectPath = "/v1/tenants/tenant-welle-zwei/projects/project-welle-zwei"
const artifactRevisionsPath = `${projectPath}/runs/lauf-20260821-a/steps/1b/artifact-revisions`
const artifactSavePath = `${projectPath}/artifacts`
const inputPreviewPath = `${projectPath}/actions/request-input/preview`
const deliveryPath = `${projectPath}/delivery`
const deliveryRequest = {
  delivery_export_result_id: "delivery-export-result-fixture-0001",
  delivery_package_id: "delivery-package-fixture-0001",
  export_id: "delivery-export-fixture-0001",
  export_request: {
    delivery_export_request_id: "delivery-export-request-fixture-0001",
    schema_version: "1.0.0",
    tenant_id: "tenant-welle-zwei",
    project_id: "project-welle-zwei",
    scope: "checkpoint",
    draft_inclusion_policy: "include_explicit_drafts",
    idempotency_key: "idem-fixture-0001",
    created_at: "2026-08-22T10:00:00Z",
    source_snapshot_revision: 3,
    requested_role_packages: ["copywriter"],
  },
  package_revision: 2,
  role_package_requests: [{ role: "copywriter", role_handoff_manifest_id: "role-handoff-fixture-0001" }],
  notion_import_request: {
    notion_import_manifest_id: "notion-import-fixture-0001",
    customer_external_id: "customer-fixture",
    implementation_tasks: [{ task_id: "task-fixture-0001", assignment_id: "assignment-fixture-0001", title: "Fixture-Aufgabe", status: "not_started", comments: "", source_assignee: "Redaktion", priority: "high", deadline: "2026-09-01", role: "copywriter", dependencies: [], artifact_relations: [], notion_user_id: "notion-user-fixture-0001" }],
    publication_registry: { publication_registry_record_id: "publication-registry-fixture-0001", urls: ["https://example.test/fixture"] },
  },
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("Operator API integration fixture", () => {
  it("exposes three immutable artifact revisions with canonical parent lineage", async () => {
    const fixture = createOperatorApiFixture()

    await fixture.fetch(artifactSavePath, { method: "POST", body: "{}" })
    const response = await fixture.fetch(artifactRevisionsPath, { method: "GET" })

    await expect(response.json()).resolves.toMatchObject({
      artifacts: [
        { artifact_id: "artifact-welle-zwei-16", revision: 16 },
        { artifact_id: "artifact-welle-zwei", revision: 17, parent_artifact_ids: ["artifact-welle-zwei-16"] },
        { artifact_id: "artifact-welle-zwei-18", revision: 18, parent_artifact_ids: ["artifact-welle-zwei"] },
      ],
    })
  })

  it("rejects an action preview whose identity does not match the canonical current run", async () => {
    const fixture = createOperatorApiFixture()

    const response = fixture.fetch(inputPreviewPath, {
      method: "POST",
      body: JSON.stringify({ action: "request-input", tenant_id: "tenant-welle-zwei", project_id: "project-welle-zwei", run_id: "lauf-veraltet-20260821", step_id: "1b", expected_revision: 17 }),
    })

    await expect(response).rejects.toThrow("Unerwartete Testanfrage")
  })

  it("serves a Task 6 checkpoint lifecycle with only a canonical ZIP download", async () => {
    const fixture = createOperatorApiFixture()

    const checkpointPreview = await fixture.fetch(`${deliveryPath}/preview?scope=checkpoint`, { method: "GET" })
    await expect(checkpointPreview.json()).resolves.toMatchObject({ scope: "checkpoint", policy_eligible: true })
    const history = await fixture.fetch(`${deliveryPath}/exports`, { method: "GET" })
    await expect(history.json()).resolves.toEqual({ data: [] })
    const created = await fixture.fetch(`${deliveryPath}/exports`, { method: "POST", body: JSON.stringify(deliveryRequest) })
    await expect(created.json()).resolves.toMatchObject({ export_id: deliveryRequest.export_id, project_id: "project-welle-zwei" })
    const record = await fixture.fetch(`${deliveryPath}/exports/${deliveryRequest.export_id}`, { method: "GET" })
    await expect(record.json()).resolves.toMatchObject({ export_id: deliveryRequest.export_id, delivery_package_id: deliveryRequest.delivery_package_id })
    const archive = await fixture.fetch(`${deliveryPath}/exports/${deliveryRequest.export_id}/download`, { method: "GET" })

    expect(archive.headers.get("Content-Disposition")).toBe(`attachment; filename="${deliveryRequest.export_id}.zip"`)
    expect(archive.headers.get("ETag")).toBe("delivery-fixture-etag")
    expect((await archive.blob()).size).toBeGreaterThan(0)
    expect(fixture.state.calls.filter((call) => call === `POST ${deliveryPath}/exports`)).toHaveLength(1)
  })

  it("rejects a Task 6 create whose request identity does not match the route", async () => {
    const fixture = createOperatorApiFixture()
    const invalidRequest = { ...deliveryRequest, export_request: { ...deliveryRequest.export_request, project_id: "project-other" } }

    await expect(fixture.fetch(`${deliveryPath}/exports`, { method: "POST", body: JSON.stringify(invalidRequest) })).rejects.toThrow("Unerwartete Testanfrage")
  })
})
