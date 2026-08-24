import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { OperatorApiClient } from "../../api/client"
import type { DeliveryCreateRequest } from "../../generated/api-types"
import type { DeliveryExportResultRead, DeliveryPackageRecordRead, DeliveryPreviewRead } from "../../api/deliveryReadModels"
import { buildOrReuseDeliveryCreateRequest, type DeliveryCreateInput, type ValidatedDeliveryCreateInput, validateDeliveryCreateInput } from "./deliveryRequest"

const formValidationTimestamp = "2000-01-01T00:00:00.000Z"

export type DeliveryCenterClient = Pick<OperatorApiClient, "previewDelivery" | "createDeliveryExport" | "listDeliveryExports" | "getDeliveryExport" | "downloadDeliveryExport">
export type DeliveryLoadState<T> = { readonly kind: "loading" } | { readonly kind: "ready"; readonly data: T } | { readonly kind: "error"; readonly message: string }
export type DeliveryFormValues = { readonly scope: string; readonly exportSequence: string; readonly sourceSnapshotRevision: string; readonly packageRevision: string; readonly draftInclusionPolicy: string; readonly selectedRoles: readonly string[]; readonly customerExternalId: string; readonly publicationUrls: string; readonly implementationTasksJson: string }
export type DeliveryFormField = Exclude<keyof DeliveryFormValues, "selectedRoles">
export type DeliveryRoleOption = "copywriter" | "developer"
export type DeliveryCreateState = { readonly kind: "idle" } | { readonly kind: "building" } | { readonly kind: "submitting" } | { readonly kind: "readback" } | { readonly kind: "ready"; readonly message: string } | { readonly kind: "error"; readonly message: string }
export type DeliveryDownloadState = { readonly kind: "idle" } | { readonly kind: "downloading" } | { readonly kind: "ready"; readonly filename: string } | { readonly kind: "error"; readonly message: string }

type DeliveryFormAssessment = { readonly input: ValidatedDeliveryCreateInput | null; readonly errors: readonly string[] }
type AssigneeSummary = { readonly mapped: number; readonly unresolved: number; readonly unassigned: number }
type UseDeliveryCenterOptions = { readonly api: DeliveryCenterClient; readonly tenantId: string; readonly projectId: string }

const emptyForm: DeliveryFormValues = { scope: "", exportSequence: "", sourceSnapshotRevision: "", packageRevision: "", draftInclusionPolicy: "", selectedRoles: [], customerExternalId: "", publicationUrls: "", implementationTasksJson: "" }

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

function abortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError"
}

function createInput(form: DeliveryFormValues, tenantId: string, projectId: string, createdAt: string): DeliveryCreateInput {
  return { tenantId, projectId, scope: form.scope, exportSequence: form.exportSequence, sourceSnapshotRevision: form.sourceSnapshotRevision, packageRevision: form.packageRevision, draftInclusionPolicy: form.draftInclusionPolicy, selectedRoles: form.selectedRoles, customerExternalId: form.customerExternalId, publicationUrls: form.publicationUrls, implementationTasksJson: form.implementationTasksJson, createdAt }
}

function assessForm(input: DeliveryCreateInput): DeliveryFormAssessment {
  const validation = validateDeliveryCreateInput(input)
  switch (validation.kind) {
    case "valid": return { input: validation.input, errors: [] }
    case "invalid": return { input: null, errors: validation.errors }
  }
}

function selectedPreview(scope: string, checkpoint: DeliveryLoadState<DeliveryPreviewRead>, final: DeliveryLoadState<DeliveryPreviewRead>): DeliveryLoadState<DeliveryPreviewRead> | null {
  switch (scope) {
    case "checkpoint": return checkpoint
    case "final": return final
    default: return null
  }
}

function policyEligible(preview: DeliveryLoadState<DeliveryPreviewRead> | null): boolean {
  if (preview === null) return false
  switch (preview.kind) {
    case "loading": return false
    case "error": return false
    case "ready": return preview.data.policyEligible
  }
}

