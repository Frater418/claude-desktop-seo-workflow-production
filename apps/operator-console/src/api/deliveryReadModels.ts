import type { ApiOperationMap } from "../generated/api-types"
import { ARTIFACT_ID, EXPORT_ID, NOTION_MANIFEST_ID, PACKAGE_ID, REQUEST_ID, RESULT_ID, ROLE_MANIFEST_ID, SOURCE_RECORD_ID, booleanAt, exactKeys, fail, identifierAt, list, manifestIdentifierAt, nullableSafeRelativePathAt, nullableSha256At, object, optionalNullableSafeRelativePathAt, positiveIntegerAt, requireUnique, rfc3339At, routeIdentity, safeRelativePathAt, sha256At, stringAt } from "./deliveryReadModelPrimitives"

type DeliveryPreviewWire = ApiOperationMap["previewDelivery"]["responses"]["200"]
type DeliveryExportResultWire = ApiOperationMap["createDeliveryExport"]["responses"]["201"]
type DeliveryPackageRecordWire = ApiOperationMap["getDeliveryExport"]["responses"]["200"]

export type DeliveryScope = ApiOperationMap["previewDelivery"]["parameters"]["query"]["scope"]
export type DeliveryCreateRequest = ApiOperationMap["createDeliveryExport"]["request"]
export type DeliveryDeliverableId = DeliveryPreviewWire["missing_deliverable_ids"][number]
export type DeliveryRole = DeliveryPreviewWire["selected_deliverables"][number]["role"]
export type DeliveryReleaseStatus = DeliveryPreviewWire["selected_deliverables"][number]["release_status"]
export type DeliveryStepId = DeliveryPreviewWire["selected_deliverables"][number]["step_id"]
export type DeliveryReplayState = DeliveryExportResultWire["replay_state"]
export type DeliveryDerivedStatus = DeliveryPackageRecordWire["derived_status"]
export type DeliverySourceKind = DeliveryPackageRecordWire["source_records"][number]["source_kind"]

export type DeliveryPolicyErrorRead = { readonly code: string; readonly message: string }
export type DeliveryDeliverableRead = { readonly artifactId: string; readonly contentSha256: string | null; readonly deliverableId: DeliveryDeliverableId; readonly outputPath: string | null; readonly releaseStatus: DeliveryReleaseStatus; readonly role: DeliveryRole; readonly stepId: DeliveryStepId }
export type DeliveryManifestRead = { readonly manifestId: string; readonly relativePath: string; readonly contentSha256: string }
export type DeliverySourceRecordRead = { readonly tenantId: string; readonly projectId: string; readonly sourceKind: DeliverySourceKind; readonly sourceRecordId: string; readonly sourceRevision: number; readonly sourceSha256: string }
export type DeliveryPackageDeliverableRead = { readonly deliverableId: DeliveryDeliverableId; readonly sourceRecordId: string; readonly sourceSha256: string; readonly packagePath: string; readonly releaseStatus: DeliveryReleaseStatus }
export type DeliveryRolePackageRead = { readonly role: DeliveryRole; readonly roleHandoffManifestId: string; readonly manifestPath: string; readonly manifestSha256: string }
export type DeliveryNotionManifestRead = { readonly notionImportManifestId: string; readonly manifestPath: string; readonly manifestSha256: string }
export type DeliveryQualitySummaryRead = { readonly summaryPath: string; readonly contentSha256: string }
export type DeliveryPreviewRead = { readonly scope: DeliveryScope; readonly policyEligible: boolean; readonly missingDeliverableIds: readonly DeliveryDeliverableId[]; readonly errors: readonly DeliveryPolicyErrorRead[]; readonly selectedDeliverables: readonly DeliveryDeliverableRead[] }
export type DeliveryExportResultRead = { readonly tenantId: string; readonly projectId: string; readonly deliveryExportResultId: string; readonly deliveryExportRequestId: string; readonly deliveryPackageId: string; readonly exportId: string; readonly sourceSnapshotRevision: number; readonly replayState: DeliveryReplayState; readonly exportPath: string; readonly zipPath: string; readonly packageSha256: string; readonly zipSha256: string; readonly zipSizeBytes: number; readonly deliveryManifest: DeliveryManifestRead; readonly roleHandoffManifests: readonly DeliveryManifestRead[]; readonly notionImportManifest: DeliveryManifestRead; readonly createdAt: string }
export type DeliveryPackageRecordRead = { readonly tenantId: string; readonly projectId: string; readonly deliveryPackageId: string; readonly exportId: string; readonly scope: DeliveryScope; readonly sourceSnapshotRevision: number; readonly sourceRecords: readonly DeliverySourceRecordRead[]; readonly requiredDeliverables: readonly DeliveryPackageDeliverableRead[]; readonly missingDeliverables: readonly DeliveryDeliverableId[]; readonly packagePaths: readonly string[]; readonly packageSha256: string; readonly zipSha256: string; readonly rolePackages: readonly DeliveryRolePackageRead[]; readonly notionImportManifest: DeliveryNotionManifestRead; readonly createdAt: string; readonly packageRevision: number; readonly derivedStatus: DeliveryDerivedStatus; readonly taskAssignmentManifestPath: string | null | undefined; readonly qualitySummary: DeliveryQualitySummaryRead | null | undefined; readonly exportManifestPath: string | null | undefined; readonly checksumsPath: string | null | undefined }

