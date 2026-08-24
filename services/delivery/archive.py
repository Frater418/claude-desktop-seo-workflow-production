from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO
import hashlib
import json
import re
from typing import Final
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .notion_import_security import assert_no_credentials
from .record_normalization import DeliveryInventoryError
from .archive_security import assert_no_public_host_paths, safe_relative as _safe_relative, safe_root as _safe_root, validate_identity as _validate_identity


ARCHIVE_FORMAT_VERSION: Final = "1.0"
CHECKSUMS_NAME: Final = "checksums.sha256"
MANIFEST_NAME: Final = "export-manifest.json"
ZIP_TIMESTAMP: Final = (1980, 1, 1, 0, 0, 0)
ZIP_MODE: Final = 0o100644
ZIP_FLAGS: Final = 0x800
_RESERVED_NAMES: Final = frozenset((CHECKSUMS_NAME, MANIFEST_NAME))
_BLOCKED_PARTS: Final = frozenset((".git", ".svn", "__pycache__", ".cache", "cache", "tmp", "temp", ".tmp"))
_CREDENTIAL_PARTS: Final = frozenset((".env", ".npmrc", ".netrc", "api_key", "apikey", "client_secret", "credential", "credentials", "oauth", "secret", "secrets", "token", "password", "id_rsa", "id_ed25519"))
_WINDOWS_DRIVE: Final = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True, slots=True)
class ArchiveIdentity:
    package_root: str
    tenant_id: str
    project_id: str
    export_id: str
    package_id: str
    scope: str
    package_revision: int
    created_at: str


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    relative_path: str
    content: bytes


@dataclass(frozen=True, slots=True)
class ArchiveBuildRequest:
    identity: ArchiveIdentity
    entries: tuple[ArchiveEntry, ...]


@dataclass(frozen=True, slots=True)
class ArchiveFile:
    relative_path: str
    sha256: str
    size: int


@dataclass(frozen=True, slots=True)
class ArchiveManifest:
    identity: ArchiveIdentity
    files: tuple[ArchiveFile, ...]
    package_sha256: str


@dataclass(frozen=True, slots=True)
class ArchiveResult:
    zip_bytes: bytes
    zip_sha256: str
    package_sha256: str
    manifest_bytes: bytes
    manifest: ArchiveManifest
    checksums_bytes: bytes


def build_archive(request: ArchiveBuildRequest) -> ArchiveResult:
    _validate_identity(request.identity)
    if _blocked_path(request.identity.package_root):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_ROOT_INVALID", "Package root is blocked by archive policy.")
    payloads = _validated_entries(request.entries)
    files = tuple(ArchiveFile(entry.relative_path, hashlib.sha256(entry.content).hexdigest(), len(entry.content)) for entry in payloads)
    package_sha256 = hashlib.sha256(_canonical_bytes(_preimage(request.identity, files))).hexdigest()
    manifest = ArchiveManifest(request.identity, files, package_sha256)
    manifest_bytes = _canonical_bytes(_manifest_data(manifest))
    checksums_bytes = _checksums(files, manifest_bytes)
    assert_no_credentials({MANIFEST_NAME: manifest_bytes, CHECKSUMS_NAME: checksums_bytes})
    archive_entries = (*payloads, ArchiveEntry(MANIFEST_NAME, manifest_bytes), ArchiveEntry(CHECKSUMS_NAME, checksums_bytes))
    zip_bytes = _zip(request.identity.package_root, archive_entries)
    return ArchiveResult(zip_bytes, hashlib.sha256(zip_bytes).hexdigest(), package_sha256, manifest_bytes, manifest, checksums_bytes)


