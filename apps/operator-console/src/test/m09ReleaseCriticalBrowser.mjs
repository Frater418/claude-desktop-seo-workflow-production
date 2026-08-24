#!/usr/bin/env node
// allow: SIZE_OK - This indivisible M09 harness owns strict fixtures, Chrome actions, and run evidence.
import { createReadStream, existsSync, statSync } from "node:fs"
import { mkdir, stat, writeFile } from "node:fs/promises"
import { createServer } from "node:http"
import { createRequire } from "node:module"
import { extname, join, normalize, resolve } from "node:path"

const tenantId = "tenant-browser-qa"
const alpha = { tenant_id: tenantId, project_id: "project-synthetic-alpha", run_id: "run-synthetic-alpha", step_id: "1b", expected_revision: 17 }
const beta = { tenant_id: tenantId, project_id: "project-synthetic-beta", run_id: "run-synthetic-beta", step_id: "2", expected_revision: 8 }
const hash = (letter) => letter.repeat(64)
const artifactByRevision = { 16: { content: "a", input: "b" }, 17: { content: "c", input: "d" }, 18: { content: "e", input: "f" } }
const artifact = (revision, artifactId, parentArtifactIds = []) => {
  const hashes = artifactByRevision[revision]
  if (hashes === undefined) throw new Error(`Unsupported synthetic artifact revision ${revision}.`)
  return { artifact_id: artifactId, ...alpha, revision, content_sha256: hash(hashes.content), input_hash: hash(hashes.input), storage_key: "outputs/synthetic-themenstruktur.md", created_at: "2026-08-21", parent_artifact_ids: parentArtifactIds }
}
const priorArtifact = artifact(16, "artifact-synthetic-0016")
const currentArtifact = artifact(17, "artifact-synthetic-0017", [priorArtifact.artifact_id])
const revisedArtifact = artifact(18, "artifact-synthetic-0018", [currentArtifact.artifact_id])
const viewport = { width: 1280, height: 900 }

function option(name, fallback) {
  const position = process.argv.indexOf(`--${name}`)
  if (position === -1) {
    if (fallback === undefined) throw new Error(`--${name} is required.`)
    return fallback
  }
  const value = process.argv[position + 1]
  if (value === undefined || value.startsWith("--")) throw new Error(`--${name} requires a value.`)
  return value
}

const dist = resolve(option("dist", "dist"))
const chrome = resolve(option("chrome", process.env.CHROME_BIN ?? "/opt/google/chrome/chrome"))
const output = resolve(option("output"))
const screenshotName = "m09-release-critical-desktop-1280x900.png"
const screenshotPath = join(output, screenshotName)
const resultPath = join(output, "m09-release-critical-browser-results.json")
const require = createRequire(process.env.PLAYWRIGHT_REQUIRE_FROM ?? import.meta.url)
const { chromium } = require("playwright")
const state = { artifactSaved: false, deliveryExports: new Map(), deliveryCreates: 0, deliveryDownloads: 0, diagnosticSequences: new Map(), released: false, requestLog: [] }
const result = {
  harness: "M09 release-critical desktop browser smoke",
  fixture: "Synthetic same-origin API fixtures only. No live customer, Notion, n8n, or deployment calls.",
  runAt: new Date().toISOString(),
  dist,
  chrome,
  output,
  viewport,
  checks: [],
  readbacks: [],
  capture: null,
  consoleErrors: [],
  failedRequests: [],
  responses: [],
  requestLog: [],
  error: null,
}

function check(value, detail) {
  if (!value) throw new Error(detail)
  result.checks.push(detail)
}

function readback(action, detail) {
  result.readbacks.push({ action, detail })
}

function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function sendJson(response, status, body) {
  response.writeHead(status, { "Cache-Control": "no-store", "Content-Type": "application/json; charset=utf-8" })
  response.end(JSON.stringify(body))
}

async function jsonBody(request) {
  let body = ""
  for await (const chunk of request) body += chunk
  return body === "" ? {} : JSON.parse(body)
}