function scope(value: string, subject: string): DeliveryScope {
  switch (value) {
    case "checkpoint": return value
    case "final": return value
    default: return fail(`einen ungueltigen Umfang in ${subject}`)
  }
}

function deliverableId(value: string, subject: string): DeliveryDeliverableId {
  switch (value) {
    case "strategy": return value
    case "architecture": return value
    case "design": return value
    case "keyword-research": return value
    case "roadmap": return value
    case "copywriter-handoff": return value
    case "developer-handoff": return value
    default: return fail(`eine ungueltige Lieferobjektkennung in ${subject}`)
  }
}

function role(value: string, subject: string): DeliveryRole {
  switch (value) {
    case "copywriter": return value
    case "developer": return value
    case "project_management": return value
    case "reviewer": return value
    default: return fail(`eine ungueltige Rolle in ${subject}`)
  }
}

function releaseStatus(value: string, subject: string): DeliveryReleaseStatus {
  switch (value) {
    case "released": return value
    case "draft": return value
    default: return fail(`einen ungueltigen Freigabestatus in ${subject}`)
  }
}

function stepId(value: string, subject: string): DeliveryStepId {
  switch (value) {
    case "1": return value
    case "1b": return value
    case "1c": return value
    case "2": return value
    case "3": return value
    case "4a": return value
    case "4b": return value
    default: return fail(`eine ungueltige Schrittkennung in ${subject}`)
  }
}

function replayState(value: string, subject: string): DeliveryReplayState {
  switch (value) {
    case "created": return value
    case "replayed": return value
    default: return fail(`einen ungueltigen Wiederholungsstatus in ${subject}`)
  }
}

function derivedStatus(value: string, subject: string): DeliveryDerivedStatus {
  switch (value) {
    case "prepared": return value
    case "archived": return value
    default: return fail(`einen ungueltigen Paketstatus in ${subject}`)
  }
}

function sourceKind(value: string, subject: string): DeliverySourceKind {
  switch (value) {
    case "project": return value
    case "workflow": return value
    case "run": return value
    case "artifact": return value
    case "release": return value
    case "task": return value
    case "assignment": return value
    case "review": return value
    case "approval": return value
    case "blocker": return value
    case "report": return value
    default: return fail(`eine ungueltige Quellart in ${subject}`)
  }
}

function schemaVersion(value: string, subject: string): void {
  if (value !== "1.0.0") fail(`eine ungueltige Schemaversion in ${subject}`)
}

function policyError(value: unknown): DeliveryPolicyErrorRead {
  const record = object(value, "Richtlinienfehler")
  exactKeys(record, ["code", "message"], "Richtlinienfehler")
  return { code: stringAt(record, "code", "Richtlinienfehler"), message: stringAt(record, "message", "Richtlinienfehler") }
}

