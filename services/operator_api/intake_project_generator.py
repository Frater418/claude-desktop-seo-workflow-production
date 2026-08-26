from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Mapping, Protocol

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from services.domain_contract.provider_locations import bind_project_provider_locations
from services.domain_contract.validator import validate_project

from .hermes_runs_client import HermesRunResult, HermesRunsError
from .intake import IntakeGenerationRecord, ReviewedIntake
from .models import JsonValue


_PROMPT_ID: Final = "heartweb.intake.project-v2"
_PROMPT_VERSION: Final = "1.3.0"
_INTAKE_RESOLVABLE_DOMAIN_CODES: Final = frozenset(
    {
        "ERROR_DOMAIN_LOCAL_SCOPE_MISSING",
        "ERROR_DOMAIN_LOCAL_PRESENCE_UNVERIFIED",
        "ERROR_DOMAIN_PROVIDER_LOCATION_UNVERIFIED",
        "ERROR_DOMAIN_PROVIDER_TARGET_UNKNOWN",
        "ERROR_DOMAIN_PROVIDER_TARGET_GEO_MISMATCH",
        "ERROR_DOMAIN_PROVIDER_TARGET_SCOPE_MISMATCH",
        "ERROR_DOMAIN_PLANNING_CAPACITY_UNCONFIRMED",
        "ERROR_DOMAIN_PLANNING_CAPACITY_INVALID",
    }
)
_PROMPT_PATH: Final = Path("prompts/intake-project-v2-v1.3.0.xml.md")
_CONTRACT_ID: Final = "https://heartweb.example/schema/operator/intake-project-draft.schema.json"
_CONTRACT_VERSION: Final = "1.0.0"
_CONTRACT_PATH: Final = Path("standards/operator/intake-project-draft.schema.json")
_EXPECTED_MODEL: Final = "gpt-5.6-sol"
_SOURCE_PATH: Final = "operator-intake/briefing.md"
_SAFE_MESSAGES: Final[dict[str, str]] = {
    "ERROR_LLM_BACKEND_AUTH": "Die isolierte Heartweb-KI-Laufzeit ist nicht authentifiziert.",
    "ERROR_LLM_BACKEND_UNAVAILABLE": "Die isolierte Heartweb-KI-Laufzeit ist nicht erreichbar. Heartweb bitte neu starten.",
    "ERROR_LLM_BACKEND_TIMEOUT": "Die Project-V2-Erstellung hat das Zeitlimit ueberschritten.",
    "ERROR_LLM_BACKEND_RUN_FAILED": "Die Project-V2-Erstellung ist in der isolierten KI-Laufzeit fehlgeschlagen.",
    "ERROR_LLM_BACKEND_INTERACTION_REQUIRED": "Die isolierte KI-Laufzeit verlangt eine nicht unterstuetzte Interaktion.",
    "ERROR_LLM_BACKEND_RESPONSE_INVALID": "Die isolierte KI-Laufzeit hat keinen gueltigen Project-V2-Entwurf geliefert.",
}


class IntakeProjectGenerator(Protocol):
    def generate(self, markdown: str, tenant_id: str, actor_id: str, generated_at: str) -> "IntakeGenerationOutcome": ...


class HermesRunsExecutor(Protocol):
    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult: ...