function project(identity) {
  const name = identity.project_id === alpha.project_id ? "Synthetic Alpha" : "Synthetic Beta"
  return { tenant_id: tenantId, project_id: identity.project_id, name, customer: "Synthetic QA Workspace", current_step: identity.step_id, progress: "3 von 8 Schritten", blocker_count: identity.project_id === alpha.project_id ? 1 : 0, owner: "Heartweb Operator", next_action: identity.project_id === alpha.project_id ? "Informationsarchitektur pruefen" : "Cluster pruefen" }
}

function identity(pathname) {
  return pathname.includes(beta.project_id) ? beta : alpha
}

function actionName(pathname, suffix) {
  return pathname.match(new RegExp(`/actions/(start|approve|reject|request-revision|request-input|escalate|request-waiver)/${suffix}$`))?.[1] ?? null
}

function matchesAction(value, action, item) {
  return value?.action === action && value.tenant_id === tenantId && value.project_id === item.project_id && value.run_id === item.run_id && value.step_id === item.step_id && value.expected_revision === item.expected_revision
}

function deliveryPreview(scope) {
  const selectedDeliverables = [
    { artifact_id: "artifact-strategy-0001", content_sha256: hash("a"), deliverable_id: "strategy", output_path: "outputs/strategy.md", release_status: "released", role: "copywriter", step_id: "1" },
    { artifact_id: "artifact-design-0001", content_sha256: null, deliverable_id: "design", output_path: null, release_status: "draft", role: "developer", step_id: "1c" },
  ]
  if (scope === "checkpoint") return { scope, policy_eligible: true, missing_deliverable_ids: ["developer-handoff"], errors: [], selected_deliverables: selectedDeliverables }
  return { scope, policy_eligible: false, missing_deliverable_ids: ["developer-handoff"], errors: [{ code: "ERR_FINAL_RELEASE", message: "Die finale Uebergabe braucht freigegebene Lieferobjekte." }], selected_deliverables: selectedDeliverables }
}

function validDelivery(body) {
  if (!isRecord(body) || !isRecord(body.export_request) || !isRecord(body.notion_import_request) || !Array.isArray(body.role_package_requests)) return null
  const request = body.export_request
  const notion = body.notion_import_request
  const roles = body.role_package_requests
  const validRoles = roles.length === 2 && roles.map((entry) => isRecord(entry) ? entry.role : "").join(",") === "copywriter,developer" && roles.every((entry) => isRecord(entry) && typeof entry.role_handoff_manifest_id === "string" && entry.role_handoff_manifest_id.startsWith("role-handoff-"))
  const validRequest = request.tenant_id === tenantId && request.project_id === alpha.project_id && request.scope === "checkpoint" && request.draft_inclusion_policy === "include_explicit_drafts" && request.schema_version === "1.0.0" && Array.isArray(request.requested_role_packages) && request.requested_role_packages.join(",") === "copywriter,developer" && typeof request.created_at === "string" && typeof request.delivery_export_request_id === "string" && typeof request.idempotency_key === "string"
  const validNotion = typeof notion.customer_external_id === "string" && notion.customer_external_id.startsWith("customer-") && Array.isArray(notion.implementation_tasks) && notion.implementation_tasks.length > 0 && isRecord(notion.publication_registry) && Array.isArray(notion.publication_registry.urls) && notion.publication_registry.urls.every((url) => typeof url === "string" && url.startsWith("https://")) && typeof notion.notion_import_manifest_id === "string"
  if (!validRoles || !validRequest || !validNotion || typeof body.export_id !== "string" || typeof body.delivery_package_id !== "string" || typeof body.delivery_export_result_id !== "string" || !Number.isInteger(body.package_revision) || body.package_revision < 1) return null
  return { body, request, notion, roles }
}

