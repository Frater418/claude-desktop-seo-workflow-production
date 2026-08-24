#!/usr/bin/env node
// allow: SIZE_OK - M05 Unit E requires one strict same-origin fixture and browser verifier.
import { mkdir, readFile, rm, writeFile } from "node:fs/promises"
import { createServer } from "node:http"
import { createRequire } from "node:module"
import { extname, resolve } from "node:path"

const tenantId = "tenant-browser-qa"
const projectId = "project-browser-qa"
const runId = "run-browser-qa"
const hash = "a".repeat(64)
const viewports = [{ width: 375, height: 812 }, { width: 768, height: 1024 }, { width: 1280, height: 900 }]
const routeName = "Uebergabe und Export"

function option(name, fallback) {
  const position = process.argv.indexOf(`--${name}`)
  if (position === -1) return fallback
  const value = process.argv[position + 1]
  if (value === undefined) throw new Error(`--${name} requires a value.`)
  return value
}

const dist = resolve(option("dist", "dist"))
const output = resolve(option("output", "../../00_admin/audits/2026-08-22-m05-unit-e"))
const screenshots = resolve(output, "screenshots")
const require = createRequire(process.env.PLAYWRIGHT_REQUIRE_FROM ?? import.meta.url)
const { chromium } = require("playwright")

function check(value, detail) {
  if (!value) throw new Error(detail)
}

function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function send(response, { status, body, headers = {} }) {
  response.writeHead(status, { "Cache-Control": "no-store", ...headers })
  response.end(body)
}

function json(response, status, body) {
  send(response, { status, body: JSON.stringify(body), headers: { "Content-Type": "application/json; charset=utf-8" } })
}

async function jsonBody(request) {
  let body = ""
  for await (const chunk of request) body += chunk
  return JSON.parse(body)
}

function workspace() {
  const current = { tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: "1b", expected_revision: 17 }
  const project = { tenant_id: tenantId, project_id: projectId, name: "Browser QA Projekt", customer: "Synthetische Heartweb QA", current_step: "1b", progress: "3 von 8 Schritten", blocker_count: 1, owner: "Heartweb Admin Operator", next_action: "Informationsarchitektur pruefen" }
  const artifact = { artifact_id: "artifact-browser-0001", ...current, revision: 17, content_sha256: hash, input_hash: "b".repeat(64), storage_key: "outputs/browser-qa.md", created_at: "2026-08-22T12:00:00Z" }
  const gate = { ...current, quality_gate_id: "gate-browser-0001", quality_gate_run_id: "gate-run-browser-0001", artifact_id: artifact.artifact_id, artifact_sha256: artifact.content_sha256, artifact_revision: artifact.revision, result: "passed", summary: "Maschinenpruefung bestanden", evidence: { struktur: "vollstaendig" }, findings: [], checker_version: "browser-qa-1.0", checked_at: "2026-08-22T12:00:00Z" }
  return { current, project, artifact, gate }
}

function preview(scope) {
  const selected = [{ artifact_id: "artifact-strategy-0001", content_sha256: hash, deliverable_id: "strategy", output_path: "outputs/strategy.md", release_status: "released", role: "copywriter", step_id: "1" }, { artifact_id: "artifact-design-0001", content_sha256: null, deliverable_id: "design", output_path: null, release_status: "draft", role: "developer", step_id: "1c" }]
  if (scope === "checkpoint") return { scope, policy_eligible: true, missing_deliverable_ids: ["developer-handoff"], errors: [], selected_deliverables: selected }
  return { scope, policy_eligible: false, missing_deliverable_ids: ["developer-handoff"], errors: [{ code: "ERR_FINAL_RELEASE", message: "Die finale Uebergabe braucht freigegebene Lieferobjekte." }], selected_deliverables: selected }
}

