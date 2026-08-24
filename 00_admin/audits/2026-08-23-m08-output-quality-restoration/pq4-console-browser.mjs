import { mkdir, stat, writeFile } from "node:fs/promises"
import { createRequire } from "node:module"
import { resolve } from "node:path"

const require = createRequire("/tmp/opencode/operator-console-playwright/node_modules/playwright/package.json")
const { chromium } = require("playwright")
const output = resolve("00_admin/audits/2026-08-23-m08-output-quality-restoration")
const screenshot = resolve(output, "pq4-console-review-desktop.png")
const payloadScreenshot = resolve(output, "pq4-console-review-payload.png")
const confirmationScreenshot = resolve(output, "pq4-console-review-confirmation.png")
const resultPath = resolve(output, "pq4-console-browser-results.json")
const base = "http://127.0.0.1:4175"
const tenant = "tenant-pq4-qa"
const project = "project-pq4-qa"
const run = "run-pq4-qa"
const step = "4b"
const hash = (character) => character.repeat(64)
const identity = { tenant_id: tenant, project_id: project, run_id: run, step_id: step }
const primary = { artifact_id: "artifact-page-spec-primary", ...identity, revision: 2, content_sha256: hash("a"), input_hash: hash("c"), storage_key: "outputs/page-spec.json", created_at: "2026-08-23T17:50:00Z", parent_artifact_ids: ["artifact-parent"] }
const supporting = { artifact_id: "artifact-staging-evidence-supporting", ...identity, revision: 2, content_sha256: hash("b"), input_hash: hash("c"), storage_key: "outputs/staging-evidence.json", created_at: "2026-08-23T17:50:00Z", parent_artifact_ids: ["artifact-parent"] }
const pageSpec = { page_id: "synthetic-step4b", sections: [{ role: "hero", heading: "Lokale Pflegeberatung" }], conversion: { primary_cta: "Beratung anfragen" }, local: { market: "DE" } }
const evidence = { evidence_source: "local_simulated", staging_url: "https://staging.invalid/synthetic", tools: [{ tool: "lighthouse", execution: "simulated" }] }
const projectData = { tenant_id: tenant, project_id: project, name: "PQ4 Synthetic Step 4B", customer: "Synthetic QA Workspace", current_step: step, progress: "8 von 8 Schritten", blocker_count: 0, owner: "Heartweb Operator", next_action: "Schritt 4B pruefen" }
const encode = (value) => Buffer.from(JSON.stringify(value), "utf8").toString("base64")
const response = (body, status = 200) => ({ status, contentType: "application/json; charset=utf-8", body: JSON.stringify(body) })
const results = { run_at: new Date().toISOString(), viewport: { width: 1280, height: 900 }, checks: [], console_errors: [], failed_requests: [], http_errors: [], screenshots: ["pq4-console-review-desktop.png", "pq4-console-review-payload.png", "pq4-console-review-confirmation.png"] }
const check = (condition, label) => { if (!condition) throw new Error(label); results.checks.push(label) }

