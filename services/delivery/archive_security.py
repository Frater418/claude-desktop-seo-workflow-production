from __future__ import annotations

from datetime import datetime
import json
import re
import unicodedata
from typing import TYPE_CHECKING
from jsonschema import FormatChecker

from .record_normalization import DeliveryInventoryError

if TYPE_CHECKING:
    from .archive import ArchiveIdentity


_IDENTIFIERS = (("tenant_id", re.compile(r"^tenant-[a-z0-9][a-z0-9-]{2,63}$")), ("project_id", re.compile(r"^project-[a-z0-9][a-z0-9-]{2,63}$")), ("export_id", re.compile(r"^delivery-export-[a-z0-9][a-z0-9-]{7,63}$")), ("package_id", re.compile(r"^delivery-package-[a-z0-9][a-z0-9-]{7,63}$")))
_DEVICES = frozenset(("con", "conin$", "conout$", "prn", "aux", "nul", *(f"com{index}" for index in range(1, 10)), *(f"lpt{index}" for index in range(1, 10))))
_DRIVE = re.compile(r"^[A-Za-z]:")
_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")
_PATH_KEYS = frozenset(("path", "source", "workspace", "root", "directory", "location"))
_POSIX_HOST_ROOTS = ("/home/", "/users/", "/workspace/", "/var/", "/tmp/", "/etc/", "/opt/", "/usr/")
_HOST_PATH_BYTES = re.compile(rb"(?i:file:/+|(?<![a-z0-9])[a-z]:[\\/]+|(?<!\\)\\{2,}[^\\/\r\n]+[\\/]|(?<![a-z0-9])/(?:home|users|workspace|tmp|var|etc|opt|usr)/)")


def validate_identity(identity: "ArchiveIdentity") -> None:
    safe_root(identity.package_root)
    for name, pattern in _IDENTIFIERS:
        if pattern.fullmatch(getattr(identity, name)) is None:
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_IDENTITY_INVALID", "Archive identity does not match the delivery contract.")
    if identity.scope not in {"checkpoint", "final"} or not isinstance(identity.package_revision, int) or isinstance(identity.package_revision, bool) or identity.package_revision < 1:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_IDENTITY_INVALID", "Archive identity does not match the delivery contract.")
    if _RFC3339.fullmatch(identity.created_at) is None or not FormatChecker().conforms(identity.created_at, "date-time"):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_IDENTITY_INVALID", "Archive creation time must be RFC3339.")
    try:
        parsed = datetime.fromisoformat(identity.created_at[:-1] + "+00:00" if identity.created_at.endswith(("Z", "z")) else identity.created_at)
    except ValueError as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_IDENTITY_INVALID", "Archive creation time must be RFC3339.") from exc
    if parsed.tzinfo is None:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_IDENTITY_INVALID", "Archive creation time requires a timezone.")


def safe_root(value: str) -> None:
    safe_relative(value)
    if "/" in value:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_ROOT_INVALID", "Package root must be one safe folder name.")


def safe_relative(value: str) -> None:
    if not value or unicodedata.normalize("NFC", value) != value or "\\" in value or "//" in value or value.lower().startswith("file:") or value.startswith("/") or _DRIVE.match(value):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_INVALID", "Archive path is not a safe relative POSIX path.")
    for part in value.split("/"):
        stem = unicodedata.normalize("NFKC", part.split(".", 1)[0]).casefold()
        if not part or part in {".", ".."} or part.endswith((".", " ")) or ":" in part or stem in _DEVICES or any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in part):
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_INVALID", "Archive path is not a safe relative POSIX path.")


def assert_no_public_host_paths(path: str, content: bytes) -> None:
    if _HOST_PATH_BYTES.search(content) is not None:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PUBLIC_HOST_PATH", "Public archive content contains a host path.")
    if not path.casefold().endswith("manifest.json"):
        return
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Public manifest must be valid UTF-8 JSON.") from exc
    _walk(value, "")


def _walk(value, key: str) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _walk(child_value, str(child_key))
    elif isinstance(value, list):
        for child in value:
            _walk(child, key)
    elif isinstance(value, str) and any(token in key.casefold() for token in _PATH_KEYS) and _host_path(value):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PUBLIC_HOST_PATH", "Public manifest contains a host path.")


def _host_path(value: str) -> bool:
    return value.lower().startswith("file:") or value.startswith("\\\\") or _DRIVE.match(value) is not None or value.casefold().startswith(_POSIX_HOST_ROOTS)