function validCheckpoint(body) {
  if (!isRecord(body) || !isRecord(body.export_request) || !isRecord(body.notion_import_request) || !Array.isArray(body.role_package_requests)) return null
  const request = body.export_request
  const notion = body.notion_import_request
  const roles = body.role_package_requests
  const validRoles = roles.length === 2 && roles.map((entry) => isRecord(entry) ? entry.role : "").join(",") === "copywriter,developer" && roles.every((entry) => isRecord(entry) && typeof entry.role_handoff_manifest_id === "string" && entry.role_handoff_manifest_id.startsWith("role-handoff-"))
  const validRequest = request.tenant_id === tenantId && request.project_id === projectId && request.scope === "checkpoint" && request.draft_inclusion_policy === "include_explicit_drafts" && request.schema_version === "1.0.0" && Array.isArray(request.requested_role_packages) && request.requested_role_packages.join(",") === "copywriter,developer" && typeof request.created_at === "string" && typeof request.delivery_export_request_id === "string" && typeof request.idempotency_key === "string"
  const validNotion = typeof notion.customer_external_id === "string" && notion.customer_external_id.startsWith("customer-") && Array.isArray(notion.implementation_tasks) && notion.implementation_tasks.length > 0 && isRecord(notion.publication_registry) && Array.isArray(notion.publication_registry.urls) && notion.publication_registry.urls.every((url) => typeof url === "string" && url.startsWith("https://")) && typeof notion.notion_import_manifest_id === "string"
  if (!validRoles || !validRequest || !validNotion || typeof body.export_id !== "string" || typeof body.delivery_package_id !== "string" || typeof body.delivery_export_result_id !== "string" || !Number.isInteger(body.package_revision) || body.package_revision < 1) return null
  return { body, request, notion, roles }
}

function deliveryResult(delivery) {
  const { body, request, notion, roles } = delivery
  return { delivery_export_result_id: body.delivery_export_result_id, schema_version: "1.0.0", tenant_id: tenantId, project_id: projectId, delivery_export_request_id: request.delivery_export_request_id, export_id: body.export_id, delivery_package_id: body.delivery_package_id, source_snapshot_revision: request.source_snapshot_revision, replay_state: "created", export_path: `delivery/${body.export_id}/result.json`, zip_path: `delivery/${body.export_id}/archive.zip`, package_sha256: hash, zip_sha256: hash, zip_size_bytes: 2048, delivery_manifest: { manifest_id: body.delivery_package_id, relative_path: `delivery/${body.export_id}/manifest.json`, content_sha256: hash }, role_handoff_manifests: roles.map((item) => ({ manifest_id: item.role_handoff_manifest_id, relative_path: `delivery/${body.export_id}/${item.role}.json`, content_sha256: hash })), notion_import_manifest: { manifest_id: notion.notion_import_manifest_id, relative_path: `delivery/${body.export_id}/notion.json`, content_sha256: hash }, created_at: request.created_at }
}

function deliveryRecord(delivery) {
  const { body, request, notion, roles } = delivery
  return { delivery_package_id: body.delivery_package_id, schema_version: "1.0.0", tenant_id: tenantId, project_id: projectId, export_id: body.export_id, scope: "checkpoint", source_snapshot_revision: request.source_snapshot_revision, source_records: [{ tenant_id: tenantId, project_id: projectId, source_kind: "project", source_record_id: projectId, source_revision: request.source_snapshot_revision, source_sha256: hash }], required_deliverables: [{ deliverable_id: "strategy", source_record_id: "artifact-browser-0001", source_sha256: hash, package_path: `delivery/${body.export_id}/strategy.md`, release_status: "released" }], missing_deliverables: ["developer-handoff"], package_paths: [`delivery/${body.export_id}/strategy.md`, `delivery/${body.export_id}/archive.zip`], package_sha256: hash, zip_sha256: hash, role_packages: roles.map((item) => ({ role: item.role, role_handoff_manifest_id: item.role_handoff_manifest_id, manifest_path: `delivery/${body.export_id}/${item.role}.json`, manifest_sha256: hash })), notion_import_manifest: { notion_import_manifest_id: notion.notion_import_manifest_id, manifest_path: `delivery/${body.export_id}/notion.json`, manifest_sha256: hash }, created_at: request.created_at, package_revision: body.package_revision, derived_status: "archived", task_assignment_manifest_path: `delivery/${body.export_id}/tasks.json`, quality_summary: { summary_path: `delivery/${body.export_id}/quality.json`, content_sha256: hash }, export_manifest_path: `delivery/${body.export_id}/export.json`, checksums_path: `delivery/${body.export_id}/checksums.json` }
}

