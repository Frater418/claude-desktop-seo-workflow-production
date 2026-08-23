import { describe, expect, it } from "vitest"
import type { DeliveryCreateRequest } from "../../generated/api-types"
import { buildDeliveryCreateRequest, buildOrReuseDeliveryCreateRequest, type DeliveryCreateInput, type ValidatedDeliveryCreateInput, validateDeliveryCreateInput } from "./deliveryRequest"

const createdAt = "2026-08-22T10:00:00.123Z"
const implementationTasksJson = JSON.stringify([
  {
    task_id: "task-delivery-0001",
    assignment_id: "assignment-delivery-0001",
    title: "Landingpage pruefen",
    status: "not_started",
    comments: "",
    source_assignee: "Redaktion",
    priority: "high",
    deadline: "2026-09-01",
    role: "copywriter",
    dependencies: ["task-predecessor-0001"],
    artifact_relations: ["artifact-delivery-0001"],
    notion_user_id: "notion-user-delivery-0001",
  },
])

function validInput(overrides: Partial<DeliveryCreateInput> = {}): DeliveryCreateInput {
  return {
    tenantId: "tenant-acme",
    projectId: "project-acme",
    scope: "checkpoint",
    exportSequence: "7",
    sourceSnapshotRevision: "3",
    packageRevision: "2",
    draftInclusionPolicy: "include_explicit_drafts",
    selectedRoles: ["developer", "copywriter"],
    customerExternalId: "customer-acme",
    publicationUrls: "https://example.test/first\nhttps://example.test/second",
    implementationTasksJson,
    createdAt,
    ...overrides,
  }
}

function validForm(input: DeliveryCreateInput): ValidatedDeliveryCreateInput {
  const validation = validateDeliveryCreateInput(input)
  if (validation.kind === "valid") return validation.input
  throw new TypeError(validation.errors.join("\n"))
}

function request(input: DeliveryCreateInput): Promise<DeliveryCreateRequest> {
  return buildDeliveryCreateRequest({ input: validForm(input), crypto: globalThis.crypto })
}

function stableIds(requestValue: DeliveryCreateRequest): readonly string[] {
  return [
    requestValue.delivery_export_result_id,
    requestValue.delivery_package_id,
    requestValue.export_id,
    requestValue.export_request.delivery_export_request_id,
    requestValue.export_request.idempotency_key,
    requestValue.notion_import_request.notion_import_manifest_id,
    requestValue.notion_import_request.publication_registry.publication_registry_record_id,
    ...requestValue.role_package_requests.map((item) => item.role_handoff_manifest_id),
  ]
}

