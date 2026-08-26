import { describe, expect, it } from "vitest"

import { parseContext, parseGates } from "./readModels"

const tenantId = "tenant-heartweb"
const projectId = "project-cl-performance-bundesweite-sichtbarkeit-fur-b2b-3d-druck"

function boundRecord(): Record<string, unknown> {
  return {
    tenant_id: tenantId,
    project_id: projectId,
    run_id: "run-neutral-0001",
    step_id: "0",
  }
}

describe("parseContext", () => {
  it("derives operator labels from a canonical Context Package", () => {
    const value = {
      data: [{
        ...boundRecord(),
        context_package_id: "context-e6465c43592ffe4f189c2ce7",
        target_revision: 2,
        sources: [{ source_id: "prompt-0" }, { source_id: "contract-0" }, { source_id: "intake-0" }],
      }],
    }

    expect(parseContext(value, tenantId, projectId)).toEqual([{
      tenantId,
      projectId,
      runId: "run-neutral-0001",
      stepId: "0",
      title: "Kontextpaket für Schritt 0",
      finding: "3 gebundene Quellen für Zielrevision 2.",
    }])
  })

  it("keeps legacy operator labels readable", () => {
    const value = { data: [{ ...boundRecord(), title: "Quellenpaket", finding: "Lokale Quellen vollständig" }] }

    expect(parseContext(value, tenantId, projectId)[0]).toMatchObject({
      title: "Quellenpaket",
      finding: "Lokale Quellen vollständig",
    })
  })
})

describe("parseGates", () => {
  it("projects the canonical Quality Gate Run into the selected project", () => {
    const value = {
      data: [{
        quality_gate_run_id: "qgr-0-domain-contract-6e506448",
        quality_gate_id: "qg-domain-contract",
        human_gate_id: "GATE-0",
        tenant_id: tenantId,
        run_id: "run-neutral-0001",
        step_id: "0",
        artifact_id: "artifact-e9ed0fbaf1842ffa",
        artifact_sha256: "a".repeat(64),
        artifact_revision: 2,
        registry_version: "1.1.0",
        policy_version: "1.1.0",
        result: "passed",
        evidence: {
          schema_id: "https://heartweb.example/schema/project-v2.schema.json",
          schema_version: "1.3.0",
          artifact_sha256: "a".repeat(64),
          validator_result: "passed",
        },
        findings: [{ code: "QG_DOMAIN_VALID", severity: "info", message: "Der Domainvertrag ist gültig." }],
        checked_at: "2026-08-25T12:00:00Z",
        checker_version: "heartweb-step-validation/1.0.0",
      }],
    }

    expect(parseGates(value, tenantId, projectId)).toEqual([{
      tenantId,
      projectId,
      runId: "run-neutral-0001",
      stepId: "0",
      qualityGateId: "qg-domain-contract",
      qualityGateRunId: "qgr-0-domain-contract-6e506448",
      artifactId: "artifact-e9ed0fbaf1842ffa",
      artifactHash: "a".repeat(64),
      artifactRevision: 2,
      result: "passed",
      summary: "Maschinenprüfung für GATE-0 bestanden.",
      evidence: {
        schema_id: "https://heartweb.example/schema/project-v2.schema.json",
        schema_version: "1.3.0",
        artifact_sha256: "a".repeat(64),
        validator_result: "passed",
      },
      findings: ["Der Domainvertrag ist gültig."],
      checkerVersion: "heartweb-step-validation/1.0.0",
      checkedAt: "2026-08-25T12:00:00Z",
    }])
  })
})