function mime(path) {
  switch (extname(path)) {
    case ".css": return "text/css; charset=utf-8"
    case ".js": return "application/javascript; charset=utf-8"
    case ".svg": return "image/svg+xml"
    default: return "text/html; charset=utf-8"
  }
}

async function routeApi({ request, response, pathname, search, exports, requests }) {
  const { current, project, artifact, gate } = workspace()
  const root = `/v1/tenants/${tenantId}/projects/${projectId}`
  const delivery = `${root}/delivery`
  const method = request.method ?? "GET"
  if (pathname === "/readyz" && method === "GET") return json(response, 200, { data: { status: "ready" } }) || true
  if (pathname === `/v1/tenants/${tenantId}/projects` && method === "GET") return json(response, 200, { data: [project] }) || true
  if (pathname === `${root}/runs/current` && method === "GET") return json(response, 200, current) || true
  if (pathname === `${root}/runs/${runId}` && method === "GET") return json(response, 200, { data: { ...current, revision: current.expected_revision, status: "in_progress" } }) || true
  if (pathname === root && method === "GET") return json(response, 200, { data: project }) || true
  if (pathname === `${root}/workflow` && method === "GET") return json(response, 200, { data: { tenant_id: tenantId, project_id: projectId, initial_edges: [{ from_step_id: "0", to_step_id: "1" }], sideflows: [{ step_id: "3b", status: "not_due" }] } }) || true
  if (pathname === `${root}/steps` && method === "GET") return json(response, 200, { data: [{ ...current, status: "in_progress", blocker: "Freigabe der Themenstruktur fehlt", next_action: project.next_action }] }) || true
  if (pathname === `${root}/tasks` && method === "GET") return json(response, 200, { data: [{ ...current, task_id: "task-browser-0001", title: "Browserroute pruefen", status: "open", owner: "Heartweb Admin Operator", priority: "hoch", deadline: "2026-08-25", resolution: "Lieferroute pruefen", dependency: "Freigabe der Themenstruktur" }] }) || true
  if (pathname === `${root}/artifacts` && method === "GET") return json(response, 200, { data: [artifact] }) || true
  if (pathname === `${root}/releases` && method === "GET") return json(response, 200, { data: [] }) || true
  if (pathname === `${root}/gates` && method === "GET") return json(response, 200, { data: [gate] }) || true
  if (pathname === `${root}/context-packages` && method === "GET") return json(response, 200, { data: [{ ...current, title: "Synthetischer Nachweis", finding: "Lokale Browserdaten vollstaendig" }] }) || true
  if (pathname === `${root}/integrations/status` && method === "GET") return json(response, 200, { data: [{ tenant_id: tenantId, project_id: projectId, name: "Notion", mode: "simulated" }, { tenant_id: tenantId, project_id: projectId, name: "n8n", mode: "simulated" }] }) || true
  if (pathname === `${delivery}/preview` && method === "GET" && (search === "?scope=checkpoint" || search === "?scope=final")) return json(response, 200, preview(search.slice("?scope=".length))) || true
  if (pathname === `${delivery}/exports` && method === "GET") return json(response, 200, { data: [...exports.values()].map(deliveryResult) }) || true
  if (pathname === `${delivery}/exports` && method === "POST") {
    const parsed = validCheckpoint(await jsonBody(request))
    if (parsed === null) return json(response, 422, { message: "Synthetische Lieferung ist ungueltig." }) || true
    exports.set(parsed.body.export_id, parsed)
    requests.creates += 1
    return json(response, 201, deliveryResult(parsed)) || true
  }
  const selected = [...exports.values()].find((entry) => pathname === `${delivery}/exports/${entry.body.export_id}`)
  if (selected !== undefined && method === "GET") return json(response, 200, deliveryRecord(selected)) || true
  const download = [...exports.values()].find((entry) => pathname === `${delivery}/exports/${entry.body.export_id}/download`)
  if (download !== undefined && method === "GET") {
    requests.downloads += 1
    return send(response, { status: 200, body: Buffer.from("synthetic-zip"), headers: { "Content-Type": "application/zip", "Content-Disposition": `attachment; filename=\"${download.body.export_id}.zip\"`, ETag: "browser-qa-zip" } }) || true
  }
  return false
}