def _validated_entries(entries: Sequence[ArchiveEntry]) -> tuple[ArchiveEntry, ...]:
    if not entries:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_EMPTY", "An archive requires at least one payload entry.")
    checked: list[ArchiveEntry] = []
    names: set[str] = set()
    folded: set[str] = set()
    for entry in entries:
        _safe_relative(entry.relative_path)
        if entry.relative_path.casefold() in {name.casefold() for name in _RESERVED_NAMES}:
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_RESERVED_PATH", "Payload entries cannot replace archive integrity files.")
        if _blocked_path(entry.relative_path):
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_BLOCKED", "Payload path is credential-like, cached, or temporary.")
        if entry.relative_path in names or entry.relative_path.casefold() in folded:
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_DUPLICATE", "Payload paths must be unique without case-fold collisions.")
        names.add(entry.relative_path)
        folded.add(entry.relative_path.casefold())
        checked.append(entry)
        assert_no_public_host_paths(entry.relative_path, entry.content)
    assert_no_credentials({entry.relative_path: entry.content for entry in checked})
    return tuple(sorted(checked, key=lambda item: item.relative_path))


def _blocked_path(value: str) -> bool:
    for part in value.split("/"):
        lowered = part.casefold()
        tokens = frozenset(token for token in re.split(r"[._-]+", lowered) if token)
        if lowered in _BLOCKED_PARTS or lowered in {"aws_access_key_id.txt", "aws_secret_access_key.txt", "service-account.json", "refresh-token.json"} or lowered == ".env" or lowered.startswith(".env.") or lowered.endswith(("~", ".swp", ".swo", ".tmp", ".temp", ".bak", ".backup", ".orig")) or lowered.startswith("~$") or lowered in _CREDENTIAL_PARTS or bool(tokens.intersection(_CREDENTIAL_PARTS)):
            return True
    return False


def _identity_data(identity: ArchiveIdentity) -> dict[str, str | int]:
    return {"created_at": identity.created_at, "export_id": identity.export_id, "package_id": identity.package_id, "package_revision": identity.package_revision, "package_root": identity.package_root, "project_id": identity.project_id, "scope": identity.scope, "tenant_id": identity.tenant_id}


def _files_data(files: tuple[ArchiveFile, ...]) -> list[dict[str, str | int]]:
    return [{"path": item.relative_path, "sha256": item.sha256, "size": item.size} for item in files]


def _preimage(identity: ArchiveIdentity, files: tuple[ArchiveFile, ...]) -> dict[str, str | dict[str, str | int] | list[dict[str, str | int]]]:
    return {"files": _files_data(files), "format_version": ARCHIVE_FORMAT_VERSION, "identity": _identity_data(identity)}


def _manifest_data(manifest: ArchiveManifest) -> dict[str, str | dict[str, str | int] | list[dict[str, str | int]]]:
    return {**_preimage(manifest.identity, manifest.files), "package_sha256": manifest.package_sha256}


def _canonical_bytes(value: dict[str, str | dict[str, str | int] | list[dict[str, str | int]]]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _checksums(files: tuple[ArchiveFile, ...], manifest_bytes: bytes) -> bytes:
    rows = [*files, ArchiveFile(MANIFEST_NAME, hashlib.sha256(manifest_bytes).hexdigest(), len(manifest_bytes))]
    return "".join(f"{item.sha256}  {item.relative_path}\n" for item in sorted(rows, key=lambda item: item.relative_path)).encode("utf-8")


def _zip(root: str, entries: tuple[ArchiveEntry, ...]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
        archive.comment = b""
        for entry in sorted(entries, key=lambda item: item.relative_path):
            info = ZipInfo(f"{root}/{entry.relative_path}", ZIP_TIMESTAMP)
            info.create_system = 3
            info.external_attr = ZIP_MODE << 16
            info.compress_type = ZIP_DEFLATED
            info.flag_bits = ZIP_FLAGS if not entry.relative_path.isascii() or not root.isascii() else 0
            info.extra = b""
            info.comment = b""
            archive.writestr(info, entry.content, compress_type=ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


__all__ = ["ARCHIVE_FORMAT_VERSION", "CHECKSUMS_NAME", "MANIFEST_NAME", "ZIP_MODE", "ZIP_TIMESTAMP", "ArchiveBuildRequest", "ArchiveEntry", "ArchiveFile", "ArchiveIdentity", "ArchiveManifest", "ArchiveResult", "build_archive"]
