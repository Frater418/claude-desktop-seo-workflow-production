// Generated from standards/api/operator-api.openapi.json. DO NOT EDIT.
// OpenAPI SHA-256: bc1d82a113730fb585112ad97dfed7f30bcc73e7016878f22f8fb8b998bb2ff4

export type CommandRequest = { readonly "command" : "start" | "request-revision" | "request-input" | "create-defect" | "escalate" | "request-waiver" | "approve" | "reject" | "resolve" | "resume"; readonly "command_id" : string; readonly "correlation_id" : string; readonly "event" : {} & Record<string, JsonValue>; readonly "expected_revision" : number; readonly "idempotency_key" : string; readonly "operator_record"?: {} & Record<string, JsonValue> | null; readonly "project_id" : string; readonly "record_type"?: string | null; readonly "run_id" : string; readonly "step_id" : string; readonly "tenant_id" : string; readonly "transition_command"?: {} & Record<string, JsonValue> | null; };

export type CommandResult = { readonly "command_id" : string; readonly "correlation_id" : string; readonly "event" : {} & Record<string, JsonValue>; readonly "replay" : boolean; readonly "run"?: {} & Record<string, JsonValue> | null; };

export type DataEnvelope = { readonly "data" : JsonValue; };

export type HTTPValidationError = { readonly "detail"?: readonly (ValidationError)[]; };

export type JsonValue = unknown;

export type ValidationError = { readonly "ctx"?: Record<string, unknown>; readonly "input"?: unknown; readonly "loc" : readonly (string | number)[]; readonly "msg" : string; readonly "type" : string; };

export type ApiOperationMap = {
  readonly "getIntegrationStatus": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/integrations/status"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getLogicalSession": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/logical-session"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getProject": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getRun": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getRunHistory": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/history"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getStep": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/steps/{step_id}"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "getWorkflow": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/workflow"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "healthz": { readonly method: "GET"; readonly path: "/healthz"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; }; };
  readonly "listAdjustmentProposals": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/adjustment-proposals"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listArtifacts": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/artifacts"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listAssignments": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/assignments"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listContextPackages": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/context-packages"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listGates": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/gates"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listMetrics": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/metrics"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listPerformanceCheckpoints": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/performance-checkpoints"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listProjects": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listSteps": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/steps"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listTasks": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/tasks"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "listTickets": { readonly method: "GET"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/tickets"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; readonly "422": HTTPValidationError; }; };
  readonly "readyz": { readonly method: "GET"; readonly path: "/readyz"; readonly request: never; readonly responses: { readonly "200": DataEnvelope; }; };
  readonly "submitOperatorCommand": { readonly method: "POST"; readonly path: "/v1/tenants/{tenant_id}/projects/{project_id}/commands/{verb}"; readonly request: CommandRequest; readonly responses: { readonly "200": CommandResult; readonly "422": HTTPValidationError; }; };
};