async function staticFile(response, pathname) {
  const file = resolve(dist, `.${pathname === "/" ? "/index.html" : pathname}`)
  if (!file.startsWith(`${dist}/`)) return json(response, 404, { message: "Unzulaessiger statischer Pfad." })
  try {
    send(response, { status: 200, body: await readFile(file), headers: { "Content-Type": mime(file) } })
  } catch {
    json(response, 404, { message: "Unbekannter synthetischer Pfad." })
  }
}

async function startServer() {
  const exports = new Map()
  const requests = { creates: 0, downloads: 0, log: [] }
  const server = createServer(async (request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1")
    requests.log.push({ method: request.method ?? "GET", pathname: url.pathname, search: url.search })
    try {
      if (await routeApi({ request, response, pathname: url.pathname, search: url.search, exports, requests })) return
      if ((request.method ?? "GET") !== "GET" && (request.method ?? "GET") !== "HEAD") return json(response, 405, { message: "Methode nicht erlaubt." })
      await staticFile(response, url.pathname)
    } catch (error) {
      json(response, 500, { message: error instanceof Error ? error.message : "Synthetischer Serverfehler." })
    }
  })
  await new Promise((resolveStarted) => server.listen(0, "127.0.0.1", resolveStarted))
  const address = server.address()
  if (address === null || typeof address === "string") throw new Error("Synthetic server did not expose a TCP address.")
  return { server, base: `http://127.0.0.1:${address.port}`, exports, requests }
}

function taskJson() {
  return JSON.stringify([{ task_id: "task-browser-0001", assignment_id: "assignment-browser-0001", title: "Synthetische Browseraufgabe", status: "not_started", comments: "", source_assignee: "Browser QA", priority: "high", deadline: "2026-09-01", role: "copywriter", dependencies: [], artifact_relations: ["artifact-browser-0001"], notion_user_id: "notion-user-browser-0001" }])
}

async function geometry(page, viewport) {
  const result = await page.evaluate(() => {
    const frame = document.querySelector(".workspace-frame")
    const evidence = document.querySelector(".evidence-panel")
    const footer = document.querySelector(".route-action-footer")
    if (!(frame instanceof HTMLElement) || !(evidence instanceof HTMLElement) || !(footer instanceof HTMLElement)) return null
    const frameBox = frame.getBoundingClientRect()
    const footerBox = footer.getBoundingClientRect()
    const initialEvidenceBox = evidence.getBoundingClientRect()
    frame.scrollTop = frame.scrollHeight
    const evidenceBox = evidence.getBoundingClientRect()
    const isReachable = (box) => box.top < frameBox.bottom && box.bottom > frameBox.top
    return { documentOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth, footerCovered: footerBox.top < frameBox.bottom - 1, evidenceReachable: isReachable(initialEvidenceBox) || isReachable(evidenceBox), scrollOwner: getComputedStyle(frame).overflowY, workspaceHeight: frame.clientHeight }
  })
  check(result !== null && !result.documentOverflow, `${viewport.width}: no document horizontal overflow`)
  check(result !== null && !result.footerCovered, `${viewport.width}: footer does not cover workspace`)
  check(result !== null && result.evidenceReachable, `${viewport.width}: ContextPanel reachable`)
  check(result !== null && result.scrollOwner === "auto", `${viewport.width}: existing workspace scroll owner retained`)
  check(result !== null && result.workspaceHeight > 0, `${viewport.width}: workspace remains visible above the footer`)
  return result
}

