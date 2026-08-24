#!/usr/bin/env node
import { createReadStream, existsSync, statSync } from "node:fs"
import { createServer } from "node:http"
import { extname, join, normalize, resolve } from "node:path"

const values = Object.fromEntries(process.argv.slice(2).reduce((items, value, index, source) => value.startsWith("--") ? [...items, [value.slice(2), source[index + 1]]] : items, []))
const staticRoot = resolve(values.static)
const port = Number(values.port)
const tenant = "tenant-browser-qa"
const alpha = { tenant_id: tenant, project_id: "project-synthetic-alpha", run_id: "run-synthetic-alpha", step_id: "1b", expected_revision: 17 }
const beta = { tenant_id: tenant, project_id: "project-synthetic-beta", run_id: "run-synthetic-beta", step_id: "2", expected_revision: 8 }
const intake = { tenant_id: tenant, project_id: "project-synthetic-intake", run_id: "run-synthetic-intake", step_id: "0", expected_revision: 1 }
const hex = (letter) => letter.repeat(64)
const hashByRevision = { 16: { content: "a", input: "b" }, 17: { content: "c", input: "d" }, 18: { content: "e", input: "f" } }
const record = (revision, id, parents = []) => { const hashes = hashByRevision[revision]; if (hashes === undefined) throw new Error(`Unsupported synthetic revision ${revision}`); return { artifact_id: id, ...alpha, revision, content_sha256: hex(hashes.content), input_hash: hex(hashes.input), storage_key: "outputs/synthetic-themenstruktur.md", created_at: "2026-08-21", parent_artifact_ids: parents } }
const prior = record(16, "artifact-synthetic-0016")
const current = record(17, "artifact-synthetic-0017", [prior.artifact_id])
const revised = record(18, "artifact-synthetic-0018", [current.artifact_id])
for (const item of [prior, current, revised]) for (const hash of [item.content_sha256, item.input_hash]) if (!/^[0-9a-f]{64}$/.test(hash)) throw new Error("Synthetic artifact hashes must be lowercase hexadecimal SHA-256 values.")
const log = []
let saved = false
let accepted = false
let released = false

function send(response, status, body) { response.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }); response.end(JSON.stringify(body)) }
function project(identity) {
  const name = identity.project_id === alpha.project_id ? "Synthetic Alpha" : identity.project_id === beta.project_id ? "Synthetic Beta" : "Synthetic Intake"
  return { tenant_id: tenant, project_id: identity.project_id, name, customer: "Synthetic QA Workspace", current_step: identity.step_id, progress: identity.project_id === intake.project_id ? "0 von 8 Schritten" : "3 von 8 Schritten", blocker_count: identity.project_id === alpha.project_id ? 1 : 0, owner: "Heartweb Operator", next_action: identity.project_id === intake.project_id ? "Kickoff starten" : "Informationsarchitektur pruefen" }
}
function identity(pathname) { return pathname.includes(beta.project_id) ? beta : pathname.includes(intake.project_id) ? intake : alpha }
function body(request) { return new Promise((resolveBody, reject) => { let data = ""; request.on("data", (part) => { data += part }); request.on("end", () => { try { resolveBody(data === "" ? {} : JSON.parse(data)) } catch (error) { reject(error) } }) }) }
function matches(value, action, item) { return value?.action === action && value.tenant_id === tenant && value.project_id === item.project_id && value.run_id === item.run_id && value.step_id === item.step_id && value.expected_revision === item.expected_revision }
function actionName(pathname, suffix) { return pathname.match(new RegExp(`/actions/(start|approve|reject|request-revision|request-input|escalate|request-waiver)/${suffix}$`))?.[1] ?? null }

