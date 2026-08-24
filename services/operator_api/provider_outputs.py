from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationInfo, model_validator


_CONTENT_TYPE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+/[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


class ProviderOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, ser_json_bytes="base64", val_json_bytes="base64")

    contract_id: str = Field(min_length=1)
    content_bytes: bytes
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_type: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    parent_revision: int = Field(gt=0)
    target_revision: int = Field(gt=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        if hashlib.sha256(self.content_bytes).hexdigest() != self.content_sha256:
            raise ValueError("content_sha256 must match content_bytes")
        if _CONTENT_TYPE.fullmatch(self.content_type) is None:
            raise ValueError("content_type must be a media type")
        if self.parent_revision != self.target_revision - 1:
            raise ValueError("parent_revision must immediately precede target_revision")
        return self


class ProviderOutputSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    primary: ProviderOutput
    supporting: tuple[ProviderOutput, ...] = ()

    @property
    def outputs(self) -> tuple[ProviderOutput, ...]:
        return (self.primary, *self.supporting)

    @property
    def canonical_sha256(self) -> str:
        material = [output.model_dump(mode="json") for output in self.outputs]
        encoded = json.dumps(material, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    @model_validator(mode="after")
    def validate_set(self, info: ValidationInfo) -> Self:
        expected_contract_ids = info.context["expected_contract_ids"]
        output_contract_ids = tuple(output.contract_id for output in self.outputs)
        if output_contract_ids != expected_contract_ids:
            raise ValueError("outputs must match selected registry contracts exactly once and in order")
        reference = self.primary
        for output in self.supporting:
            if (
                output.tenant_id,
                output.project_id,
                output.run_id,
                output.step_id,
                output.idempotency_key,
                output.parent_revision,
                output.target_revision,
                output.created_at,
            ) != (
                reference.tenant_id,
                reference.project_id,
                reference.run_id,
                reference.step_id,
                reference.idempotency_key,
                reference.parent_revision,
                reference.target_revision,
                reference.created_at,
            ):
                raise ValueError("all outputs must share one execution identity")
        return self

    @classmethod
    def from_registry(
        cls,
        registry: dict[str, JsonValue],
        *,
        primary: ProviderOutput,
        supporting: tuple[ProviderOutput, ...] = (),
    ) -> Self:
        expected_contract_ids = _contract_ids_for_step(registry, primary.step_id)
        return cls.model_validate(
            {"primary": primary, "supporting": supporting},
            context={"expected_contract_ids": expected_contract_ids},
        )


def _contract_ids_for_step(registry: dict[str, JsonValue], step_id: str) -> tuple[str, ...]:
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("official prompt registry entries are required")
    selected = [entry for entry in entries if isinstance(entry, dict) and entry.get("step_id") == step_id and entry.get("active") is True]
    if len(selected) != 1:
        raise ValueError("exactly one active registry entry is required for the output step")
    contracts = selected[0].get("output_contracts")
    if not isinstance(contracts, list) or not contracts:
        raise ValueError("selected registry entry requires output contracts")
    contract_ids = tuple(contract.get("contract_id") for contract in contracts if isinstance(contract, dict))
    if len(contract_ids) != len(contracts) or not all(isinstance(contract_id, str) and contract_id for contract_id in contract_ids):
        raise ValueError("selected registry output contracts must have contract IDs")
    if len(set(contract_ids)) != len(contract_ids):
        raise ValueError("selected registry output contracts must be unique")
    return contract_ids