function deliverable(value: unknown): DeliveryDeliverableRead {
  const record = object(value, "Lieferobjekt")
  exactKeys(record, ["artifact_id", "content_sha256", "deliverable_id", "output_path", "release_status", "role", "step_id"], "Lieferobjekt")
  return { artifactId: identifierAt(record, "artifact_id", ARTIFACT_ID, "Lieferobjekt"), contentSha256: nullableSha256At(record, "content_sha256", "Lieferobjekt"), deliverableId: deliverableId(stringAt(record, "deliverable_id", "Lieferobjekt"), "Lieferobjekt"), outputPath: nullableSafeRelativePathAt(record, "output_path", "Lieferobjekt"), releaseStatus: releaseStatus(stringAt(record, "release_status", "Lieferobjekt"), "Lieferobjekt"), role: role(stringAt(record, "role", "Lieferobjekt"), "Lieferobjekt"), stepId: stepId(stringAt(record, "step_id", "Lieferobjekt"), "Lieferobjekt") }
}

function manifest(value: unknown, subject: string): DeliveryManifestRead {
  const record = object(value, subject)
  exactKeys(record, ["manifest_id", "relative_path", "content_sha256"], subject)
  return { manifestId: manifestIdentifierAt(record, "manifest_id", subject), relativePath: safeRelativePathAt(record, "relative_path", subject), contentSha256: sha256At(record, "content_sha256", subject) }
}

function sourceRecord(value: unknown, tenantId: string, projectId: string): DeliverySourceRecordRead {
  const record = object(value, "Quellnachweis")
  exactKeys(record, ["tenant_id", "project_id", "source_kind", "source_record_id", "source_revision", "source_sha256"], "Quellnachweis")
  const identity = routeIdentity(record, "Quellnachweis", tenantId, projectId)
  return { ...identity, sourceKind: sourceKind(stringAt(record, "source_kind", "Quellnachweis"), "Quellnachweis"), sourceRecordId: identifierAt(record, "source_record_id", SOURCE_RECORD_ID, "Quellnachweis"), sourceRevision: positiveIntegerAt(record, "source_revision", "Quellnachweis"), sourceSha256: sha256At(record, "source_sha256", "Quellnachweis") }
}

function packageDeliverable(value: unknown): DeliveryPackageDeliverableRead {
  const record = object(value, "Paket-Lieferobjekt")
  exactKeys(record, ["deliverable_id", "source_record_id", "source_sha256", "package_path", "release_status"], "Paket-Lieferobjekt")
  return { deliverableId: deliverableId(stringAt(record, "deliverable_id", "Paket-Lieferobjekt"), "Paket-Lieferobjekt"), sourceRecordId: identifierAt(record, "source_record_id", ARTIFACT_ID, "Paket-Lieferobjekt"), sourceSha256: sha256At(record, "source_sha256", "Paket-Lieferobjekt"), packagePath: safeRelativePathAt(record, "package_path", "Paket-Lieferobjekt"), releaseStatus: releaseStatus(stringAt(record, "release_status", "Paket-Lieferobjekt"), "Paket-Lieferobjekt") }
}

function rolePackage(value: unknown): DeliveryRolePackageRead {
  const record = object(value, "Rollenpaket")
  exactKeys(record, ["role", "role_handoff_manifest_id", "manifest_path", "manifest_sha256"], "Rollenpaket")
  return { role: role(stringAt(record, "role", "Rollenpaket"), "Rollenpaket"), roleHandoffManifestId: identifierAt(record, "role_handoff_manifest_id", ROLE_MANIFEST_ID, "Rollenpaket"), manifestPath: safeRelativePathAt(record, "manifest_path", "Rollenpaket"), manifestSha256: sha256At(record, "manifest_sha256", "Rollenpaket") }
}

function notionManifest(value: unknown): DeliveryNotionManifestRead {
  const record = object(value, "Notion-Manifest")
  exactKeys(record, ["notion_import_manifest_id", "manifest_path", "manifest_sha256"], "Notion-Manifest")
  return { notionImportManifestId: identifierAt(record, "notion_import_manifest_id", NOTION_MANIFEST_ID, "Notion-Manifest"), manifestPath: safeRelativePathAt(record, "manifest_path", "Notion-Manifest"), manifestSha256: sha256At(record, "manifest_sha256", "Notion-Manifest") }
}

function qualitySummary(value: unknown): DeliveryQualitySummaryRead {
  const record = object(value, "Qualitaetszusammenfassung")
  exactKeys(record, ["summary_path", "content_sha256"], "Qualitaetszusammenfassung")
  return { summaryPath: safeRelativePathAt(record, "summary_path", "Qualitaetszusammenfassung"), contentSha256: sha256At(record, "content_sha256", "Qualitaetszusammenfassung") }
}

