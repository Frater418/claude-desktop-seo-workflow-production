// Generated from standards/api/operator-api.openapi.json. DO NOT EDIT.
// OpenAPI SHA-256: dfd3f86b903782144aa247d5167ca05160b4fbb619d0552fb34d9d0776f76893

export type ActionBlocker = { readonly "code" : string; readonly "message" : string; readonly "remediation" : string; };

export type ActionConfirmRequest = { readonly "confirmed" : true; readonly "idempotency_key" : string; readonly "intent" : ActionIntent; readonly "preview_hash" : string; };

export type ActionConfirmResult = { readonly "canonical" : {} & Record<string, JsonValue>; readonly "preview_hash" : string; readonly "readback_urls" : readonly (string)[]; readonly "replay" : boolean; };

export type ActionIntent = { readonly "action" : "start" | "submit-for-gate" | "approve" | "reject" | "request-revision" | "request-input" | "escalate" | "request-waiver" | "resolve" | "complete"; readonly "expected_revision" : number; readonly "payload"?: ActionPayload; readonly "project_id" : string; readonly "run_id" : string; readonly "step_id" : string; readonly "tenant_id" : string; };

export type ActionPayload = { readonly "affected_sections"?: readonly (string)[]; readonly "immutable_constraints"?: readonly (string)[]; readonly "impacts"?: readonly (string)[]; readonly "instructions"?: string; readonly "options"?: readonly (string)[]; readonly "reason"?: string; readonly "source_id"?: string | null; readonly "source_type"?: "operator_task" | "blocker" | "revision_request" | "workflow_defect" | "escalation" | null; };

export type ActionPreview = { readonly "allowed" : boolean; readonly "blockers" : readonly (ActionBlocker)[]; readonly "consequence" : {} & Record<string, JsonValue>; readonly "intent" : ActionIntent; readonly "preview_hash" : string; };

export type ArtifactCandidateSaveRequest = { readonly "bundle" : {} & Record<string, JsonValue>; readonly "expected_parent_revision" : number; readonly "gate_context" : GateContext; readonly "idempotency_key" : string; readonly "primary_document" : JsonValue; readonly "run_id" : string; readonly "supporting_documents"?: readonly (JsonValue)[]; };

export type ArtifactContentResponse = { readonly "artifact" : ArtifactRecord; readonly "content_base64" : string; };

export type ArtifactDiffRequest = { readonly "left_artifact_id" : string; readonly "right_artifact_id" : string; };

export type ArtifactDiffResponse = { readonly "left_artifact" : ArtifactRecord; readonly "right_artifact" : ArtifactRecord; readonly "unified_diff" : string; };

export type ArtifactRecord = { readonly "artifact_id" : string; readonly "content_sha256" : string; readonly "contract_version"?: string; readonly "created_at" : string; readonly "input_hash" : string; readonly "parent_artifact_ids"?: readonly (string)[]; readonly "producer_version"?: string; readonly "project_id" : string; readonly "revision" : number; readonly "run_id" : string; readonly "step_id" : string; readonly "storage_key" : string; readonly "tenant_id" : string; };

export type ArtifactRevisionListResponse = { readonly "artifacts" : readonly (ArtifactRecord)[]; };

export type ArtifactValidationRequest = { readonly "content_sha256" : string; readonly "revision" : number; };

export type CommandRequest = { readonly "command" : "start" | "request-revision" | "request-input" | "create-defect" | "escalate" | "request-waiver" | "submit-for-gate" | "approve" | "complete" | "reject" | "resolve" | "resume"; readonly "command_id" : string; readonly "correlation_id" : string; readonly "event" : {} & Record<string, JsonValue>; readonly "expected_revision" : number; readonly "idempotency_key" : string; readonly "operator_record"?: {} & Record<string, JsonValue> | null; readonly "project_id" : string; readonly "record_type"?: string | null; readonly "run_id" : string; readonly "step_id" : string; readonly "tenant_id" : string; readonly "transition_command"?: {} & Record<string, JsonValue> | null; };

export type CommandResult = { readonly "command_id" : string; readonly "correlation_id" : string; readonly "event" : {} & Record<string, JsonValue>; readonly "readback_url" : string; readonly "replay" : boolean; readonly "run"?: {} & Record<string, JsonValue> | null; };

export type CurrentRunResponse = { readonly "expected_revision" : number; readonly "project_id" : string; readonly "run_id" : string; readonly "step_id" : "0" | "1" | "1b" | "1c" | "2" | "3" | "4a" | "4b"; readonly "tenant_id" : string; };