async function api(request, response, pathname) {
  const item = identity(pathname)
  const root = `/v1/tenants/${tenant}/projects/${item.project_id}`
  if (pathname === "/readyz" && request.method === "GET") return send(response, 200, { data: { status: "ready" } })
  if (pathname === `/v1/tenants/${tenant}/projects` && request.method === "GET") return send(response, 200, { data: accepted ? [project(alpha), project(beta), project(intake)] : [project(alpha), project(beta)] })
  if (pathname === `${root}/runs/current` && request.method === "GET") return send(response, 200, item)
  if (pathname === `${root}/runs/${item.run_id}` && request.method === "GET") return send(response, 200, { data: { ...item, revision: item.expected_revision, status: "in_progress" } })
  if (pathname === root && request.method === "GET") return send(response, 200, { data: project(item) })
  if (pathname === `${root}/workflow` && request.method === "GET") return send(response, 200, { data: { tenant_id: tenant, project_id: item.project_id, initial_edges: [{ from_step_id: "0", to_step_id: "1" }, { from_step_id: "1", to_step_id: "1b" }], sideflows: [{ step_id: "3b", status: "not_due" }] } })
  if (pathname === `${root}/steps` && request.method === "GET") return send(response, 200, { data: [{ ...item, status: "in_progress", blocker: item.project_id === alpha.project_id ? "Freigabe der Themenstruktur fehlt" : "Keine", next_action: project(item).next_action }] })
  if (pathname === `${root}/tasks` && request.method === "GET") return send(response, 200, { data: item.project_id === intake.project_id ? [] : [{ ...item, task_id: `task-${item.project_id}`, title: item.project_id === alpha.project_id ? "Themenstruktur pruefen" : "Cluster pruefen", status: "open", owner: "Heartweb Operator", priority: "high", deadline: "2026-08-25", resolution: "Synthetische Pruefung abschliessen", dependency: "Freigabe der Themenstruktur" }] })
  if (pathname === `${root}/artifacts` && request.method === "GET") return send(response, 200, { data: item.project_id === alpha.project_id ? [prior, current] : [] })
  if (pathname === `${root}/releases` && request.method === "GET") return send(response, 200, { data: released && item.project_id === alpha.project_id ? [{ release_id: "release-synthetic-001", ...alpha, gate_id: "GATE-1B", artifact_id: current.artifact_id, artifact_sha256: current.content_sha256, artifact_revision: current.revision, approval_id: "approval-synthetic-001", policy_version: "synthetic-1", released_at: "2026-08-21", status: "released" }] : [] })
  if (pathname === `${root}/runs/${item.run_id}/steps/${item.step_id}/artifact-revisions` && request.method === "GET") return send(response, 200, { artifacts: saved ? [prior, current, revised] : [prior, current] })
  if (pathname === `${root}/gates` && request.method === "GET") return send(response, 200, { data: item.project_id === intake.project_id ? [] : [{ ...item, quality_gate_id: "GATE-1B", quality_gate_run_id: "gate-run-synthetic", artifact_id: current.artifact_id, artifact_sha256: current.content_sha256, artifact_revision: current.revision, result: "passed", summary: "Maschinenpruefung bestanden", evidence: { struktur: "vollstaendig" }, findings: [], checker_version: "synthetic-checker-1.0", checked_at: "2026-08-21" }] })
  if (pathname === `${root}/context-packages` && request.method === "GET") return send(response, 200, { data: item.project_id === intake.project_id ? [] : [{ ...item, title: "Synthetischer Nachweis", finding: "Lokale Testdaten vollstaendig" }] })
  if (pathname === `${root}/integrations/status` && request.method === "GET") return send(response, 200, { data: [{ tenant_id: tenant, project_id: item.project_id, name: "Notion", mode: "simulated" }, { tenant_id: tenant, project_id: item.project_id, name: "n8n", mode: "simulated" }] })
  if (pathname === `${root}/artifacts/${prior.artifact_id}/content` && request.method === "GET") { await new Promise((resolveDelay) => setTimeout(resolveDelay, 300)); return send(response, 200, { artifact: prior, content_base64: Buffer.from("# Revision 16\n\nVeralteter Inhalt.").toString("base64") }) }
  if (pathname === `${root}/artifacts/${current.artifact_id}/content` && request.method === "GET") return send(response, 200, { artifact: current, content_base64: Buffer.from("# Synthetische Themenstruktur\n\nPruefbarer Inhalt.").toString("base64") })
  if (pathname === `${root}/artifacts` && request.method === "POST") { const value = await body(request); if (value.expected_parent_revision !== 17 || value.run_id !== alpha.run_id || value.primary_document !== "# Synthetische Themenstruktur\n\nPruefbarer Inhalt.\nAktualisierung.") return send(response, 422, { detail: "invalid synthetic artifact payload" }); saved = true; return send(response, 200, { data: revised }) }
  if (pathname === `${root}/artifact-revisions/compare` && request.method === "POST") { const value = await body(request); if (value.left_artifact_id !== current.artifact_id || value.right_artifact_id !== revised.artifact_id) return send(response, 422, { detail: "invalid synthetic comparison payload" }); return send(response, 200, { left_artifact: current, right_artifact: revised, unified_diff: "+ Aktualisierung." }) }
  if (pathname === `${root}/artifacts/${revised.artifact_id}/validate` && request.method === "POST") { const value = await body(request); if (value.content_sha256 !== revised.content_sha256 || value.revision !== 18) return send(response, 422, { detail: "invalid synthetic validation payload" }); return send(response, 200, { data: { result: "passed", report: "Maschinenpruefung bestanden" } }) }
  if (pathname === `/v1/tenants/${tenant}/intake/preview` && request.method === "POST") return send(response, 200, { data: { preview_hash: hex("a"), source_sha256: hex("b"), reviewed: { tenant_id: tenant, project_id: intake.project_id, project_name: "Synthetic Intake", title: "Synthetic Intake", project_v2: { version: 2 } }, missing_fields: [], eligible: true, previewed_at: "2026-08-21" } })
  if (pathname === `/v1/tenants/${tenant}/intake/accept` && request.method === "POST") { const value = await body(request); if (value.confirmed !== true || value.preview_hash !== hex("a") || value.source_sha256 !== hex("b")) return send(response, 422, { detail: "invalid synthetic intake payload" }); accepted = true; return send(response, 200, { data: { tenant_id: tenant, project_id: intake.project_id } }) }
  const preview = actionName(pathname, "preview")
  if (preview !== null && request.method === "POST") { const value = await body(request); if (!matches(value, preview, item)) return send(response, 422, { detail: "invalid synthetic action payload" }); return send(response, 200, { allowed: true, blockers: [], consequence: { result: `Synthetische ${preview}-Folge.` }, intent: value, preview_hash: `${preview}-preview` }) }
  const confirm = actionName(pathname, "confirm")
  if (confirm !== null && request.method === "POST") { const value = await body(request); if (value.confirmed !== true || value.preview_hash !== `${confirm}-preview` || typeof value.idempotency_key !== "string" || !matches(value.intent, confirm, item)) return send(response, 422, { detail: "invalid synthetic confirm payload" }); if (confirm === "approve") released = true; return send(response, 200, { canonical: { decision: confirm }, preview_hash: `${confirm}-preview`, readback_urls: [root], replay: false }) }
  return false
}