function deliveryResult(delivery) {
  const { body, request, notion, roles } = delivery
  return { delivery_export_result_id: body.delivery_export_result_id, schema_version: "1.0.0", tenant_id: tenantId, project_id: alpha.project_id, delivery_export_request_id: request.delivery_export_request_id, export_id: body.export_id, delivery_package_id: body.delivery_package_id, source_snapshot_revision: request.source_snapshot_revision, replay_state: "created", export_path: `delivery/${body.export_id}/result.json`, zip_path: `delivery/${body.export_id}/archive.zip`, package_sha256: hash("a"), zip_sha256: hash("a"), zip_size_bytes: 2048, delivery_manifest: { manifest_id: body.delivery_package_id, relative_path: `delivery/${body.export_id}/manifest.json`, content_sha256: hash("a") }, role_handoff_manifests: roles.map((item) => ({ manifest_id: item.role_handoff_manifest_id, relative_path: `delivery/${body.export_id}/${item.role}.json`, content_sha256: hash("a") })), notion_import_manifest: { manifest_id: notion.notion_import_manifest_id, relative_path: `delivery/${body.export_id}/notion.json`, content_sha256: hash("a") }, created_at: request.created_at }
}

function deliveryRecord(delivery) {
  const { body, request, notion, roles } = delivery
  return { delivery_package_id: body.delivery_package_id, schema_version: "1.0.0", tenant_id: tenantId, project_id: alpha.project_id, export_id: body.export_id, scope: "checkpoint", source_snapshot_revision: request.source_snapshot_revision, source_records: [{ tenant_id: tenantId, project_id: alpha.project_id, source_kind: "project", source_record_id: alpha.project_id, source_revision: request.source_snapshot_revision, source_sha256: hash("a") }], required_deliverables: [{ deliverable_id: "strategy", source_record_id: "artifact-synthetic-0017", source_sha256: hash("a"), package_path: `delivery/${body.export_id}/strategy.md`, release_status: "released" }], missing_deliverables: ["developer-handoff"], package_paths: [`delivery/${body.export_id}/strategy.md`, `delivery/${body.export_id}/archive.zip`], package_sha256: hash("a"), zip_sha256: hash("a"), role_packages: roles.map((item) => ({ role: item.role, role_handoff_manifest_id: item.role_handoff_manifest_id, manifest_path: `delivery/${body.export_id}/${item.role}.json`, manifest_sha256: hash("a") })), notion_import_manifest: { notion_import_manifest_id: notion.notion_import_manifest_id, manifest_path: `delivery/${body.export_id}/notion.json`, manifest_sha256: hash("a") }, created_at: request.created_at, package_revision: body.package_revision, derived_status: "archived", task_assignment_manifest_path: `delivery/${body.export_id}/tasks.json`, quality_summary: { summary_path: `delivery/${body.export_id}/quality.json`, content_sha256: hash("a") }, export_manifest_path: `delivery/${body.export_id}/export.json`, checksums_path: `delivery/${body.export_id}/checksums.json` }
}