export type DataEnvelope = { readonly "data" : JsonValue; };

export type GateContext = { readonly "available_tools"?: readonly (string)[]; readonly "configured_tools"?: readonly (string)[]; readonly "evidence_by_gate" : {} & Record<string, {} & Record<string, string | number | boolean>>; readonly "not_applicable_decisions"?: {} & Record<string, {} & Record<string, JsonValue>>; readonly "site_status"?: "existing_site" | "non_existing_site" | null; };

export type HTTPValidationError = { readonly "detail"?: readonly (ValidationError)[]; };

export type IntakeAcceptanceRequest = { readonly "confirmed" : boolean; readonly "markdown" : string; readonly "preview_hash" : string; readonly "reviewed" : ReviewedIntake; readonly "source_sha256" : string; };

export type IntakePreviewRequest = { readonly "markdown" : string; };

export type JsonValue = unknown;

export type ReviewedIntake = { readonly "project_id"?: string | null; readonly "project_name"?: string | null; readonly "project_v2"?: {} & Record<string, JsonValue> | null; readonly "tenant_id"?: string | null; readonly "title"?: string | null; };

export type ValidationError = { readonly "ctx"?: Record<string, unknown>; readonly "input"?: unknown; readonly "loc" : readonly (string | number)[]; readonly "msg" : string; readonly "type" : string; };

export type ApiOperationMap = {
  readonly "acceptMarkdownIntake": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/intake/accept"; readonly request: IntakeAcceptanceRequest; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "compareArtifactRevisions": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifact-revisions/compare"; readonly request: ArtifactDiffRequest; readonly responses: { readonly "200": ArtifactDiffResponse; readonly "422": HTTPValidationError; }; };
  readonly "confirmAdminAction": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/actions/{verb}/confirm"; readonly request: ActionConfirmRequest; readonly responses: { readonly "200": ActionConfirmResult; readonly "422": HTTPValidationError; }; };
  readonly "getArtifactRevision": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifacts/{artifact_id}"; readonly request: never; readonly responses: { readonly "200": ArtifactContentResponse; readonly "422": HTTPValidationError; }; };
  readonly "getArtifactRevisionContent": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifacts/{artifact_id}/content"; readonly request: never; readonly responses: { readonly "200": ArtifactContentResponse; readonly "422": HTTPValidationError; }; };
  readonly "getCurrentRun": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/runs/current"; readonly request: never; readonly responses: { readonly "200": CurrentRunResponse; readonly "422": HTTPValidationError; }; };
  readonly "getIntegrationStatus": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/integrations/status"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getLogicalSession": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/logical-session"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getMarkdownIntake": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/intake"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getOperatorRecord": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/operator-records/{record_type}/{record_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getProject": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getRun": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getRunHistory": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/history"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getStep": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/steps/{step_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getWorkflow": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/workflow"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "healthz": { readonly method: "GET"; readonly path: "/healthz"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; }; };
  readonly "listAdjustmentProposals": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/adjustment-proposals"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listApprovals": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/approvals"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listArtifactRevisions": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/steps/{step_id}/artifact-revisions"; readonly request: never; readonly responses: { readonly "200": ArtifactRevisionListResponse; readonly "422": HTTPValidationError; }; };
  readonly "listArtifacts": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifacts"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listAssignments": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/assignments"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listContextPackages": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/context-packages"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listGates": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/gates"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listMetrics": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/metrics"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listPerformanceCheckpoints": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/performance-checkpoints"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listProjects": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listReleases": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/releases"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listSteps": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/steps"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listTasks": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/tasks"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listTickets": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/tickets"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "previewAdminAction": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/actions/{verb}/preview"; readonly request: ActionIntent; readonly responses: { readonly "200": ActionPreview; readonly "422": HTTPValidationError; }; };
  readonly "previewMarkdownIntake": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/intake/preview"; readonly request: IntakePreviewRequest; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "readyz": { readonly method: "GET"; readonly path: "/readyz"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; }; };
  readonly "saveArtifactRevision": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifacts"; readonly request: ArtifactCandidateSaveRequest; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "submitOperatorCommand": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/commands/{verb}"; readonly request: CommandRequest; readonly responses: { readonly "200": CommandResult; readonly "422": HTTPValidationError; }; };
  readonly "validateArtifactRevision": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifacts/{artifact_id}/validate"; readonly request: ArtifactValidationRequest; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
};
