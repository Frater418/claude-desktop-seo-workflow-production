from __future__ import annotations

import hashlib
import json
import re
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

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


class IntakeGenerationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    output_characters: int = Field(ge=0)
    validation_stages: tuple[str, ...]
    normalizations: tuple[str, ...]


class IntakePreview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_sha256: str
    reviewed: ReviewedIntake
    missing_fields: tuple[str, ...]
    eligible: bool
    preview_hash: str
    previewed_at: str
    generation_summary: IntakeGenerationSummary | None = None


class IntakeTokenUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def total_matches_parts(self) -> "IntakeTokenUsage":
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("Token total does not match input and output tokens.")
        return self


class IntakeGenerationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prompt_id: str = Field(min_length=1)
    prompt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_contract_id: str = Field(min_length=1)
    output_contract_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    output_contract_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)
    token_usage: IntakeTokenUsage
    output_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReviewedAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    markdown: str
    source_sha256: str
    reviewed: ReviewedIntake
    actor_id: str
    accepted_at: str
    generation: IntakeGenerationRecord | None = None


def preview_intake(markdown: str, actor_id: str, previewed_at: str) -> IntakePreview:
    values = _markdown_fields(markdown)
    project_v2 = _project_v2(markdown)
    reviewed = ReviewedIntake(title=_title(markdown), project_v2=project_v2, **values)
    return preview_reviewed_intake(markdown, actor_id, previewed_at, reviewed)


def preview_reviewed_intake(
    markdown: str,
    actor_id: str,
    previewed_at: str,
    reviewed: ReviewedIntake,
    missing_fields: tuple[str, ...] | None = None,
    binding_sha256: str = "",
    generation_summary: IntakeGenerationSummary | None = None,
) -> IntakePreview:
    missing = missing_fields if missing_fields is not None else tuple(name for name, value in reviewed if value is None)
    source_sha256 = _sha(markdown)
    review_bytes = json.dumps(reviewed.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return IntakePreview(
        source_sha256=source_sha256,
        reviewed=reviewed,
        missing_fields=missing,
        eligible=not missing and all(value is not None for _, value in reviewed),
        preview_hash=_sha(f"{source_sha256}|{actor_id}|{previewed_at}|{review_bytes}|{binding_sha256}"),
        previewed_at=previewed_at,
        generation_summary=generation_summary,
    )


def confirm_intake(
    tenant_id: str,
    request: IntakeAcceptanceRequest,
    preview: IntakePreview,
    actor_id: str,
    generation: IntakeGenerationRecord | None = None,
) -> ReviewedAcceptance:
    if not request.confirmed:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Stufe: Annahmevalidierung. Die verbindliche Annahme erfordert eine ausdrueckliche Bestaetigung.")
    request_hash = _sha(request.markdown)
    if request.preview_hash != preview.preview_hash or request.source_sha256 != preview.source_sha256 or request_hash != preview.source_sha256:
        raise Package4Error("ERR_STALE_REVISION", "Stufe: Annahmevalidierung. Das Briefing oder die Vorschau wurde seit der Pruefung veraendert.")
    if not preview.eligible:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Stufe: Annahmevalidierung. Der gepruefte Entwurf enthaelt noch fehlende Pflichtangaben.")
    if request.reviewed != preview.reviewed:
        raise Package4Error("ERR_STALE_REVISION", "Stufe: Annahmevalidierung. Die uebermittelten Project-V2-Daten stimmen nicht mit der geprueften Vorschau ueberein.")
    if request.reviewed.tenant_id != tenant_id:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Stufe: Annahmevalidierung. Der Mandant stimmt nicht mit der geprueften Vorschau ueberein.")
    return ReviewedAcceptance(
        markdown=request.markdown,
        source_sha256=preview.source_sha256,
        reviewed=preview.reviewed,
        actor_id=actor_id,
        accepted_at=preview.previewed_at,
        generation=generation,
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