async function api(request, response, pathname, search) {
  const item = identity(pathname)
  const root = `/v1/tenants/${tenantId}/projects/${item.project_id}`
  const delivery = `${root}/delivery`
  const method = request.method ?? "GET"
  if (pathname === "/readyz" && method === "GET") return sendJson(response, 200, { data: { status: "ready" } }) || true
  if (pathname === `/v1/tenants/${tenantId}/projects` && method === "GET") return sendJson(response, 200, { data: [project(alpha), project(beta)] }) || true
  if (pathname === `${root}/runs/current` && method === "GET") return sendJson(response, 200, item) || true
  if (pathname === `${root}/runs/${item.run_id}` && method === "GET") return sendJson(response, 200, { data: { ...item, revision: item.expected_revision, status: "in_progress" } }) || true
  if (pathname === root && method === "GET") return sendJson(response, 200, { data: project(item) }) || true
  if (pathname === `${root}/workflow` && method === "GET") return sendJson(response, 200, { data: { tenant_id: tenantId, project_id: item.project_id, initial_edges: [{ from_step_id: "0", to_step_id: "1" }, { from_step_id: "1", to_step_id: "1b" }], sideflows: [{ step_id: "3b", status: "not_due" }] } }) || true
  if (pathname === `${root}/steps` && method === "GET") return sendJson(response, 200, { data: [{ ...item, status: "in_progress", blocker: item.project_id === alpha.project_id ? "Freigabe der Themenstruktur fehlt" : "Keine", next_action: project(item).next_action }] }) || true
  if (pathname === `${root}/tasks` && method === "GET") return sendJson(response, 200, { data: [{ ...item, task_id: `task-${item.project_id}`, title: item.project_id === alpha.project_id ? "Themenstruktur pruefen" : "Cluster pruefen", status: "open", owner: "Heartweb Operator", priority: "high", deadline: "2026-08-25", resolution: "Synthetische Pruefung abschliessen", dependency: "Freigabe der Themenstruktur" }] }) || true
  if (pathname === `${root}/artifacts` && method === "GET") return sendJson(response, 200, { data: item.project_id === alpha.project_id ? [priorArtifact, currentArtifact] : [] }) || true
  if (pathname === `${root}/releases` && method === "GET") return sendJson(response, 200, { data: state.released && item.project_id === alpha.project_id ? [{ release_id: "release-synthetic-001", ...alpha, gate_id: "GATE-1B", artifact_id: currentArtifact.artifact_id, artifact_sha256: currentArtifact.content_sha256, artifact_revision: currentArtifact.revision, approval_id: "approval-synthetic-001", policy_version: "synthetic-1", released_at: "2026-08-21", status: "released" }] : [] }) || true
  if (pathname === `${root}/runs/${item.run_id}/steps/${item.step_id}/artifact-revisions` && method === "GET") return sendJson(response, 200, { artifacts: state.artifactSaved ? [priorArtifact, currentArtifact, revisedArtifact] : [priorArtifact, currentArtifact] }) || true
  if (pathname === `${root}/gates` && method === "GET") return sendJson(response, 200, { data: [{ ...item, quality_gate_id: "GATE-1B", quality_gate_run_id: "gate-run-synthetic", artifact_id: currentArtifact.artifact_id, artifact_sha256: currentArtifact.content_sha256, artifact_revision: currentArtifact.revision, result: "passed", summary: "Maschinenpruefung bestanden", evidence: { struktur: "vollstaendig" }, findings: [], checker_version: "synthetic-checker-1.0", checked_at: "2026-08-21" }] }) || true
  if (pathname === `${root}/context-packages` && method === "GET") return sendJson(response, 200, { data: [{ ...item, title: "Synthetischer Nachweis", finding: "Lokale Testdaten vollstaendig" }] }) || true
  if (pathname === `${root}/integrations/status` && method === "GET") return sendJson(response, 200, { data: [{ tenant_id: tenantId, project_id: item.project_id, name: "Notion", mode: "simulated" }, { tenant_id: tenantId, project_id: item.project_id, name: "n8n", mode: "simulated" }] }) || true
  if (pathname === `${root}/diagnostic-traces` && method === "POST") {
    const value = await jsonBody(request)
    const traceId = `trace-${(item.project_id === alpha.project_id ? "a" : "b").repeat(32)}`
    if (value.tenant_id !== tenantId || value.project_id !== item.project_id || value.run_id !== item.run_id) return sendJson(response, 422, { detail: "invalid synthetic diagnostic start" }) || true
    state.diagnosticSequences.set(traceId, 0)
    return sendJson(response, 201, { ...value, trace_id: traceId, status: "active", replay: false }) || true
  }
  const diagnostic = pathname.match(new RegExp(`^${root}/diagnostic-traces/(trace-[a-f0-9]{32})/(entries|close)$`))
  if (diagnostic !== null && method === "POST") {
    const [, traceId, operation] = diagnostic
    const value = await jsonBody(request)
    if (operation === "entries") {
      const sequence = (state.diagnosticSequences.get(traceId) ?? 0) + 1
      state.diagnosticSequences.set(traceId, sequence)
      return sendJson(response, 201, { trace_id: traceId, operation_id: value.operation_id, sequence, replay: false }) || true
    }
    return sendJson(response, 200, { trace_id: traceId, close_id: value.close_id, closed_at: value.closed_at, first_failing_operation_id: null, last_successful_operation_id: null, status: "closed", replay: false }) || true
  }
  if (pathname === `${root}/artifacts/${priorArtifact.artifact_id}/content` && method === "GET") return sendJson(response, 200, { artifact: priorArtifact, content_base64: Buffer.from("# Revision 16\n\nVeralteter Inhalt.").toString("base64") }) || true
  if (pathname === `${root}/artifacts/${currentArtifact.artifact_id}/content` && method === "GET") return sendJson(response, 200, { artifact: currentArtifact, content_base64: Buffer.from("# Synthetische Themenstruktur\n\nPruefbarer Inhalt.").toString("base64") }) || true
  if (pathname === `${root}/artifacts` && method === "POST") {
    const value = await jsonBody(request)
    if (value.expected_parent_revision !== 17 || value.run_id !== alpha.run_id || value.primary_document !== "# Synthetische Themenstruktur\n\nPruefbarer Inhalt.\nAktualisierung.") return sendJson(response, 422, { detail: "invalid synthetic artifact payload" }) || true
    state.artifactSaved = true
    return sendJson(response, 200, { data: revisedArtifact }) || true
  }
  if (pathname === `${root}/artifact-revisions/compare` && method === "POST") {
    const value = await jsonBody(request)
    if (value.left_artifact_id !== currentArtifact.artifact_id || value.right_artifact_id !== revisedArtifact.artifact_id) return sendJson(response, 422, { detail: "invalid synthetic comparison payload" }) || true
    return sendJson(response, 200, { left_artifact: currentArtifact, right_artifact: revisedArtifact, unified_diff: "+ Aktualisierung." }) || true
  }
  if (pathname === `${root}/artifacts/${revisedArtifact.artifact_id}/validate` && method === "POST") {
    const value = await jsonBody(request)
    if (value.content_sha256 !== revisedArtifact.content_sha256 || value.revision !== 18) return sendJson(response, 422, { detail: "invalid synthetic validation payload" }) || true
    return sendJson(response, 200, { data: { result: "passed", report: "Maschinenpruefung bestanden" } }) || true
  }
  if (pathname === `${delivery}/preview` && method === "GET" && (search === "?scope=checkpoint" || search === "?scope=final")) return sendJson(response, 200, deliveryPreview(search.slice("?scope=".length))) || true
  if (pathname === `${delivery}/exports` && method === "GET") return sendJson(response, 200, { data: [...state.deliveryExports.values()].map(deliveryResult) }) || true
  if (pathname === `${delivery}/exports` && method === "POST") {
    const deliveryRequest = validDelivery(await jsonBody(request))
    if (deliveryRequest === null) return sendJson(response, 422, { detail: "invalid synthetic delivery payload" }) || true
    state.deliveryExports.set(deliveryRequest.body.export_id, deliveryRequest)
    state.deliveryCreates += 1
    return sendJson(response, 201, deliveryResult(deliveryRequest)) || true
  }
  const selectedExport = [...state.deliveryExports.values()].find((entry) => pathname === `${delivery}/exports/${entry.body.export_id}`)
  if (selectedExport !== undefined && method === "GET") return sendJson(response, 200, deliveryRecord(selectedExport)) || true
  const download = [...state.deliveryExports.values()].find((entry) => pathname === `${delivery}/exports/${entry.body.export_id}/download`)
  if (download !== undefined && method === "GET") {
    state.deliveryDownloads += 1
    response.writeHead(200, { "Cache-Control": "no-store", "Content-Disposition": `attachment; filename=\"${download.body.export_id}.zip\"`, "Content-Type": "application/zip", ETag: "m09-synthetic-zip" })
    response.end(Buffer.from("synthetic-zip"))
    return true
  }
  const previewAction = actionName(pathname, "preview")
  if (previewAction !== null && method === "POST") {
    const value = await jsonBody(request)
    if (!matchesAction(value, previewAction, item)) return sendJson(response, 422, { detail: "invalid synthetic action payload" }) || true
    return sendJson(response, 200, { allowed: true, blockers: [], consequence: { result: `Synthetische ${previewAction}-Folge.` }, intent: value, preview_hash: `${previewAction}-preview` }) || true
  }
  const confirmAction = actionName(pathname, "confirm")
  if (confirmAction !== null && method === "POST") {
    const value = await jsonBody(request)
    if (value.confirmed !== true || value.preview_hash !== `${confirmAction}-preview` || typeof value.idempotency_key !== "string" || !matchesAction(value.intent, confirmAction, item)) return sendJson(response, 422, { detail: "invalid synthetic confirm payload" }) || true
    if (confirmAction === "approve") state.released = true
    return sendJson(response, 200, { canonical: { decision: confirmAction }, preview_hash: `${confirmAction}-preview`, readback_urls: [root], replay: false }) || true
  }
  return false
}

