import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import type { OperatorApiClient, PlanningCapacityPreview } from "../api/client"
import type { AcceptedIntakeRead } from "../api/readModels"
import { AcceptedIntakePanel } from "./AcceptedIntakePanel"

afterEach(() => cleanup())

const intake: AcceptedIntakeRead = {
  tenantId: "tenant-heartweb",
  projectId: "project-capacity-ui",
  title: "Kapazitätsprojekt",
  acceptedAt: "2026-08-26T00:00:00Z",
  acceptedBy: "operator-heartweb-admin",
  markdown: "# Briefing",
  sourceHash: "a".repeat(64),
  projectV2: {
    business_goal: "Sichtbarkeit",
    core_services: ["SEO"],
    entity_domain_gbp: { domains: [{ role: "primary", host: "example.com" }] },
    market_deployments: [{ deployment_id: "dep-capacity-de", deployment_role: "primary", country_code: "DE", locale: "de-DE", language: "de", target_regions: ["Deutschland"], provider_location_verification: { status: "verified", location_name: "Germany", provider_location_code: 2276 } }],
    source_legacy_manifest: { source: "operator-intake/briefing.md" },
  },
  generation: null,
}

const preview: PlanningCapacityPreview = {
  tenant_id: intake.tenantId,
  project_id: intake.projectId,
  preview_hash: "b".repeat(64),
  current_project_sha256: "c".repeat(64),
  proposed_project_sha256: "d".repeat(64),
  capacity: { min: 10, max: 10, source: "operator_confirmed", provisional: false, confirmed_by: "operator-heartweb-admin", confirmed_at: "2026-08-26T00:30:00Z" },
  run_id: "run-capacity-0001",
  deployment_id: "dep-capacity-de",
  changed: true,
}

describe("AcceptedIntakePanel planning capacity", () => {
  it("previews and confirms a missing weekly capacity through the operator API", async () => {
    const previewPlanningCapacity = vi.fn().mockResolvedValue(preview)
    const confirmPlanningCapacity = vi.fn().mockResolvedValue(preview)
    const reload = vi.fn().mockResolvedValue(undefined)
    const api = { previewPlanningCapacity, confirmPlanningCapacity } as unknown as OperatorApiClient
    render(<AcceptedIntakePanel api={api} intake={intake} reload={reload} />)

    fireEvent.change(screen.getByLabelText("Minimum Stunden pro Woche"), { target: { value: "10" } })
    fireEvent.change(screen.getByLabelText("Maximum Stunden pro Woche"), { target: { value: "10" } })
    fireEvent.click(screen.getByRole("button", { name: "Kapazität prüfen" }))

    expect(await screen.findByText("10 Stunden pro Woche", { exact: false })).toBeTruthy()
    expect(previewPlanningCapacity).toHaveBeenCalledWith(
      intake.projectId,
      { min_hours_per_week: 10, max_hours_per_week: 10 },
      expect.any(AbortSignal),
    )

    fireEvent.click(screen.getByRole("button", { name: "Kapazität verbindlich bestätigen" }))

    await vi.waitFor(() => expect(confirmPlanningCapacity).toHaveBeenCalled())
    expect(reload).toHaveBeenCalledOnce()
  })
})
