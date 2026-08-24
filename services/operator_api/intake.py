from __future__ import annotations

import hashlib
import json
import re
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from .package4 import Package4Error


_PROJECT_V2_BLOCK: Final = re.compile(r"^## Project V2\s*\n```json\s*\n(?P<document>.*?)\n```\s*$", re.MULTILINE | re.DOTALL)
_FIELDS: Final = {"Tenant ID": "tenant_id", "Project ID": "project_id", "Project Name": "project_name"}


class ReviewedIntake(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str | None = None
    tenant_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    project_v2: dict[str, JsonValue] | None = None


class IntakePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    markdown: str = Field(min_length=1)


class IntakeAcceptanceRequest(IntakePreviewRequest):
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: ReviewedIntake
    preview_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: bool


class IntakePreview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_sha256: str
    reviewed: ReviewedIntake
    missing_fields: tuple[str, ...]
    eligible: bool
    preview_hash: str
    previewed_at: str


class ReviewedAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    markdown: str
    source_sha256: str
    reviewed: ReviewedIntake
    actor_id: str
    accepted_at: str


def preview_intake(markdown: str, actor_id: str, previewed_at: str) -> IntakePreview:
    values = _markdown_fields(markdown)
    project_v2 = _project_v2(markdown)
    reviewed = ReviewedIntake(title=_title(markdown), project_v2=project_v2, **values)
    missing = tuple(name for name, value in reviewed if value is None)
    source_sha256 = _sha(markdown)
    return IntakePreview(
        source_sha256=source_sha256,
        reviewed=reviewed,
        missing_fields=missing,
        eligible=not missing,
        preview_hash=_sha(f"{source_sha256}|{actor_id}|{previewed_at}"),
        previewed_at=previewed_at,
    )


def confirm_intake(tenant_id: str, request: IntakeAcceptanceRequest, preview: IntakePreview, actor_id: str) -> ReviewedAcceptance:
    if not request.confirmed:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Intake acceptance requires explicit confirmation.")
    request_hash = _sha(request.markdown)
    if request.preview_hash != preview.preview_hash or request.source_sha256 != preview.source_sha256 or request_hash != preview.source_sha256:
        raise Package4Error("ERR_STALE_REVISION", "Intake source hash does not match the reviewed preview.")
    if not preview.eligible:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Intake has required fields missing from the reviewed Markdown.")
    if request.reviewed != preview.reviewed:
        raise Package4Error("ERR_STALE_REVISION", "Intake reviewed fields do not match the reviewed Markdown.")
    if request.reviewed.tenant_id != tenant_id:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Intake tenant does not match the tenant-scoped route.")
    return ReviewedAcceptance(
        markdown=request.markdown,
        source_sha256=preview.source_sha256,
        reviewed=preview.reviewed,
        actor_id=actor_id,
        accepted_at=preview.previewed_at,
    )


def _markdown_fields(markdown: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in markdown.splitlines():
        label, separator, value = line.partition(":")
        field = _FIELDS.get(label.strip())
        if separator and field and value.strip():
            values[field] = value.strip()
    return values


def _project_v2(markdown: str) -> dict[str, JsonValue] | None:
    match = _PROJECT_V2_BLOCK.search(markdown)
    if match is None:
        return None
    try:
        document = json.loads(match.group("document"))
    except json.JSONDecodeError:
        return None
    return document if isinstance(document, dict) else None


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _title(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# ") and line[2:].strip():
            return line[2:].strip()
    return None