function contentType(file) {
  switch (extname(file)) {
    case ".css": return "text/css; charset=utf-8"
    case ".html": return "text/html; charset=utf-8"
    case ".js": return "application/javascript; charset=utf-8"
    case ".svg": return "image/svg+xml"
    default: return "application/octet-stream"
  }
}

async function startServer() {
  const server = createServer(async (request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1")
    const method = request.method ?? "GET"
    state.requestLog.push({ method, pathname: url.pathname, search: url.search })
    try {
      if (url.pathname === "/readyz" || url.pathname.startsWith("/v1/")) {
        if (await api(request, response, url.pathname, url.search)) return
        return sendJson(response, 404, { detail: "strict synthetic API fixture rejected unknown path" })
      }
      if (method !== "GET" && method !== "HEAD") return sendJson(response, 405, { detail: "method not allowed" })
      const relativePath = normalize(url.pathname === "/" ? "index.html" : url.pathname).replace(/^[/\\]+/, "")
      const file = resolve(dist, relativePath)
      if (!file.startsWith(`${dist}/`) || !existsSync(file) || !statSync(file).isFile()) return sendJson(response, 404, { detail: "strict synthetic server rejected unexpected path" })
      response.writeHead(200, { "Cache-Control": "no-store", "Content-Type": contentType(file) })
      if (method === "HEAD") return response.end()
      createReadStream(file).pipe(response)
    } catch (error) {
      sendJson(response, 500, { detail: error instanceof Error ? error.message : "synthetic fixture failure" })
    }
  })
  await new Promise((resolveStarted, rejectStarted) => {
    server.once("error", rejectStarted)
    server.listen(0, "127.0.0.1", () => {
      server.off("error", rejectStarted)
      resolveStarted()
    })
  })
  const address = server.address()
  if (address === null || typeof address === "string") throw new Error("Synthetic server did not expose a TCP address.")
  return { server, base: `http://127.0.0.1:${address.port}` }
}

