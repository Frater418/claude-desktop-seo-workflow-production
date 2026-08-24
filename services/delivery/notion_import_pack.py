from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json

from .contract_validation import JsonValue


def plain_json(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {key: plain_json(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [plain_json(item) for item in value]
    return value


def manifest_preimage_bytes(value: Mapping[str, JsonValue]) -> bytes:
    copied = dict(value)
    copied.pop("manifest_sha256", None)
    return json.dumps(plain_json(copied), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def complete_json_bytes(value: Mapping[str, JsonValue]) -> bytes:
    return json.dumps(plain_json(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"


@dataclass(frozen=True, slots=True, init=False)
class NotionImportPack:
    """A pack whose returned views cannot mutate rendered replay state."""

    _manifest: Mapping[str, JsonValue]
    _files: Mapping[str, bytes]

    def __init__(self, manifest: Mapping[str, JsonValue], files: Mapping[str, bytes]) -> None:
        object.__setattr__(self, "_manifest", plain_json(manifest))
        object.__setattr__(self, "_files", dict(files))

    @property
    def manifest(self) -> dict[str, JsonValue]:
        copied = plain_json(self._manifest)
        return {key: value for key, value in copied.items()} if isinstance(copied, Mapping) else {}

    @property
    def files(self) -> dict[str, bytes]:
        return dict(self._files)
