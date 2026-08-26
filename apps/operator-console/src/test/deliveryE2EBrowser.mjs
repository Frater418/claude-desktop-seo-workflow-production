#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises"
import { resolve } from "node:path"
import { chromium } from "playwright-core"

const base = process.env.M06_BASE_URL
const evidenceDir = process.env.M07_EVIDENCE_DIR
const checkpointDownload = process.env.M06_CHECKPOINT_DOWNLOAD
const screenshotReference = process.env.M07_SCREENSHOT_REFERENCE
const chromeBin = process.env.CHROME_BIN
const routeName = "Uebergabe und Export"
const expectedIds = {
  delivery_export_request_id: "delivery-export-request-66ff1f053918e8c41f3a5f57bea8863c",
  export_id: "delivery-export-aa3335ee5ab249b02303c7abb8074b34",
  delivery_package_id: "delivery-package-eb5b530fdb3e45f038676536d1d22517",
  delivery_export_result_id: "delivery-export-result-99f28508f91a282db3bcc9e000dd8150",
  idempotency_key: "idem-8f79262566f7f176266069cc24898f5a",
  notion_import_manifest_id: "notion-import-61d3557d1959a0bd66ef7d1ce9d53154",
  publication_registry_record_id: "publication-registry-9940e186e04b93d5643fb0544e83a6a1",
  copywriter_manifest_id: "role-handoff-b7e688134993e41473c213f9c8d0b17a",
  developer_manifest_id: "role-handoff-43c4a35d025de3da8ec7c06d8081bf02",
}

function check(value, detail) {
  if (!value) throw new Error(detail)
}

function required(value, name) {
  check(typeof value === "string" && value !== "", `${name} is required.`)
  return value
}

function taskJson() {
  return JSON.stringify([{
    task_id: "task-implementation-0001",
    assignment_id: "assignment-implementation-0001",
    title: "Publish delivery package",
    status: "not_started",
    comments: "",
    source_assignee: "",
    priority: "high",
    deadline: "2026-09-01",
    role: "copywriter",
    dependencies: [],
    artifact_relations: [],
  }])
}

const result = {
  route: routeName,
  viewport: { width: 1280, height: 900 },
  fixed_time: "2026-08-22T10:15:30.000Z",
  checkpoint_request_body: "",
  retry_request_body: "",
  checkpoint_export_id: "",
  create_status: 0,
  retry_status: 0,
  notion_post_count: 0,
  screenshot: "delivery-center-1280x900.png",
  checkpoint_download: "checkpoint.zip",
  requests: [],
  console_errors: [],
  failed_requests: [],
  steps_projection: null,
  diagnostic_trace_id: "",
  diagnostic_close_id: "",
  diagnostic_closed_at: "",
  diagnostic_status: "",
  error: null,
}

const root = required(base, "M06_BASE_URL")
const output = required(evidenceDir, "M07_EVIDENCE_DIR")
const downloadPath = required(checkpointDownload, "M06_CHECKPOINT_DOWNLOAD")
const relativeScreenshot = required(screenshotReference, "M07_SCREENSHOT_REFERENCE")
await mkdir(output, { recursive: true })
const browser = await chromium.launch(chromeBin === undefined ? { channel: "chrome", headless: true } : { executablePath: chromeBin, headless: true })
const context = await browser.newContext({ acceptDownloads: true, deviceScaleFactor: 1, viewport: result.viewport })
const page = await context.newPage()
const postBodies = []
const createStatuses = []
const requestUrls = []
let browserObservationRecorded = false
page.on("console", (message) => { if (message.type() === "error") result.console_errors.push(message.text()) })
page.on("requestfailed", (request) => result.failed_requests.push({ method: request.method(), url: request.url(), error: request.failure()?.errorText ?? "unknown" }))
page.on("request", (request) => {
  const url = new URL(request.url())
  requestUrls.push(url)
  result.requests.push({ method: request.method(), path: url.pathname })
  if (request.method() === "POST" && url.pathname.endsWith("/delivery/exports")) postBodies.push(request.postData() ?? "")
})
page.on("response", (response) => {
  const request = response.request()
  if (request.method() === "POST" && new URL(response.url()).pathname.endsWith("/delivery/exports")) createStatuses.push(response.status())
})

