import { afterEach, describe, expect, it, vi } from "vitest"
import { createOperatorApiFixture } from "./operatorApiFixture"

const artifactRevisionsPath = "/v1/tenants/tenant-welle-zwei/projects/projekt-welle-zwei/runs/lauf-20260821-a/steps/1b/artifact-revisions"
const artifactSavePath = "/v1/tenants/tenant-welle-zwei/projects/projekt-welle-zwei/artifacts"
const inputPreviewPath = "/v1/tenants/tenant-welle-zwei/projects/projekt-welle-zwei/actions/request-input/preview"

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
      body: JSON.stringify({ action: "request-input", tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", run_id: "lauf-veraltet-20260821", step_id: "1b", expected_revision: 17 }),
    })

    await expect(response).rejects.toThrow("Unerwartete Testanfrage")
  })
})