async function runViewport({ browser, base, capture, requests, viewport }) {
  const context = await browser.newContext({ acceptDownloads: true, deviceScaleFactor: 1, viewport })
  const page = await context.newPage()
  const evidence = { viewport, checks: [], consoleErrors: [], failedRequests: [], responses: [] }
  const checkViewport = (value, detail) => { check(value, detail); evidence.checks.push(detail) }
  page.on("console", (message) => { if (message.type() === "error") evidence.consoleErrors.push(message.text()) })
  page.on("requestfailed", (request) => evidence.failedRequests.push({ url: request.url(), error: request.failure()?.errorText ?? "unknown" }))
  page.on("response", (response) => evidence.responses.push({ method: response.request().method(), status: response.status(), url: response.url() }))
  try {
    await page.goto(base, { waitUntil: "networkidle" })
    await page.getByRole("link", { name: routeName, exact: true }).click()
    await page.getByRole("heading", { name: routeName, exact: true }).waitFor()
    await page.getByRole("heading", { name: "Checkpoint-Vorschau", exact: true }).waitFor()
    await page.getByRole("heading", { name: "Finale Uebergabe", exact: true }).waitFor()
    checkViewport(await page.getByRole("heading", { name: "Exporthistorie", exact: true }).isVisible(), `${viewport.width}: history visible`)
    checkViewport(await page.getByLabel("Exportumfang", { exact: true }).isVisible(), `${viewport.width}: export form visible`)
    checkViewport(await page.locator(".delivery-contract-gate").count() === 0 && await page.getByText("Sprint 5E Liefervertraege sind noch nicht installiert.", { exact: true }).count() === 0, `${viewport.width}: contract placeholder absent`)
    const scope = page.getByLabel("Exportumfang", { exact: true })
    await scope.focus()
    checkViewport(await scope.evaluate((element) => document.activeElement === element), `${viewport.width}: form focus reachable`)
    await page.keyboard.press("ArrowDown")
    checkViewport(await scope.inputValue() === "checkpoint", `${viewport.width}: scope selectable by keyboard`)
    await page.getByLabel("Exportfolge", { exact: true }).fill("1")
    await page.getByLabel("Quell-Snapshot-Revision", { exact: true }).fill("17")
    await page.getByLabel("Paketrevision", { exact: true }).fill("1")
    await page.getByLabel("Entwurfsrichtlinie", { exact: true }).selectOption("include_explicit_drafts")
    const roleInputs = page.locator('input[type="checkbox"]')
    checkViewport(await roleInputs.count() === 2, `${viewport.width}: only two supported role inputs`)
    await roleInputs.nth(0).focus()
    checkViewport(await roleInputs.nth(0).evaluate((element) => document.activeElement === element), `${viewport.width}: role control focus reachable`)
    await page.keyboard.press("Space")
    await roleInputs.nth(1).focus()
    await page.keyboard.press("Space")
    await page.getByLabel("Externe Kundenkennung", { exact: true }).fill("customer-browser-qa")
    await page.getByLabel("Publikations-URLs", { exact: true }).fill("https://example.test/browser-qa")
    await page.getByLabel("Notion-Implementierungsaufgaben", { exact: true }).fill(taskJson())
    const notion = page.getByRole("button", { name: "Notion-Uebergabe vorbereiten", exact: true })
    await notion.focus()
    checkViewport(await notion.evaluate((element) => document.activeElement === element), `${viewport.width}: footer Notion preview reachable`)
    await page.keyboard.press("Enter")
    await page.getByText("Diese Vorschau bereitet nur das manuelle Notion-Importpaket vor. Es werden keine externen Daten geschrieben.", { exact: true }).waitFor()
    checkViewport(requests.creates === 0, `${viewport.width}: Notion preview performs no write`)
    const create = page.getByRole("button", { name: "Export erstellen", exact: true })
    await create.focus()
    checkViewport(await create.evaluate((element) => document.activeElement === element), `${viewport.width}: create action reachable by keyboard`)
    await page.keyboard.press("Enter")
    await page.getByText("Export wurde erstellt und kanonisch gelesen.", { exact: true }).waitFor()
    await page.getByRole("heading", { name: "Ausgewaehlter Export", exact: true }).waitFor()
    checkViewport(await page.getByRole("button", { name: "Export unveraendert wiederholen", exact: true }).isVisible(), `${viewport.width}: canonical retry control visible`)
    const wholeZip = page.getByRole("button", { name: "Gesamtes ZIP herunterladen", exact: true })
    await wholeZip.focus()
    checkViewport(await wholeZip.evaluate((element) => document.activeElement === element), `${viewport.width}: whole ZIP action reachable by keyboard`)
    const download = page.waitForEvent("download")
    await page.keyboard.press("Enter")
    checkViewport((await download).suggestedFilename().endsWith(".zip"), `${viewport.width}: whole ZIP download uses a ZIP filename`)
    const labels = await page.locator("button").allTextContents()
    checkViewport(!labels.some((label) => /(?:copywriter|developer|notion).*(?:herunterladen|download)|(?:ordner|folder).*(?:oeffnen|open)|(?:notion|n8n).*(?:synchronisieren|uebertragen|live)/i.test(label)), `${viewport.width}: no unsupported role, Notion, folder, or live action`)
    checkViewport(requests.downloads === requests.creates, `${viewport.width}: only the whole ZIP endpoint downloads`)
    await page.locator(".workspace-frame").evaluate((element) => { element.scrollTop = 0 })
    checkViewport(await page.getByRole("heading", { name: routeName, exact: true }).evaluate((heading) => {
      const frame = document.querySelector(".workspace-frame")
      if (!(frame instanceof HTMLElement)) return false
      const frameBox = frame.getBoundingClientRect()
      const headingBox = heading.getBoundingClientRect()
      return frame.clientHeight > 0 && headingBox.top < frameBox.bottom && headingBox.bottom > frameBox.top
    }), `${viewport.width}: delivery workspace visible above footer`)
    await page.screenshot({ path: capture, scale: "css" })
    const image = await readFile(capture)
    checkViewport(image.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])), `${viewport.width}: PNG capture signature valid`)
    checkViewport(image.readUInt32BE(16) === viewport.width && image.readUInt32BE(20) === viewport.height, `${viewport.width}: capture dimensions match viewport`)
    evidence.geometry = await geometry(page, viewport)
    checkViewport(evidence.consoleErrors.length === 0, `${viewport.width}: no console errors`)
    checkViewport(evidence.failedRequests.length === 0, `${viewport.width}: no failed requests`)
    checkViewport(evidence.responses.every((response) => response.status < 400), `${viewport.width}: no failed HTTP response`)
    checkViewport(evidence.responses.filter((response) => new URL(response.url).pathname.startsWith("/v1/")).every((response) => new URL(response.url).origin === base), `${viewport.width}: Task 6 requests remain same-origin`)
    evidence.deliveryActions = { creates: requests.creates, downloads: requests.downloads }
    return evidence
  } finally {
    await context.close()
  }
}