function optionalQualitySummary(value: unknown): DeliveryQualitySummaryRead | null | undefined {
  if (value === undefined || value === null) return value
  return qualitySummary(value)
}

export function parseDeliveryPreview(value: unknown, expectedScope: DeliveryScope): DeliveryPreviewRead {
  const record = object(value, "Liefer-Vorschau")
  exactKeys(record, ["scope", "policy_eligible", "missing_deliverable_ids", "errors", "selected_deliverables"], "Liefer-Vorschau")
  const parsedScope = scope(stringAt(record, "scope", "Liefer-Vorschau"), "Liefer-Vorschau")
  if (parsedScope !== expectedScope) return fail("eine Vorschau mit ungueltigem Umfang")
  return { scope: parsedScope, policyEligible: booleanAt(record, "policy_eligible", "Liefer-Vorschau"), missingDeliverableIds: list(record["missing_deliverable_ids"], "fehlende Lieferobjekte").map((item) => deliverableId(typeof item === "string" ? item : fail("eine ungueltige Lieferobjektkennung"), "fehlende Lieferobjekte")), errors: list(record["errors"], "Richtlinienfehler").map(policyError), selectedDeliverables: list(record["selected_deliverables"], "Lieferobjekte").map(deliverable) }
}

export function parseDeliveryExportResult(value: unknown, tenantId: string, projectId: string): DeliveryExportResultRead {
  const record = object(value, "Lieferergebnis")
  exactKeys(record, ["delivery_export_result_id", "schema_version", "tenant_id", "project_id", "delivery_export_request_id", "export_id", "delivery_package_id", "source_snapshot_revision", "replay_state", "export_path", "zip_path", "package_sha256", "zip_sha256", "zip_size_bytes", "delivery_manifest", "role_handoff_manifests", "notion_import_manifest", "created_at"], "Lieferergebnis")
  const identity = routeIdentity(record, "Lieferergebnis", tenantId, projectId)
  const roleHandoffManifests = list(record["role_handoff_manifests"], "Rollen-Manifesten").map((item) => manifest(item, "Rollen-Manifest"))
  if (roleHandoffManifests.length === 0) return fail("keine Rollen-Manifeste im Lieferergebnis")
  requireUnique(roleHandoffManifests.map((item) => item.manifestId), "Rollen-Manifesten")
  schemaVersion(stringAt(record, "schema_version", "Lieferergebnis"), "Lieferergebnis")
  return { ...identity, deliveryExportResultId: identifierAt(record, "delivery_export_result_id", RESULT_ID, "Lieferergebnis"), deliveryExportRequestId: identifierAt(record, "delivery_export_request_id", REQUEST_ID, "Lieferergebnis"), deliveryPackageId: identifierAt(record, "delivery_package_id", PACKAGE_ID, "Lieferergebnis"), exportId: identifierAt(record, "export_id", EXPORT_ID, "Lieferergebnis"), sourceSnapshotRevision: positiveIntegerAt(record, "source_snapshot_revision", "Lieferergebnis"), replayState: replayState(stringAt(record, "replay_state", "Lieferergebnis"), "Lieferergebnis"), exportPath: safeRelativePathAt(record, "export_path", "Lieferergebnis"), zipPath: safeRelativePathAt(record, "zip_path", "Lieferergebnis"), packageSha256: sha256At(record, "package_sha256", "Lieferergebnis"), zipSha256: sha256At(record, "zip_sha256", "Lieferergebnis"), zipSizeBytes: positiveIntegerAt(record, "zip_size_bytes", "Lieferergebnis"), deliveryManifest: manifest(record["delivery_manifest"], "Liefer-Manifest"), roleHandoffManifests, notionImportManifest: manifest(record["notion_import_manifest"], "Notion-Manifest"), createdAt: rfc3339At(record, "created_at", "Lieferergebnis") }
}

export function parseDeliveryExportHistory(value: unknown, tenantId: string, projectId: string): readonly DeliveryExportResultRead[] {
  const record = object(value, "Lieferhistorie")
  exactKeys(record, ["data"], "Lieferhistorie")
  return list(record["data"], "Lieferhistorie").map((item) => parseDeliveryExportResult(item, tenantId, projectId))
}