class IntakeProjectGenerationError(RuntimeError):
    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        self.message = message or _SAFE_MESSAGES.get(code, _SAFE_MESSAGES["ERROR_LLM_BACKEND_RESPONSE_INVALID"])
        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class IntakeGenerationOutcome:
    reviewed: ReviewedIntake
    missing_fields: tuple[str, ...]
    generation: IntakeGenerationRecord
    output_characters: int
    normalizations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HermesIntakeProjectGenerator:
    client: HermesRunsExecutor
    repository_root: Path

    def generate(self, markdown: str, tenant_id: str, actor_id: str, generated_at: str) -> IntakeGenerationOutcome:
        source_sha256 = _sha(markdown.encode("utf-8"))
        prompt_bytes = _read(self.repository_root / _PROMPT_PATH)
        contract_bytes = _read(self.repository_root / _CONTRACT_PATH)
        contract = _object(contract_bytes, "Intake output contract")
        provider_location_registry = _json_file(
            self.repository_root / "standards/domain/provider-location-registry.json"
        )
        input_text = _canonical_json(
            {
                "briefing_markdown": markdown,
                "generated_at": generated_at,
                "market_registry": _json_file(self.repository_root / "standards/domain/market-registry.json"),
                "provider_location_registry": provider_location_registry,
                "project_contracts": {
                    name: _json_file(self.repository_root / "standards/domain" / name)
                    for name in (
                        "project.schema.json",
                        "entity-domain-gbp.schema.json",
                        "search-deployment.schema.json",
                        "risk-compliance.schema.json",
                        "market-registry.schema.json",
                        "provider-location-registry.schema.json",
                    )
                },
                "source_sha256": source_sha256,
                "tenant_id": tenant_id,
                "tenant_name": "Heartweb",
            }
        )
        try:
            result = self.client.execute(
                input_text=input_text,
                instructions=f"{prompt_bytes.decode('utf-8')}\n\nReturn exactly one JSON object and no other text.",
                session_id=f"intake-{source_sha256[:24]}",
            )
        except HermesRunsError as error:
            raise IntakeProjectGenerationError(error.code) from error
        if result.last_event != "run.completed" or result.model != _EXPECTED_MODEL:
            raise _response_error(
                result,
                "Providerabschluss",
                f"Erwartet wurden run.completed und {_EXPECTED_MODEL}; erhalten wurden {result.last_event} und {result.model}.",
            )
        output_bytes = result.output.encode("utf-8")
        try:
            provider_document = _object(output_bytes, "Intake-Providerantwort")
        except IntakeProjectGenerationError as error:
            raise _response_error(result, "JSON-Extraktion", error.message) from error
        system_echoes: dict[str, JsonValue] = {
            "actor_id": actor_id,
            "generated_at": generated_at,
            "source_sha256": source_sha256,
            "tenant_id": tenant_id,
            "tenant_name": "Heartweb",
        }
        removed_echoes = _matching_system_echoes(provider_document, system_echoes)
        draft = _normalize_generated_object(provider_document, system_echoes=system_echoes)
        errors = sorted(
            Draft202012Validator(contract, format_checker=FormatChecker()).iter_errors(draft),
            key=lambda error: (list(error.absolute_path), error.message),
        )
        if errors:
            raise _response_error(result, "Intake-Draft-Schema", _schema_error_detail(errors))
        project_name_value = draft.get("project_name")
        project_name = project_name_value.strip() if isinstance(project_name_value, str) and project_name_value.strip() else None
        project_value = draft.get("project_v2")
        missing_value = draft.get("missing_fields")
        if not isinstance(missing_value, list) or not all(isinstance(item, str) and item.strip() for item in missing_value):
            raise _response_error(result, "Intake-Draft-Schema", "missing_fields enthaelt keinen gueltigen Fragenkatalog.")
        missing_fields = tuple(item.strip() for item in missing_value)
        project_v2: dict[str, JsonValue] | None = None
        project_id: str | None = None
        domain_blockers_converted = False
        if isinstance(project_value, dict):
            if project_name is None or missing_fields:
                raise _response_error(result, "Intake-Draft-Schema", "Ein vollstaendiges project_v2 darf weder einen leeren Projektnamen noch fehlende Felder enthalten.")
            try:
                project_id, project_v2 = _normalize_project(
                    project_value,
                    tenant_id,
                    project_name,
                    generated_at,
                    actor_id,
                    source_sha256,
                    provider_location_registry,
                )
            except IntakeProjectGenerationError as error:
                raise _response_error(result, "Project-V2-Normalisierung", error.message) from error
            validation = validate_project(project_v2, root=self.repository_root)
            if not validation["valid"]:
                contract_errors = validation.get("errors")
                error_rows = contract_errors if isinstance(contract_errors, list) else []
                questions = _domain_blocker_questions(project_v2, error_rows)
                if questions is None:
                    raise _response_error(result, "Project-V2-Vertrag", _contract_error_detail(error_rows))
                missing_fields = questions
                project_v2 = None
                domain_blockers_converted = True
        elif project_value is not None or not missing_fields:
            raise _response_error(result, "Intake-Draft-Schema", "project_v2 und missing_fields bilden keinen gueltigen vollstaendigen oder offenen Entwurf.")
        elif project_name is not None:
            project_id = f"project-{_slug(project_name)}"
        source_title = _title(markdown)
        title = _normalize_generated_text(source_title) if source_title is not None else project_name
        record = IntakeGenerationRecord(
            schema_version="1.0.0",
            source_sha256=source_sha256,
            prompt_id=_PROMPT_ID,
            prompt_version=_PROMPT_VERSION,
            prompt_sha256=_sha(prompt_bytes),
            output_contract_id=_CONTRACT_ID,
            output_contract_version=_CONTRACT_VERSION,
            output_contract_sha256=_sha(contract_bytes),
            provider_run_id=result.run_id,
            model_id=result.model,
            started_at=_rfc3339(result.created_at),
            finished_at=_rfc3339(result.updated_at),
            token_usage={
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
                "total_tokens": result.usage.total_tokens,
            },
            output_sha256=_sha(output_bytes),
        )
        normalizations = [f"Exaktes Core-Systemfeld {key} aus dem aeusseren Antwortobjekt entfernt." for key in removed_echoes]
        if "\u2013" in result.output or "\u2014" in result.output:
            normalizations.append("Unicode-Gedankenstriche in generierten Textwerten durch ASCII-Bindestriche ersetzt.")
        if domain_blockers_converted:
            normalizations.append("Lokale Domain-Vertragsblocker wurden als konkrete Intake-Rückfragen ausgegeben.")
        if project_v2 is not None:
            normalizations.append("Kanonische Hauptidentitaeten und Systemwerte durch den Heartweb Core gesetzt.")
        return IntakeGenerationOutcome(
            reviewed=ReviewedIntake(
                title=title,
                tenant_id=tenant_id,
                project_id=project_id,
                project_name=project_name,
                project_v2=project_v2,
            ),
            missing_fields=missing_fields,
            generation=record,
            output_characters=len(result.output),
            normalizations=tuple(normalizations),
        )