async function close(server) {
  await new Promise((resolveClosed, rejectClosed) => server.close((error) => error === undefined ? resolveClosed() : rejectClosed(error)))
}

const result = { route: routeName, runAt: new Date().toISOString(), dist, output, viewports, browser: { executable: process.env.CHROME_BIN ?? "/opt/google/chrome/chrome" }, captures: [], cells: [], checks: [], consoleErrors: [], failedRequests: [], requestLog: [], error: null }
await rm(output, { force: true, recursive: true })
await mkdir(screenshots, { recursive: true })
const server = await startServer()
let browser
try {
  browser = await chromium.launch({ executablePath: result.browser.executable, headless: true })
  for (const viewport of viewports) {
    server.exports.clear()
    server.requests.creates = 0
    server.requests.downloads = 0
    const capture = resolve(screenshots, `delivery-route-${viewport.width}x${viewport.height}.png`)
    const evidence = await runViewport({ browser, base: server.base, capture, requests: server.requests, viewport })
    result.captures.push({ file: capture, viewport })
    result.cells.push({ ...evidence, capture })
    result.checks.push(...evidence.checks)
    result.consoleErrors.push(...evidence.consoleErrors)
    result.failedRequests.push(...evidence.failedRequests)
  }
  result.requestLog = server.requests.log
} catch (error) {
  result.error = error instanceof Error ? error.message : String(error)
  throw error
} finally {
  if (browser !== undefined) await browser.close()
  await close(server.server)
  await writeFile(resolve(output, "delivery-route-browser-results.json"), `${JSON.stringify(result, null, 2)}\n`)
}