function assigneeSummary(input: ValidatedDeliveryCreateInput | null): AssigneeSummary {
  if (input === null) return { mapped: 0, unresolved: 0, unassigned: 0 }
  return input.implementationTasks.reduce<AssigneeSummary>((summary, task) => {
    if (task.source_assignee === "") return { ...summary, unassigned: summary.unassigned + 1 }
    if (task.notion_user_id === null || task.notion_user_id === undefined) return { ...summary, unresolved: summary.unresolved + 1 }
    return { ...summary, mapped: summary.mapped + 1 }
  }, { mapped: 0, unresolved: 0, unassigned: 0 })
}

function readbackMismatch(request: DeliveryCreateRequest, result: DeliveryExportResultRead, record: DeliveryPackageRecordRead): string | null {
  if (result.tenantId !== request.export_request.tenant_id || result.projectId !== request.export_request.project_id || record.tenantId !== result.tenantId || record.projectId !== result.projectId) return "Die kanonische Lieferung hat eine abweichende Projektzuordnung."
  if (result.exportId !== request.export_id || record.exportId !== result.exportId || result.deliveryPackageId !== request.delivery_package_id || record.deliveryPackageId !== result.deliveryPackageId || result.deliveryExportRequestId !== request.export_request.delivery_export_request_id) return "Die kanonische Lieferung hat abweichende Kennungen."
  if (result.sourceSnapshotRevision !== request.export_request.source_snapshot_revision || record.sourceSnapshotRevision !== result.sourceSnapshotRevision || record.packageRevision !== request.package_revision || record.scope !== request.export_request.scope) return "Die kanonische Lieferung hat abweichende Revisionen."
  if (record.packageSha256 !== result.packageSha256 || record.zipSha256 !== result.zipSha256) return "Die kanonische Lieferung hat abweichende Pruefsummen."
  return null
}