describe("Delivery request construction", () => {
  it("builds identical stable IDs when tenant project scope and sequence are unchanged", async () => {
    const given = validInput()

    const first = await request(given)
    const second = await request(validInput({ createdAt: "2026-08-22T10:01:00Z" }))

    expect(stableIds(second)).toEqual(stableIds(first))
    expect(second.export_request.created_at).toBe("2026-08-22T10:01:00Z")
  })

  it("changes every stable ID when the export sequence changes", async () => {
    const given = await request(validInput())

    const changed = await request(validInput({ exportSequence: "8" }))

    expect(stableIds(changed)).not.toEqual(stableIds(given))
    expect(stableIds(changed).every((identifier, index) => identifier !== stableIds(given)[index])).toBe(true)
  })

  it("changes every stable ID when the scope changes", async () => {
    const given = await request(validInput())

    const changed = await request(validInput({ scope: "final", draftInclusionPolicy: "exclude_drafts" }))

    expect(stableIds(changed).every((identifier, index) => identifier !== stableIds(given)[index])).toBe(true)
  })

  it("preserves revisions and the injected RFC3339 timestamp while sorting role requests", async () => {
    const given = validInput()

    const built = await request(given)

    expect(built.export_request.source_snapshot_revision).toBe(3)
    expect(built.package_revision).toBe(2)
    expect(built.export_request.created_at).toBe(createdAt)
    expect(built.export_request.requested_role_packages).toEqual(["copywriter", "developer"])
    expect(built.role_package_requests.map((item) => item.role)).toEqual(["copywriter", "developer"])
    expect(new Set(built.role_package_requests.map((item) => item.role_handoff_manifest_id)).size).toBe(2)
  })

  it("keeps stable IDs independent from customer and task display values", async () => {
    const given = await request(validInput())
    const changedTasks = implementationTasksJson.replace("Landingpage pruefen", "Andere Anzeige")

    const changed = await request(validInput({ customerExternalId: "customer-other", implementationTasksJson: changedTasks }))

    expect(stableIds(changed)).toEqual(stableIds(given))
  })

  it("keeps checkpoint explicit without inventing a final-only role or draft policy", () => {
    const explicitCheckpoint = validateDeliveryCreateInput(validInput({ selectedRoles: ["copywriter"] }))
    const absentScope = validateDeliveryCreateInput(validInput({ scope: "" }))

    expect(explicitCheckpoint.kind).toBe("valid")
    expect(absentScope).toMatchObject({ kind: "invalid", errors: expect.arrayContaining([expect.stringContaining("Exportumfang")]) })
  })

  it("rejects final input that includes drafts", () => {
    const result = validateDeliveryCreateInput(validInput({ scope: "final", draftInclusionPolicy: "include_explicit_drafts" }))

    expect(result).toMatchObject({ kind: "invalid", errors: expect.arrayContaining([expect.stringContaining("Entwuerfe")]) })
  })

  it.each([
    ["Copywriter", ["developer"]],
    ["Developer", ["copywriter"]],
  ])("rejects final input when %s is missing", (_role, selectedRoles) => {
    const result = validateDeliveryCreateInput(validInput({ scope: "final", selectedRoles, draftInclusionPolicy: "exclude_drafts" }))

    expect(result).toMatchObject({ kind: "invalid", errors: expect.arrayContaining([expect.stringContaining("Finale Uebergabe")]) })
  })

  it.each([
    ["malformed task JSON", validInput({ implementationTasksJson: "{" }), "JSON"],
    ["an unknown task field", validInput({ implementationTasksJson: implementationTasksJson.replace("\"title\"", "\"unbekannt\": \"x\", \"title\"") }), "unbekanntes Feld"],
    ["duplicate task dependencies", validInput({ implementationTasksJson: implementationTasksJson.replace("[\"task-predecessor-0001\"]", "[\"task-predecessor-0001\", \"task-predecessor-0001\"]") }), "doppelte Abhaengigkeiten"],
    ["duplicate artifact relations", validInput({ implementationTasksJson: implementationTasksJson.replace("[\"artifact-delivery-0001\"]", "[\"artifact-delivery-0001\", \"artifact-delivery-0001\"]") }), "doppelte Artefaktbeziehungen"],
    ["an invalid task deadline", validInput({ implementationTasksJson: implementationTasksJson.replace("2026-09-01", "2026-02-30") }), "gueltiges RFC3339-Datum"],
    ["an invalid task status", validInput({ implementationTasksJson: implementationTasksJson.replace("not_started", "queued") }), "Status"],
    ["an invalid task priority", validInput({ implementationTasksJson: implementationTasksJson.replace("\"high\"", "\"urgent\"") }), "Prioritaet"],
    ["an unsupported task role", validInput({ implementationTasksJson: implementationTasksJson.replace("copywriter", "reviewer") }), "Rolle"],
    ["an invalid notion user", validInput({ implementationTasksJson: implementationTasksJson.replace("notion-user-delivery-0001", "notion-user-invalid") }), "Notion-Benutzerkennung"],
    ["an invalid customer ID", validInput({ customerExternalId: "customer-Acme" }), "Kundenkennung"],
    ["a duplicate publication URL", validInput({ publicationUrls: "https://example.test/first\nhttps://example.test/first" }), "doppelt"],
    ["a non-HTTPS publication URL", validInput({ publicationUrls: "http://example.test/first" }), "HTTPS"],
    ["a nonpositive export sequence", validInput({ exportSequence: "0" }), "Exportfolge"],
    ["a timestamp without a timezone", validInput({ createdAt: "2026-08-22T10:00:00" }), "Zeitzone"],
  ])("rejects %s", (_description, input, expectedMessage) => {
    const result = validateDeliveryCreateInput(input)

    expect(result).toMatchObject({ kind: "invalid", errors: expect.arrayContaining([expect.stringContaining(expectedMessage)]) })
  })

  it("rejects duplicate task and assignment IDs across implementation tasks", () => {
    const duplicateTasks = `[${implementationTasksJson.slice(1, -1)},${implementationTasksJson.slice(1, -1)}]`

    const result = validateDeliveryCreateInput(validInput({ implementationTasksJson: duplicateTasks }))

    expect(result).toMatchObject({ kind: "invalid", errors: expect.arrayContaining([expect.stringContaining("Aufgaben- oder Zuordnungskennungen")]) })
  })

  it("accepts a nullable Notion user mapping", () => {
    const result = validateDeliveryCreateInput(validInput({ implementationTasksJson: implementationTasksJson.replace("\"notion-user-delivery-0001\"", "null") }))

    expect(result).toMatchObject({ kind: "valid", input: { implementationTasks: [{ notion_user_id: null }] } })
  })

  it("reuses the exact existing request object for a retry", async () => {
    const first = await request(validInput())
    const retry = await buildOrReuseDeliveryCreateRequest({ existingRequest: first, input: validForm(validInput({ createdAt: "2027-01-01T00:00:00Z" })), crypto: globalThis.crypto })

    expect(retry).toBe(first)
    expect(JSON.stringify(retry)).toBe(JSON.stringify(first))
  })
})