def _normalize_project(
    document: dict[str, object],
    tenant_id: str,
    project_name: str,
    generated_at: str,
    actor_id: str,
    source_sha256: str,
    provider_location_registry: Mapping[str, JsonValue],
) -> tuple[str, dict[str, JsonValue]]:
    slug = _slug(project_name)
    project_id = f"project-{slug}"
    project = copy.deepcopy(document)
    customer = project.get("customer")
    entities = project.get("entity_domain_gbp")
    if not isinstance(customer, dict) or not isinstance(entities, dict) or not isinstance(entities.get("brand"), dict):
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    brand_id = f"brand-{slug}"
    project.update(
        {
            "schema_version": "1.3.0",
            "project_id": project_id,
            "author": "Raphael Rechberger",
            "created_at": generated_at,
            "source_legacy_manifest": {"source": _SOURCE_PATH, "sha256": source_sha256},
            "tenant": {"tenant_id": tenant_id, "name": "Heartweb"},
        }
    )
    customer.update({"customer_id": f"customer-{slug}", "name": project_name})
    entities["brand"].update({"brand_id": brand_id, "name": project_name})
    deployments = project.get("market_deployments")
    if not isinstance(deployments, list):
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    for deployment in deployments:
        if not isinstance(deployment, dict):
            raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        deployment["brand_id"] = brand_id
    capacity = project.get("planning_capacity")
    if isinstance(capacity, dict):
        capacity["confirmed_by"] = actor_id
        capacity["confirmed_at"] = generated_at
        capacity["provisional"] = False
    bound = bind_project_provider_locations(
        project,
        provider_location_registry,
        infer_missing_targets=False,
        require_verified=False,
    )
    return project_id, bound  # type: ignore[return-value]


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.replace("ß", "ss")).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")[:56].rstrip("-")
    if len(slug) < 3:
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return slug