export function useDeliveryCenter({ api, tenantId, projectId }: UseDeliveryCenterOptions) {
  const [checkpoint, setCheckpoint] = useState<DeliveryLoadState<DeliveryPreviewRead>>({ kind: "loading" })
  const [final, setFinal] = useState<DeliveryLoadState<DeliveryPreviewRead>>({ kind: "loading" })
  const [history, setHistory] = useState<DeliveryLoadState<readonly DeliveryExportResultRead[]>>({ kind: "loading" })
  const [record, setRecord] = useState<DeliveryLoadState<DeliveryPackageRecordRead>>({ kind: "loading" })
  const [selectedExportId, setSelectedExportId] = useState<string | null>(null)
  const [form, setForm] = useState<DeliveryFormValues>(emptyForm)
  const [pendingRequest, setPendingRequest] = useState<DeliveryCreateRequest | null>(null)
  const [consumedSequence, setConsumedSequence] = useState<number | null>(null)
  const [editedAfterSubmission, setEditedAfterSubmission] = useState(false)
  const [createState, setCreateState] = useState<DeliveryCreateState>({ kind: "idle" })
  const [downloadState, setDownloadState] = useState<DeliveryDownloadState>({ kind: "idle" })
  const [notionPreviewVisible, setNotionPreviewVisible] = useState(false)
  const actionController = useRef<AbortController | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    actionController.current?.abort()
    setCheckpoint({ kind: "loading" })
    setFinal({ kind: "loading" })
    setHistory({ kind: "loading" })
    setRecord({ kind: "loading" })
    setSelectedExportId(null)
    setForm(emptyForm)
    setPendingRequest(null)
    setConsumedSequence(null)
    setEditedAfterSubmission(false)
    setCreateState({ kind: "idle" })
    setDownloadState({ kind: "idle" })
    setNotionPreviewVisible(false)
    void api.previewDelivery(projectId, "checkpoint", controller.signal).then((data) => {
      if (!controller.signal.aborted) setCheckpoint({ kind: "ready", data })
    }).catch((error: unknown) => {
      if (!controller.signal.aborted && !abortError(error)) setCheckpoint({ kind: "error", message: errorMessage(error, "Die Checkpoint-Vorschau konnte nicht geladen werden.") })
    })
    void api.previewDelivery(projectId, "final", controller.signal).then((data) => {
      if (!controller.signal.aborted) setFinal({ kind: "ready", data })
    }).catch((error: unknown) => {
      if (!controller.signal.aborted && !abortError(error)) setFinal({ kind: "error", message: errorMessage(error, "Die finale Vorschau konnte nicht geladen werden.") })
    })
    void api.listDeliveryExports(projectId, controller.signal).then((data) => {
      if (!controller.signal.aborted) setHistory({ kind: "ready", data })
    }).catch((error: unknown) => {
      if (!controller.signal.aborted && !abortError(error)) setHistory({ kind: "error", message: errorMessage(error, "Die Exporthistorie konnte nicht geladen werden.") })
    })
    return () => {
      controller.abort()
      actionController.current?.abort()
      actionController.current = null
    }
  }, [api, projectId])

  const assessment = useMemo(() => assessForm(createInput(form, tenantId, projectId, formValidationTimestamp)), [form, projectId, tenantId])
  const preview = selectedPreview(form.scope, checkpoint, final)
  const selectedPolicyEligible = policyEligible(preview)
  const assignments = assigneeSummary(assessment.input)
  const needsHigherSequence = pendingRequest !== null && editedAfterSubmission && (assessment.input === null || consumedSequence === null || assessment.input.exportSequence <= consumedSequence)
  const isCreating = (() => {
    switch (createState.kind) {
      case "building":
      case "submitting":
      case "readback": return true
      case "idle":
      case "ready":
      case "error": return false
    }
  })()
  const canCreate = assessment.input !== null && selectedPolicyEligible && !isCreating && (pendingRequest === null || (editedAfterSubmission && !needsHigherSequence))
  const canRetry = pendingRequest !== null && !editedAfterSubmission && !isCreating

  const updateField = useCallback((field: DeliveryFormField, value: string): void => {
    if (pendingRequest !== null) setEditedAfterSubmission(true)
    setForm((current) => ({ ...current, [field]: value }))
    setNotionPreviewVisible(false)
  }, [pendingRequest])

  const toggleRole = useCallback((role: DeliveryRoleOption): void => {
    if (pendingRequest !== null) setEditedAfterSubmission(true)
    setForm((current) => current.selectedRoles.includes(role) ? { ...current, selectedRoles: current.selectedRoles.filter((value) => value !== role) } : { ...current, selectedRoles: [...current.selectedRoles, role] })
    setNotionPreviewVisible(false)
  }, [pendingRequest])

  const submitRequest = useCallback(async (request: DeliveryCreateRequest): Promise<void> => {
    actionController.current?.abort()
    const controller = new AbortController()
    actionController.current = controller
    setCreateState({ kind: "submitting" })
    try {
      const result = await api.createDeliveryExport(projectId, request, controller.signal)
      if (controller.signal.aborted) return
      setCreateState({ kind: "readback" })
      const canonicalRecord = await api.getDeliveryExport(projectId, result.exportId, controller.signal)
      if (controller.signal.aborted) return
      const mismatch = readbackMismatch(request, result, canonicalRecord)
      if (mismatch !== null) {
        setCreateState({ kind: "error", message: mismatch })
        return
      }
      setHistory((current) => {
        const retained = (() => {
          switch (current.kind) {
            case "ready": return current.data.filter((item) => item.exportId !== result.exportId)
            case "loading":
            case "error": return []
          }
        })()
        return { kind: "ready", data: [result, ...retained] }
      })
      setSelectedExportId(result.exportId)
      setRecord({ kind: "ready", data: canonicalRecord })
      setCreateState({ kind: "ready", message: result.replayState === "replayed" ? "Vorhandener Export wurde unveraendert wiederverwendet." : "Export wurde erstellt und kanonisch gelesen." })
    } catch (error) {
      if (!controller.signal.aborted && !abortError(error)) setCreateState({ kind: "error", message: errorMessage(error, "Der Export konnte nicht erstellt werden.") })
    }
  }, [api, projectId])

  const createExport = useCallback(async (): Promise<void> => {
    if (!canCreate || assessment.input === null) return
    const timestamped = validateDeliveryCreateInput(createInput(form, tenantId, projectId, new Date().toISOString()))
    switch (timestamped.kind) {
      case "invalid":
        setCreateState({ kind: "error", message: timestamped.errors.join(" ") })
        return
      case "valid": {
        setCreateState({ kind: "building" })
        try {
          const request = await buildOrReuseDeliveryCreateRequest({ existingRequest: null, input: timestamped.input, crypto: globalThis.crypto })
          setPendingRequest(request)
          setConsumedSequence(timestamped.input.exportSequence)
          setEditedAfterSubmission(false)
          await submitRequest(request)
        } catch (error) {
          setCreateState({ kind: "error", message: errorMessage(error, "Der Exportauftrag konnte nicht vorbereitet werden.") })
        }
      }
    }
  }, [assessment.input, canCreate, form, projectId, submitRequest, tenantId])

  const retryExport = useCallback(async (): Promise<void> => {
    if (!canRetry || pendingRequest === null || assessment.input === null) return
    const request = await buildOrReuseDeliveryCreateRequest({ existingRequest: pendingRequest, input: assessment.input, crypto: globalThis.crypto })
    await submitRequest(request)
  }, [assessment.input, canRetry, pendingRequest, submitRequest])

  const selectExport = useCallback(async (exportId: string): Promise<void> => {
    actionController.current?.abort()
    const controller = new AbortController()
    actionController.current = controller
    setSelectedExportId(exportId)
    setRecord({ kind: "loading" })
    try {
      const selectedRecord = await api.getDeliveryExport(projectId, exportId, controller.signal)
      if (!controller.signal.aborted) setRecord({ kind: "ready", data: selectedRecord })
    } catch (error) {
      if (!controller.signal.aborted && !abortError(error)) setRecord({ kind: "error", message: errorMessage(error, "Der Exportdatensatz konnte nicht geladen werden.") })
    }
  }, [api, projectId])

  const downloadExport = useCallback(async (): Promise<void> => {
    if (selectedExportId === null) return
    actionController.current?.abort()
    const controller = new AbortController()
    actionController.current = controller
    setDownloadState({ kind: "downloading" })
    try {
      const download = await api.downloadDeliveryExport(projectId, selectedExportId, controller.signal)
      if (controller.signal.aborted) return
      const objectUrl = URL.createObjectURL(download.blob)
      const anchor = document.createElement("a")
      anchor.href = objectUrl
      anchor.download = download.filename
      document.body.append(anchor)
      try {
        anchor.click()
      } finally {
        anchor.remove()
        URL.revokeObjectURL(objectUrl)
      }
      setDownloadState({ kind: "ready", filename: download.filename })
    } catch (error) {
      if (!controller.signal.aborted && !abortError(error)) setDownloadState({ kind: "error", message: errorMessage(error, "Das ZIP konnte nicht heruntergeladen werden.") })
    }
  }, [api, projectId, selectedExportId])

  const prepareNotionPreview = useCallback((): void => {
    setNotionPreviewVisible(assessment.input !== null)
  }, [assessment.input])

  return { checkpoint, final, history, record, selectedExportId, form, assessment, assignments, preview, selectedPolicyEligible, needsHigherSequence, createState, downloadState, notionPreviewVisible, canCreate, canRetry, updateField, toggleRole, createExport, retryExport, selectExport, downloadExport, prepareNotionPreview }
}
