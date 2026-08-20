"""Generate the local Operator API OpenAPI snapshot and TypeScript contract types."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import TypeAlias

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
SNAPSHOT_RELATIVE = Path("standards/api/operator-api.openapi.json")
TYPES_RELATIVE = Path("apps/operator-console/src/generated/api-types.ts")
HTTP_METHODS = frozenset({"delete", "get", "head", "options", "patch", "post", "put", "trace"})


class ContractGenerationError(RuntimeError):
    """Raised when FastAPI emits an OpenAPI document outside the supported contract subset."""


def _mapping(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ContractGenerationError("OpenAPI contract value must be an object.")
    return value


def _canonical_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _literal(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def _reference(value: JsonValue) -> str:
    reference = _mapping(value).get("$ref")
    if not isinstance(reference, str) or not reference.startswith("#/components/schemas/"):
        raise ContractGenerationError("OpenAPI reference must target a named component schema.")
    return reference.rsplit("/", maxsplit=1)[1]


def _union(parts: list[str]) -> str:
    return " | ".join(dict.fromkeys(parts)) if parts else "unknown"


def _schema_type(value: JsonValue) -> str:
    schema = _mapping(value)
    if "$ref" in schema:
        return _reference(schema)
    for key in ("oneOf", "anyOf", "allOf"):
        alternatives = schema.get(key)
        if isinstance(alternatives, list):
            rendered = [_schema_type(item) for item in alternatives]
            separator = " & " if key == "allOf" else " | "
            return separator.join(dict.fromkeys(rendered))
    constant = schema.get("const")
    if constant is not None or "const" in schema:
        return _literal(constant)
    enum = schema.get("enum")
    if isinstance(enum, list):
        return _union([_literal(item) for item in enum])
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        return _union([_primitive_type(item, schema) for item in schema_type])
    if isinstance(schema_type, str):
        return _primitive_type(schema_type, schema)
    if "properties" in schema or "additionalProperties" in schema:
        return _object_type(schema)
    return "unknown"


def _primitive_type(schema_type: JsonValue, schema: dict[str, JsonValue]) -> str:
    if schema_type == "array":
        items = schema.get("items")
        return f"readonly ({_schema_type(items) if items is not None else 'unknown'})[]"
    if schema_type == "object":
        return _object_type(schema)
    primitives = {"boolean": "boolean", "integer": "number", "number": "number", "null": "null", "string": "string"}
    if isinstance(schema_type, str) and schema_type in primitives:
        return primitives[schema_type]
    return "unknown"


def _object_type(schema: dict[str, JsonValue]) -> str:
    properties_value = schema.get("properties", {})
    properties = _mapping(properties_value)
    required_value = schema.get("required", [])
    required = frozenset(item for item in required_value if isinstance(item, str)) if isinstance(required_value, list) else frozenset()
    members = [
        f"readonly {_literal(name)}{' ' if name in required else '?'}: {_schema_type(value)};"
        for name, value in sorted(properties.items())
    ]
    shape = "{ " + " ".join(members) + " }" if members else "{}"
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        return f"{shape} & Record<string, {_schema_type(additional)}>"
    if additional is True or (additional is None and not properties):
        return f"{shape} & Record<string, unknown>" if properties else "Record<string, unknown>"
    return shape


def _request_type(operation: dict[str, JsonValue]) -> str:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return "never"
    content = _mapping(body.get("content", {}))
    return _union([_schema_type(_mapping(media).get("schema", {})) for _, media in sorted(content.items())])


def _response_type(response: JsonValue) -> str:
    content = _mapping(response).get("content", {})
    if not isinstance(content, dict):
        return "never"
    return _union([_schema_type(_mapping(media).get("schema", {})) for _, media in sorted(content.items())])


def _operation_map(document: dict[str, JsonValue]) -> list[str]:
    paths = _mapping(document.get("paths", {}))
    operations: list[tuple[str, str, str, dict[str, JsonValue]]] = []
    for path, path_item in sorted(paths.items()):
        if not isinstance(path, str):
            raise ContractGenerationError("OpenAPI path must be a string.")
        for method, operation in sorted(_mapping(path_item).items()):
            if method not in HTTP_METHODS:
                continue
            operation_map = _mapping(operation)
            operation_id = operation_map.get("operationId")
            if not isinstance(operation_id, str):
                raise ContractGenerationError("Every OpenAPI route must have an operation ID.")
            operations.append((operation_id, method.upper(), path, operation_map))
    return [
        "export type ApiOperationMap = {",
        *[
            "  readonly " + _literal(operation_id) + ": { "
            + f"readonly method: {_literal(method)}; readonly path: {_literal(path)}; "
            + f"readonly request: {_request_type(operation)}; readonly responses: {{ "
            + " ".join(
                f"readonly {_literal(str(status))}: {_response_type(response)};"
                for status, response in sorted(_mapping(operation.get("responses", {})).items())
            )
            + " }; };"
            for operation_id, method, path, operation in sorted(operations)
        ],
        "};",
    ]


def _typescript(snapshot: str) -> str:
    document = _mapping(json.loads(snapshot))
    schemas = _mapping(_mapping(document.get("components", {})).get("schemas", {}))
    lines = [
        "// Generated from standards/api/operator-api.openapi.json. DO NOT EDIT.",
        f"// OpenAPI SHA-256: {hashlib.sha256(snapshot.encode('ascii')).hexdigest()}",
        "",
    ]
    for name, schema in sorted(schemas.items()):
        if not isinstance(name, str):
            raise ContractGenerationError("OpenAPI component name must be a string.")
        lines.extend((f"export type {name} = {_schema_type(schema)};", ""))
    lines.extend(_operation_map(document))
    return "\n".join(lines) + "\n"


def generate_artifacts(root: Path) -> tuple[str, str]:
    """Return the deterministic FastAPI snapshot and TypeScript generated from it."""
    with tempfile.TemporaryDirectory(prefix="operator-api-openapi-") as temporary:
        registry = WorkspaceRegistry((WorkspaceRegistration("tenant-openapi", "project-openapi", Path(temporary)),))
        app = create_app(registry, root, AppConfig(root, allow_unready=True))
        snapshot = _canonical_json(app.openapi())
    return snapshot, _typescript(snapshot)


def _write_artifacts(root: Path, snapshot: str, types: str) -> None:
    for relative, content in ((SNAPSHOT_RELATIVE, snapshot), (TYPES_RELATIVE, types)):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    snapshot, types = generate_artifacts(ROOT)
    if arguments.check:
        stale = [
            str(relative)
            for relative, content in ((SNAPSHOT_RELATIVE, snapshot), (TYPES_RELATIVE, types))
            if not (ROOT / relative).is_file() or (ROOT / relative).read_text(encoding="utf-8") != content
        ]
        if stale:
            sys.stderr.write("Stale generated operator API artifacts: " + ", ".join(stale) + "\n")
            return 1
        return 0
    _write_artifacts(ROOT, snapshot, types)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