def _normalize_generated_object(
    document: dict[str, JsonValue],
    system_echoes: Mapping[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    normalized = {key: _normalize_generated_value(value) for key, value in document.items()}
    if system_echoes is None:
        return normalized
    for key, expected in system_echoes.items():
        if normalized.get(key) == _normalize_generated_value(expected):
            normalized.pop(key)
    return normalized


def _matching_system_echoes(document: Mapping[str, JsonValue], system_echoes: Mapping[str, JsonValue]) -> tuple[str, ...]:
    return tuple(
        key
        for key, expected in system_echoes.items()
        if key in document and _normalize_generated_value(document[key]) == _normalize_generated_value(expected)
    )


def _normalize_generated_value(value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return _normalize_generated_text(value)
    if isinstance(value, list):
        return [_normalize_generated_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_generated_value(item) for key, item in value.items()}
    return value


def _normalize_generated_text(value: str) -> str:
    return re.sub(r"\s*[\u2013\u2014]\s*", " - ", value).strip()


def _response_error(result: HermesRunResult, stage: str, detail: str) -> IntakeProjectGenerationError:
    safe_detail = re.sub(r"\s+", " ", _normalize_generated_text(detail)).strip()[:700]
    message = (
        f"Provider-Run {result.run_id} wurde mit {result.model} abgeschlossen. "
        f"Antwort: {len(result.output)} Zeichen. Stufe: {stage}. Ursache: {safe_detail}"
    )
    return IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID", message)


def _schema_error_detail(errors: list[ValidationError]) -> str:
    details: list[str] = []
    for error in errors[:4]:
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        details.append(f"{path}: {error.message}")
    if len(errors) > 4:
        details.append(f"{len(errors) - 4} weitere Vertragsverletzungen")
    return " | ".join(details)


def _contract_error_detail(errors: list[object]) -> str:
    if not errors:
        return "Der Domain-Validator hat den Entwurf ohne lesbare Einzelfehler abgelehnt."
    details = [str(error) for error in errors[:4]]
    if len(errors) > 4:
        details.append(f"{len(errors) - 4} weitere Vertragsverletzungen")
    return " | ".join(details)


def _domain_blocker_questions(project: Mapping[str, JsonValue], errors: list[object]) -> tuple[str, ...] | None:
    if not errors or not all(isinstance(error, dict) and error.get("code") in _INTAKE_RESOLVABLE_DOMAIN_CODES for error in errors):
        return None
    questions: list[str] = []
    for error in errors:
        if not isinstance(error, dict):
            return None
        code = error.get("code")
        path = error.get("path")
        if code == "ERROR_DOMAIN_LOCAL_SCOPE_MISSING":
            deployment = _project_list_record(project, "market_deployments", _path_index(path, "market_deployments"))
            if deployment is None:
                return None
            regions = deployment.get("target_regions")
            region_label = ", ".join(item for item in regions if isinstance(item, str) and item.strip()) if isinstance(regions, list) else ""
            if not region_label:
                country_code = deployment.get("country_code")
                region_label = country_code if isinstance(country_code, str) and country_code else "den betroffenen lokalen Markt"
            questions.append(
                f"Bitte bestätige für {region_label}, ob dort bereits Leistungen aktiv erbracht werden. "
                "Wenn ja, nenne das konkret bediente Servicegebiet oder einen belegten physischen Standort. "
                "Wenn die Expansion erst geplant ist, bestätige den Planungsstatus ohne aktive lokale Präsenz."
            )
        elif code == "ERROR_DOMAIN_LOCAL_PRESENCE_UNVERIFIED":
            entities = project.get("entity_domain_gbp")
            if not isinstance(entities, dict):
                return None
            profile = _list_record(entities.get("gbp_profiles"), _path_index(path, "gbp_profiles"))
            if profile is None:
                return None
            location_id = profile.get("location_id")
            locations = entities.get("physical_locations")
            location = next(
                (item for item in locations if isinstance(item, dict) and item.get("location_id") == location_id),
                None,
            ) if isinstance(locations, list) else None
            location_name = location.get("name") if isinstance(location, dict) else None
            label = location_name if isinstance(location_name, str) and location_name.strip() else "den zugeordneten physischen Standort"
            questions.append(
                f"Bitte belege {label} für das im Briefing genannte Google Business Profile, zum Beispiel mit vollständiger Geschäftsadresse oder belastbarer Quelle. "
                "Alternativ bestätige, dass dieses Profil bis zur Verifizierung noch nicht in Project V2 aufgenommen werden soll."
            )
        elif code in {
            "ERROR_DOMAIN_PROVIDER_LOCATION_UNVERIFIED",
            "ERROR_DOMAIN_PROVIDER_TARGET_UNKNOWN",
            "ERROR_DOMAIN_PROVIDER_TARGET_GEO_MISMATCH",
            "ERROR_DOMAIN_PROVIDER_TARGET_SCOPE_MISMATCH",
        }:
            deployment = _project_list_record(project, "market_deployments", _path_index(path, "market_deployments"))
            if deployment is None:
                return None
            regions = deployment.get("target_regions")
            region_label = ", ".join(
                item for item in regions if isinstance(item, str) and item.strip()
            ) if isinstance(regions, list) else ""
            if not region_label:
                country_code = deployment.get("country_code")
                region_label = country_code if isinstance(country_code, str) and country_code else "das Deployment"
            questions.append(
                f"Bitte verifiziere den exakten Provider-Standort für {region_label} und wähle die passende target_id aus der Provider-Location-Registry. "
                "Ein aktives Deployment wird vor Step 0 nur mit passendem Markt, Sprache, Standorttyp und verifiziertem Provider-Code angelegt."
            )
        elif code in {
            "ERROR_DOMAIN_PLANNING_CAPACITY_UNCONFIRMED",
            "ERROR_DOMAIN_PLANNING_CAPACITY_INVALID",
        }:
            questions.append(
                "Bitte bestätige die verbindliche wöchentliche Planungskapazität als Minimum und Maximum in Stunden. "
                "Ohne bestätigten Wert legt Heartweb keinen Default fest und startet Step 0 nicht."
            )
        else:
            return None
    return tuple(dict.fromkeys(questions)) or None


def _path_index(path: object, collection: str) -> int | None:
    if not isinstance(path, list):
        return None
    try:
        position = path.index(collection)
    except ValueError:
        return None
    index = path[position + 1] if position + 1 < len(path) else None
    return index if isinstance(index, int) and not isinstance(index, bool) and index >= 0 else None


def _project_list_record(project: Mapping[str, JsonValue], key: str, index: int | None) -> dict[str, JsonValue] | None:
    return _list_record(project.get(key), index)


def _list_record(value: object, index: int | None) -> dict[str, JsonValue] | None:
    if not isinstance(value, list) or index is None or index >= len(value):
        return None
    item = value[index]
    return item if isinstance(item, dict) else None


def _title(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# ") and line[2:].strip():
            return line[2:].strip()
    return None


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error


def _json_file(path: Path) -> dict[str, JsonValue]:
    return _object(_read(path), str(path.name))


def _object(value: bytes, subject: str) -> dict[str, JsonValue]:
    try:
        document = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID", f"{subject} ist kein gueltiges JSON-Objekt.") from error
    if not isinstance(document, dict):
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID", f"{subject} ist kein gueltiges JSON-Objekt.")
    return document


def _canonical_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _rfc3339(epoch: int | float) -> str:
    try:
        return datetime.fromtimestamp(epoch, UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    except (OSError, OverflowError, ValueError) as error:
        raise IntakeProjectGenerationError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