async function close(server) {
  await new Promise((resolveClosed, rejectClosed) => server.close((error) => error === undefined ? resolveClosed() : rejectClosed(error)))
}

async function navigate(page, route) {
  await page.getByRole("link", { name: route, exact: true }).click()
  await page.waitForTimeout(100)
  check(await page.locator(".workspace-frame").evaluate((element) => element.scrollTop === 0), `${route}: route reset readback`)
}

async function review(page, action, fields) {
  await page.getByLabel("Entscheidung waehlen", { exact: true }).selectOption(action)
  for (const [label, value] of Object.entries(fields)) await page.getByLabel(label, { exact: true }).fill(value)
  const preview = action === "approve" ? "Freigabe vorbereiten" : "Vorschau fuer Revision erstellen"
  await page.getByRole("button", { name: preview, exact: true }).click()
  const confirm = page.getByRole("button", { name: /bestaetigen/, exact: false })
  await confirm.click()
  await confirm.waitFor({ state: "detached" })
  await page.getByText("Kanonischer Stand aktualisiert", { exact: true }).waitFor()
  check(await page.getByLabel("Entscheidung waehlen", { exact: true }).isEnabled(), `${action}: canonical review readback`)
  readback(`review:${action}`, "Kanonischer Stand aktualisiert")
}