await mkdir(output, { recursive: true })
const browser = await chromium.launch({ executablePath: "/opt/google/chrome/chrome", headless: true })
const page = await browser.newPage({ viewport: results.viewport })
page.on("console", (message) => { if (message.type() === "error") results.console_errors.push(message.text()) })
page.on("requestfailed", (request) => { if (request.failure()?.errorText !== "net::ERR_ABORTED") results.failed_requests.push(request.url()) })
page.on("response", (received) => { if (received.status() >= 400) results.http_errors.push(`${received.status()} ${received.url()}`) })
await page.route("**/readyz", (route) => route.fulfill(response({ data: { status: "ready" } })))
await page.route(`**/v1/tenants/${tenant}/projects`, (route) => route.fulfill(response({ data: [projectData] })))
await page.route(`**/v1/tenants/${tenant}/projects/${project}`, (route) => route.fulfill(response({ data: projectData })))
await page.route(`**/v1/tenants/${tenant}/projects/${project}/**`, async (route) => {
  const path = new URL(route.request().url()).pathname
  const root = `/v1/tenants/${tenant}/projects/${project}`
  if (path === `${root}/runs/current`) return route.fulfill(response({ ...identity, expected_revision: 2 }))
  if (path === `${root}/runs/${run}`) return route.fulfill(response({ data: { ...identity, revision: 2, status: "in_progress" } }))
  if (path === `${root}/workflow`) return route.fulfill(response({ data: { tenant_id: tenant, project_id: project, initial_edges: [{ from_step_id: "4a", to_step_id: "4b" }], sideflows: [{ step_id: "3b", status: "not_due" }] } }))
  if (path === `${root}/steps`) return route.fulfill(response({ data: [{ ...identity, status: "in_progress", blocker: "Keine", next_action: "Schritt 4B pruefen" }] }))
  if (path === `${root}/tasks`) return route.fulfill(response({ data: [] }))
  if (path === `${root}/artifacts`) return route.fulfill(response({ data: [supporting, primary] }))
  if (path === `${root}/gates`) return route.fulfill(response({ data: [{ ...identity, quality_gate_id: "qg-step-4b-local", quality_gate_run_id: "qgr-step-4b-local", artifact_id: primary.artifact_id, artifact_sha256: primary.content_sha256, artifact_revision: 2, result: "passed", summary: "Lokale Vorpruefung bestanden", evidence: { provenance: "local_simulated", validator_result: "simulated:fixture-validated" }, findings: [], checker_version: "step4b-local-1.0", checked_at: "2026-08-23T17:50:00Z" }] }))
  if (path === `${root}/context-packages`) return route.fulfill(response({ data: [{ ...identity, title: "Lokaler PQ4-Nachweis", finding: "Nur lokale simulierte Vertragspruefung" }] }))
  if (path === `${root}/integrations/status`) return route.fulfill(response({ data: [{ tenant_id: tenant, project_id: project, name: "Notion", mode: "simulated" }] }))
  if (path === `${root}/diagnostic-traces`) {
    const start = route.request().postDataJSON()
    return route.fulfill(response({ ...start, trace_id: `trace-${"1".repeat(32)}`, status: "active", replay: false }))
  }
  if (path.endsWith(`/diagnostic-traces/trace-${"1".repeat(32)}/entries`)) {
    const entry = route.request().postDataJSON()
    return route.fulfill(response({ trace_id: `trace-${"1".repeat(32)}`, operation_id: entry.operation_id, sequence: 1, replay: false }))
  }
  if (path.endsWith(`/diagnostic-traces/trace-${"1".repeat(32)}/close`)) {
    const close = route.request().postDataJSON()
    return route.fulfill(response({ trace_id: `trace-${"1".repeat(32)}`, close_id: close.close_id, closed_at: close.closed_at, status: "closed", first_failing_operation_id: null, last_successful_operation_id: null, replay: false }))
  }
  if (path === `${root}/artifacts/${primary.artifact_id}/content`) return route.fulfill(response({ artifact: primary, content_base64: encode(pageSpec) }))
  if (path === `${root}/artifacts/${supporting.artifact_id}/content`) return route.fulfill(response({ artifact: supporting, content_base64: encode(evidence) }))
  if (path === `${root}/actions/approve/preview`) return route.fulfill(response({ allowed: true, blockers: [], consequence: { result: "Synthetische Freigabe fuer exakt gebundene Revision 2." }, intent: route.request().postDataJSON(), preview_hash: "approve-pq4-preview" }))
  if (path === `${root}/actions/approve/confirm`) return route.fulfill(response({ canonical: { decision: "approve" }, preview_hash: "approve-pq4-preview", readback_urls: [root], replay: false }))
  return route.fulfill(response({ detail: `unexpected ${path}` }, 404))
})

try {
  await page.goto(base, { waitUntil: "networkidle" })
  await page.getByRole("link", { name: "Pruefungen und Freigaben", exact: true }).click()
  await page.waitForTimeout(500)
  if (await page.getByRole("heading", { name: "Exakte Schritt-4-Review-Unterlagen", exact: true }).count() === 0) throw new Error(await page.locator("body").innerText())
  await page.getByRole("heading", { name: "Exakte Schritt-4-Review-Unterlagen", exact: true }).waitFor()
  check((await page.locator('pre[aria-label="Kanonisches Primaerdokument"]').textContent())?.includes("synthetic-step4b") === true, "exact primary payload visible")
  check((await page.locator('pre[aria-label="Unterstuetzendes Dokument"]').textContent())?.includes("local_simulated") === true, "exact supporting evidence visible")
  check(await page.getByRole("heading", { name: "Lokale oder simulierte Nachweisquelle", exact: true }).isVisible(), "local provenance warning visible")
  const approve = page.getByRole("button", { name: "Freigabe vorbereiten", exact: true })
  check(await approve.isEnabled(), "approval enabled only after exact payload and gate binding")
  const geometry = await page.evaluate(() => ({ document_overflow: document.body.scrollWidth > document.body.clientWidth, pre_overflow: [...document.querySelectorAll("pre")].every((item) => item.scrollWidth <= item.clientWidth || getComputedStyle(item).overflowX !== "visible") }))
  check(!geometry.document_overflow && geometry.pre_overflow, "desktop payload layout has contained horizontal overflow")
  await page.screenshot({ path: screenshot, fullPage: true })
  await page.getByRole("heading", { name: "Exakte Schritt-4-Review-Unterlagen", exact: true }).locator("..").screenshot({ path: payloadScreenshot })
  await approve.click()
  await page.getByText("Synthetische Freigabe fuer exakt gebundene Revision 2.", { exact: true }).waitFor()
  check(await page.getByRole("button", { name: "Freigabe bestaetigen", exact: true }).isVisible(), "approval preview requires explicit confirmation")
  await page.locator(".workspace-frame").evaluate((element) => { element.scrollTop = element.scrollHeight })
  await page.screenshot({ path: confirmationScreenshot, fullPage: true })
  check(results.console_errors.length === 0, `no console errors: ${results.console_errors.join(" | ")} HTTP: ${results.http_errors.join(" | ")}`)
  check(results.failed_requests.length === 0, "no failed requests")
  results.screenshot_bytes = { desktop: (await stat(screenshot)).size, payload: (await stat(payloadScreenshot)).size, confirmation: (await stat(confirmationScreenshot)).size }
  await writeFile(resultPath, `${JSON.stringify(results, null, 2)}\n`)
} finally {
  await browser.close()
}