const types = { ".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml" }
createServer(async (request, response) => {
  const pathname = new URL(request.url ?? "/", "http://127.0.0.1").pathname
  log.push({ method: request.method, pathname })
  try {
    if (pathname === "/qa-log" && request.method === "GET") return send(response, 200, { data: log })
    if (pathname === "/readyz" || pathname.startsWith(`/v1/tenants/${tenant}/`)) { const handled = await api(request, response, pathname); if (handled !== false) return }
    if (request.method !== "GET" && request.method !== "HEAD") return send(response, 405, { detail: "method not allowed" })
    const file = join(staticRoot, normalize(pathname === "/" ? "index.html" : pathname).replace(/^[/\\]+/, ""))
    if (!file.startsWith(staticRoot) || !existsSync(file) || !statSync(file).isFile()) return send(response, 404, { detail: "strict synthetic server rejected unexpected path" })
    response.writeHead(200, { "Content-Type": types[extname(file)] ?? "application/octet-stream", "Cache-Control": "no-store" })
    if (request.method === "HEAD") return response.end()
    createReadStream(file).pipe(response)
  } catch (error) { send(response, 500, { detail: error instanceof Error ? error.message : "synthetic fixture failure" }) }
}).listen(port, "127.0.0.1", () => process.stdout.write(`strict synthetic server ready on ${port}\n`))