function taskJson() {
  return JSON.stringify([{ task_id: "task-browser-0001", assignment_id: "assignment-browser-0001", title: "Synthetische Browseraufgabe", status: "not_started", comments: "", source_assignee: "Browser QA", priority: "high", deadline: "2026-09-01", role: "copywriter", dependencies: [], artifact_relations: [currentArtifact.artifact_id], notion_user_id: "notion-user-browser-0001" }])
}

async function runScenario(browser, base) {
  const context = await browser.newContext({ acceptDownloads: true, deviceScaleFactor: 1, viewport })
  const page = await context.newPage()
  page.on("console", (message) => { if (message.type() === "error") result.consoleErrors.push(message.text()) })
  page.on("requestfailed", (request) => result.failedRequests.push({ url: request.url(), error: request.failure()?.errorText ?? "unknown" }))
  page.on("response", (response) => result.responses.push({ method: response.request().method(), status: response.status(), url: response.url() }))
  try {
    await page.goto(base, { waitUntil: "networkidle" })
    await page.getByRole("heading", { name: "Synthetic Alpha", exact: true }).waitFor()
    check(await page.getByRole("heading", { name: "Synthetic Alpha", exact: true }).isVisible(), "initial synthetic Alpha project visible")
    readback("initial project", "Synthetic Alpha heading visible")

    await navigate(page, "Projekte")
    await page.getByRole("button", { name: "Synthetic Beta waehlen", exact: true }).click()
    await page.getByRole("heading", { name: "Synthetic Beta", exact: true }).waitFor()
    check(await page.getByRole("heading", { name: "Synthetic Beta", exact: true }).isVisible(), "project selection: Synthetic Beta visible")
    readback("project selection", "Synthetic Beta heading visible")
    await page.getByRole("button", { name: "Synthetic Alpha waehlen", exact: true }).click()
    await page.getByRole("heading", { name: "Synthetic Alpha", exact: true }).waitFor()
    check(await page.getByRole("heading", { name: "Synthetic Alpha", exact: true }).isVisible(), "project selection: Synthetic Alpha visible")
    readback("project selection", "Synthetic Alpha heading visible")

    await navigate(page, "Workflow")
    await page.getByRole("button", { name: "Naechsten Schritt vorbereiten", exact: true }).click()
    await page.getByRole("button", { name: "Start verbindlich bestaetigen", exact: true }).click()
    await page.getByText("Readback abgeschlossen.", { exact: true }).waitFor()
    check(await page.getByText("Readback abgeschlossen.", { exact: true }).isVisible(), "workflow transition: canonical readback visible")
    readback("workflow transition", "Readback abgeschlossen.")

    await navigate(page, "Artefakte")
    await page.getByLabel("Ausgangsrevision", { exact: true }).selectOption(currentArtifact.artifact_id)
    await page.getByRole("button", { name: /synthetic-themenstruktur/i }).click()
    const artifactEditor = page.getByLabel("Artefaktinhalt bearbeiten", { exact: true })
    const expectedArtifactContent = "# Synthetische Themenstruktur\n\nPruefbarer Inhalt."
    await page.waitForFunction((expected) => document.querySelector('textarea[aria-label="Artefaktinhalt bearbeiten"]')?.value === expected, expectedArtifactContent)
    check(await artifactEditor.inputValue() === expectedArtifactContent, "artifact load: canonical revision content visible")
    readback("artifact load", "Canonical revision 17 content visible")

    await navigate(page, "Pruefungen und Freigaben")
    await review(page, "request-revision", { Begruendung: "Synthetischer Grund", Anweisungen: "Synthetische Anweisung", "Betroffene Abschnitte": "Abschnitt A", "Unveraenderliche Vorgaben": "Vorgabe A" })

    await navigate(page, "Uebergabe und Export")
    await page.getByRole("heading", { name: "Checkpoint-Vorschau", exact: true }).waitFor()
    await page.getByRole("heading", { name: "Finale Uebergabe", exact: true }).waitFor()
    await page.getByRole("heading", { name: "Exporthistorie", exact: true }).waitFor()
    await page.getByLabel("Exportumfang", { exact: true }).selectOption("checkpoint")
    await page.getByText("Zulaessig", { exact: true }).waitFor()
    check(await page.getByLabel("Exportumfang", { exact: true }).inputValue() === "checkpoint", "Delivery preview: checkpoint policy visible")
    readback("Delivery preview", "Checkpoint and final policy sections plus Exporthistorie visible")
    await page.getByLabel("Exportfolge", { exact: true }).fill("1")
    await page.getByLabel("Quell-Snapshot-Revision", { exact: true }).fill("17")
    await page.getByLabel("Paketrevision", { exact: true }).fill("1")
    await page.getByLabel("Entwurfsrichtlinie", { exact: true }).selectOption("include_explicit_drafts")
    const roleInputs = page.locator('input[type="checkbox"]')
    check(await roleInputs.count() === 2, "Delivery form: exactly two supported role inputs")
    await roleInputs.nth(0).check()
    await roleInputs.nth(1).check()
    await page.getByLabel("Externe Kundenkennung", { exact: true }).fill("customer-browser-qa")
    await page.getByLabel("Publikations-URLs", { exact: true }).fill("https://example.test/browser-qa")
    await page.getByLabel("Notion-Implementierungsaufgaben", { exact: true }).fill(taskJson())
    await page.getByRole("button", { name: "Notion-Uebergabe vorbereiten", exact: true }).click()
    await page.getByText("Diese Vorschau bereitet nur das manuelle Notion-Importpaket vor. Es werden keine externen Daten geschrieben.", { exact: true }).waitFor()
    check(state.deliveryCreates === 0, "Delivery preview: no export write")
    await page.getByRole("button", { name: "Export erstellen", exact: true }).click()
    await page.getByText("Export wurde erstellt und kanonisch gelesen.", { exact: true }).waitFor()
    await page.getByRole("heading", { name: "Ausgewaehlter Export", exact: true }).waitFor()
    check(await page.getByRole("heading", { name: "Exporthistorie", exact: true }).isVisible(), "Delivery create: history visible after canonical readback")
    check(state.deliveryCreates === 1 && state.deliveryExports.size === 1, "Delivery create: strict fixture stored one export")
    readback("Delivery create", "Export wurde erstellt und kanonisch gelesen.")
    const exportId = [...state.deliveryExports.keys()][0]
    await page.getByRole("button", { name: `Export ${exportId} waehlen`, exact: true }).click()
    await page.getByRole("heading", { name: "Ausgewaehlter Export", exact: true }).waitFor()
    check(await page.getByRole("button", { name: `Export ${exportId} waehlen`, exact: true }).getAttribute("aria-pressed") === "true", "Delivery history: created export selected")
    readback("Delivery history", "Created export selected from Exporthistorie")
    const download = page.waitForEvent("download")
    await page.getByRole("button", { name: "Gesamtes ZIP herunterladen", exact: true }).click()
    check((await download).suggestedFilename().endsWith(".zip"), "Delivery download: ZIP filename observed")
    check(state.deliveryDownloads === 1, "Delivery download: strict fixture served one ZIP")
    readback("Delivery download", "ZIP filename observed")
    await page.screenshot({ path: screenshotPath, scale: "css" })
    result.capture = { file: screenshotName, bytes: (await stat(screenshotPath)).size, viewport }
    check(result.consoleErrors.length === 0, "no console errors")
    check(result.failedRequests.every((request) => request.error === "net::ERR_ABORTED"), "no unexpected failed requests")
    check(result.responses.every((response) => response.status < 400), "no HTTP error responses")
    check(result.responses.every((response) => new URL(response.url).origin === base), "all browser responses remain same-origin")
  } finally {
    await context.close()
  }
}

await mkdir(output, { recursive: true })
let server
let browser
try {
  server = await startServer()
  browser = await chromium.launch({ executablePath: chrome, headless: true })
  await runScenario(browser, server.base)
} catch (error) {
  result.error = error instanceof Error ? error.message : String(error)
  throw error
} finally {
  if (browser !== undefined) await browser.close()
  if (server !== undefined) await close(server.server)
  result.requestLog = state.requestLog
  await writeFile(resultPath, `${JSON.stringify(result, null, 2)}\n`)
}