try {
  await page.clock.setFixedTime(new Date(result.fixed_time))
  const diagnosticUrl = new URL(root)
  diagnosticUrl.searchParams.set("diagnostic_source", "automated")
  diagnosticUrl.searchParams.set("diagnostic_scenario", "m06-delivery")
  await page.goto(diagnosticUrl.toString(), { waitUntil: "networkidle" })
  await page.getByRole("heading", { name: "Projektübersicht", exact: true }).waitFor()
  const stepsResponse = page.waitForResponse((response) => new URL(response.url()).pathname.endsWith("/steps"))
  const diagnosticCreateResponse = page.waitForResponse((response) => {
    const request = response.request()
    return request.method() === "POST" && new URL(response.url()).pathname.endsWith("/diagnostic-traces")
  })
  const [, stepsCreated, diagnosticCreated] = await Promise.all([
    page.getByRole("button", { name: / öffnen$/ }).click(),
    stepsResponse,
    diagnosticCreateResponse,
  ])
  result.steps_projection = await stepsCreated.json()
  check(diagnosticCreated.status() === 201, "Automated diagnostic trace must be created.")
  const diagnosticTrace = await diagnosticCreated.json()
  check(typeof diagnosticTrace.trace_id === "string" && /^trace-[a-f0-9]{32}$/.test(diagnosticTrace.trace_id), "Diagnostic create response must contain a trace ID.")
  result.diagnostic_trace_id = diagnosticTrace.trace_id
  check(result.steps_projection.data.every((step) => typeof step.blocker === "string" && typeof step.next_action === "string"), "Step projection must include readable blocker and next action fields.")
  await page.getByRole("button", { name: "Uebergabe", exact: true }).click()
  await page.getByRole("heading", { name: routeName, exact: true }).waitFor()
  await page.getByRole("heading", { name: "Checkpoint-Vorschau", exact: true }).waitFor()
  await page.getByRole("heading", { name: "Finale Uebergabe", exact: true }).waitFor()
  await page.getByRole("heading", { name: "Exporthistorie", exact: true }).waitFor()
  const missingDeveloperHandoff = page.getByText(/developer-handoff/i, { exact: false }).first()
  await missingDeveloperHandoff.waitFor()
  check((await missingDeveloperHandoff.innerText()).toLowerCase().includes("developer-handoff"), "Final preview must name developer-handoff as missing.")
  const scope = page.getByLabel("Exportumfang", { exact: true })
  await scope.selectOption("checkpoint")
  await page.getByLabel("Exportfolge", { exact: true }).fill("1")
  await page.getByLabel("Quell-Snapshot-Revision", { exact: true }).fill("11")
  await page.getByLabel("Paketrevision", { exact: true }).fill("7")
  await page.getByLabel("Entwurfsrichtlinie", { exact: true }).selectOption("exclude_drafts")
  const roles = page.locator('input[type="checkbox"]')
  check(await roles.count() === 2, "Delivery Center must expose exactly Copywriter and Developer roles.")
  await roles.nth(0).check()
  await roles.nth(1).check()
  await page.getByLabel("Externe Kundenkennung", { exact: true }).fill("customer-delivery-0001")
  await page.getByLabel("Publikations-URLs", { exact: true }).fill("https://example.test/publish/delivery")
  await page.getByLabel("Notion-Implementierungsaufgaben", { exact: true }).fill(taskJson())
  await page.getByRole("button", { name: "Notion-Uebergabe vorbereiten", exact: true }).click()
  await page.getByText("Diese Vorschau bereitet nur das manuelle Notion-Importpaket vor. Es werden keine externen Daten geschrieben.", { exact: true }).waitFor()
  result.notion_post_count = postBodies.length
  check(result.notion_post_count === 0, "Notion preview must not create a Delivery export.")
  const createResponse = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/delivery/exports"))
  await page.getByRole("button", { name: "Export erstellen", exact: true }).click()
  check((await createResponse).status() === 201, "Checkpoint create must return HTTP 201.")
  await page.getByText("Export wurde erstellt und kanonisch gelesen.", { exact: true }).waitFor()
  await page.getByRole("heading", { name: "Ausgewaehlter Export", exact: true }).waitFor()
  const download = page.waitForEvent("download")
  await page.getByRole("button", { name: "Gesamtes ZIP herunterladen", exact: true }).click()
  const saved = await download
  check(saved.suggestedFilename() === "project-demo-checkpoint-r7.zip", "Checkpoint ZIP filename must be canonical.")
  await saved.saveAs(downloadPath)
  const retryResponse = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/delivery/exports") && response.status() === 200)
  await page.getByRole("button", { name: "Export unveraendert wiederholen", exact: true }).click()
  check((await retryResponse).status() === 200, "Checkpoint replay must return HTTP 200.")
  await page.getByText("Vorhandener Export wurde unveraendert wiederverwendet.", { exact: true }).waitFor()
  check(postBodies.length === 2 && postBodies[0] === postBodies[1], "Checkpoint replay must reuse byte-identical request JSON.")
  const checkpoint = JSON.parse(postBodies[0])
  result.checkpoint_request_body = postBodies[0]
  result.retry_request_body = postBodies[1]
  result.checkpoint_export_id = checkpoint.export_id
  result.create_status = createStatuses[0] ?? 0
  result.retry_status = createStatuses[1] ?? 0
  check(checkpoint.export_id === expectedIds.export_id, "Checkpoint export ID is not deterministic.")
  check(checkpoint.export_request.created_at === result.fixed_time, "Checkpoint caller time is not fixed.")
  check(checkpoint.export_request.delivery_export_request_id === expectedIds.delivery_export_request_id, "Checkpoint request ID is not deterministic.")
  check(checkpoint.export_request.idempotency_key === expectedIds.idempotency_key, "Checkpoint idempotency key is not deterministic.")
  check(checkpoint.delivery_package_id === expectedIds.delivery_package_id && checkpoint.delivery_export_result_id === expectedIds.delivery_export_result_id, "Checkpoint package/result IDs are not deterministic.")
  check(checkpoint.notion_import_request.notion_import_manifest_id === expectedIds.notion_import_manifest_id && checkpoint.notion_import_request.publication_registry.publication_registry_record_id === expectedIds.publication_registry_record_id, "Checkpoint Notion IDs are not deterministic.")
  check(checkpoint.role_package_requests[0].role_handoff_manifest_id === expectedIds.copywriter_manifest_id && checkpoint.role_package_requests[1].role_handoff_manifest_id === expectedIds.developer_manifest_id, "Checkpoint role manifest IDs are not deterministic.")
  await page.screenshot({ path: resolve(output, result.screenshot), scale: "css" })
  check(requestUrls.every((url) => url.origin === root), "Browser made an external request.")
  check(requestUrls.every((url) => !/(?:notion|n8n|agentseo)/i.test(url.href)), "Browser contacted a prohibited integration endpoint.")
  check(result.console_errors.length === 0, "Browser console contained errors.")
  check(result.failed_requests.length === 0, "Browser contained failed requests.")
  const browserObservation = await page.evaluate(async ({ screenshot, traceId }) => {
    const response = await fetch(`/v1/tenants/tenant-demo/projects/project-demo/diagnostic-traces/${traceId}/entries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        operation_id: "operation-0004-browser-observation",
        occurred_at: "2026-08-22T10:15:30Z",
        action: "browser_observation",
        route: "/v1/tenants/tenant-demo/projects/project-demo/delivery/exports",
        api_method: "POST",
        api_status: 200,
        error_code: null,
        remediation: null,
        expected_actions: ["create_delivery_export", "download_delivery_export"],
        rendered_actions: ["create_delivery_export", "download_delivery_export"],
        disabled_actions: [],
        evidence_references: [{ kind: "screenshot", relative_path: screenshot }],
      }),
    })
    const payload = await response.json()
    return { operationId: payload.operation_id, status: response.status, traceId: payload.trace_id }
  }, { screenshot: relativeScreenshot, traceId: result.diagnostic_trace_id })
  check(browserObservation.status === 201 && browserObservation.traceId === result.diagnostic_trace_id && browserObservation.operationId === "operation-0004-browser-observation", "Normalized browser observation must be appended once.")
  browserObservationRecorded = true
  const diagnosticCloseResponse = page.waitForResponse((response) => {
    const request = response.request()
    return request.method() === "POST" && new URL(response.url()).pathname.endsWith(`/diagnostic-traces/${result.diagnostic_trace_id}/close`)
  })
  await page.evaluate(() => window.dispatchEvent(new Event("pagehide")))
  const diagnosticClosed = await diagnosticCloseResponse
  check(diagnosticClosed.status() === 200, "Pagehide diagnostic trace close must return HTTP 200.")
  const closedTrace = await diagnosticClosed.json()
  check(closedTrace.trace_id === result.diagnostic_trace_id && closedTrace.status === "closed" && typeof closedTrace.close_id === "string" && typeof closedTrace.closed_at === "string", "Diagnostic close response must be canonical.")
  result.diagnostic_close_id = closedTrace.close_id
  result.diagnostic_closed_at = closedTrace.closed_at
  result.diagnostic_status = closedTrace.status
  const diagnosticStatus = page.locator('[aria-label="Automatische Diagnose"]')
  await diagnosticStatus.waitFor({ state: "attached" })
  check(await diagnosticStatus.getAttribute("data-state") === "closed", "Diagnostic trace status must be closed after pagehide.")
  check((await diagnosticStatus.textContent())?.includes("Diagnoseprotokoll geschlossen.") === true, "Closed diagnostic trace text must remain in the technical details.")
} catch (error) {
  if (result.diagnostic_trace_id !== "" && !browserObservationRecorded) {
    try {
      await page.evaluate(async (traceId) => {
        await fetch(`/v1/tenants/tenant-demo/projects/project-demo/diagnostic-traces/${traceId}/entries`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            operation_id: "operation-0004-browser-observation",
            occurred_at: "2026-08-22T10:15:30Z",
            action: "browser_observation",
            route: "/v1/tenants/tenant-demo/projects/project-demo/delivery/exports",
            api_method: "POST",
            api_status: 599,
            error_code: "ERROR_QA_HARNESS_FAILURE",
            remediation: "inspect-qa-harness",
            expected_actions: ["create_delivery_export", "download_delivery_export"],
            rendered_actions: ["create_delivery_export", "download_delivery_export"],
            disabled_actions: [],
            evidence_references: [],
          }),
        })
      }, result.diagnostic_trace_id)
      browserObservationRecorded = true
    } catch {
      result.diagnostic_status = "failure-observation-unavailable"
    }
  }
  const visibleText = await page.locator("body").innerText().catch(() => "Visible UI unavailable.")
  const observedRequests = result.requests.slice(-50).map((request) => `${request.method} ${request.path}`).join("\n")
  const originalMessage = error instanceof Error ? error.message : String(error)
  result.error = `${originalMessage}\nVisible UI:\n${visibleText.slice(0, 4000)}\nObserved requests:\n${observedRequests}`
  throw new Error(result.error, { cause: error })
} finally {
  await context.close()
  await browser.close()
  const auditResult = { route: result.route, viewport: result.viewport, fixed_time: result.fixed_time, checkpoint_export_id: result.checkpoint_export_id, create_status: result.create_status, retry_status: result.retry_status, screenshot: result.screenshot, diagnostic: { trace_id: result.diagnostic_trace_id, close_id: result.diagnostic_close_id, closed_at: result.diagnostic_closed_at, status: result.diagnostic_status } }
  await writeFile(resolve(output, "browser-results.json"), `${JSON.stringify(auditResult, null, 2)}\n`)
}

process.stdout.write(JSON.stringify(result))