export function parseDeliveryPackageRecord(value: unknown, tenantId: string, projectId: string, expectedExportId: string): DeliveryPackageRecordRead {
  const record = object(value, "Lieferpaket")
  exactKeys(record, ["delivery_package_id", "schema_version", "tenant_id", "project_id", "export_id", "scope", "source_snapshot_revision", "source_records", "required_deliverables", "missing_deliverables", "package_paths", "package_sha256", "zip_sha256", "role_packages", "notion_import_manifest", "created_at", "package_revision", "derived_status", "task_assignment_manifest_path", "quality_summary", "export_manifest_path", "checksums_path"], "Lieferpaket")
  const identity = routeIdentity(record, "Lieferpaket", tenantId, projectId)
  const parsedExportId = identifierAt(record, "export_id", EXPORT_ID, "Lieferpaket")
  if (parsedExportId !== expectedExportId) return fail("eine ungueltige Exportbindung im Lieferpaket")
  const sourceRecords = list(record["source_records"], "Quellnachweisen").map((item) => sourceRecord(item, tenantId, projectId))
  const requiredDeliverables = list(record["required_deliverables"], "Paket-Lieferobjekten").map(packageDeliverable)
  const packagePaths = list(record["package_paths"], "Paketpfaden").map((item) => typeof item === "string" ? safeRelativePathAt({ value: item }, "value", "Paketpfaden") : fail("keinen sicheren relativen Pfad in Paketpfaden"))
  const rolePackages = list(record["role_packages"], "Rollenpaketen").map(rolePackage)
  if (sourceRecords.length === 0 || requiredDeliverables.length === 0 || packagePaths.length === 0 || rolePackages.length === 0) return fail("unvollstaendige Pflichtlisten im Lieferpaket")
  requireUnique(sourceRecords.map((item) => item.sourceRecordId), "Quellnachweisen")
  requireUnique(requiredDeliverables.map((item) => item.deliverableId), "Paket-Lieferobjekten")
  requireUnique(packagePaths, "Paketpfaden")
  requireUnique(rolePackages.map((item) => item.role), "Rollenpaketen")
  const taskAssignmentManifestPath = optionalNullableSafeRelativePathAt(record, "task_assignment_manifest_path", "Lieferpaket")
  const quality = optionalQualitySummary(record["quality_summary"])
  const exportManifestPath = optionalNullableSafeRelativePathAt(record, "export_manifest_path", "Lieferpaket")
  const checksumsPath = optionalNullableSafeRelativePathAt(record, "checksums_path", "Lieferpaket")
  const parsedScope = scope(stringAt(record, "scope", "Lieferpaket"), "Lieferpaket")
  const missingDeliverables = list(record["missing_deliverables"], "fehlenden Lieferobjekten").map((item) => deliverableId(typeof item === "string" ? item : fail("eine ungueltige Lieferobjektkennung"), "fehlenden Lieferobjekten"))
  if (parsedScope === "final" && (missingDeliverables.length !== 0 || requiredDeliverables.length !== 7 || requiredDeliverables.some((item) => item.releaseStatus !== "released") || !rolePackages.some((item) => item.role === "copywriter") || !rolePackages.some((item) => item.role === "developer") || taskAssignmentManifestPath == null || quality == null || exportManifestPath == null || checksumsPath == null)) return fail("ein unvollstaendiges finales Lieferpaket")
  schemaVersion(stringAt(record, "schema_version", "Lieferpaket"), "Lieferpaket")
  return { ...identity, deliveryPackageId: identifierAt(record, "delivery_package_id", PACKAGE_ID, "Lieferpaket"), exportId: parsedExportId, scope: parsedScope, sourceSnapshotRevision: positiveIntegerAt(record, "source_snapshot_revision", "Lieferpaket"), sourceRecords, requiredDeliverables, missingDeliverables, packagePaths, packageSha256: sha256At(record, "package_sha256", "Lieferpaket"), zipSha256: sha256At(record, "zip_sha256", "Lieferpaket"), rolePackages, notionImportManifest: notionManifest(record["notion_import_manifest"]), createdAt: rfc3339At(record, "created_at", "Lieferpaket"), packageRevision: positiveIntegerAt(record, "package_revision", "Lieferpaket"), derivedStatus: derivedStatus(stringAt(record, "derived_status", "Lieferpaket"), "Lieferpaket"), taskAssignmentManifestPath, qualitySummary: quality, exportManifestPath, checksumsPath }
}
