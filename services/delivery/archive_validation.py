from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import hashlib
import zlib
from typing import Final, Literal
from zipfile import BadZipFile, LargeZipFile, ZIP_DEFLATED, ZipFile, ZipInfo

from pydantic import BaseModel, ConfigDict, ValidationError

from .archive import ARCHIVE_FORMAT_VERSION, CHECKSUMS_NAME, MANIFEST_NAME, ZIP_MODE, ZIP_TIMESTAMP, ArchiveEntry, ArchiveFile, ArchiveIdentity, ArchiveManifest, _blocked_path, _canonical_bytes, _checksums, _manifest_data, _preimage
from .archive_security import assert_no_public_host_paths, safe_relative as _safe_relative, safe_root as _safe_root, validate_identity as _validate_identity
from .notion_import_security import assert_no_credentials
from .record_normalization import DeliveryInventoryError


_UTF8_FLAG: Final = 0x800


@dataclass(frozen=True, slots=True)
class ArchiveLimits:
    max_entries: int = 256
    max_file_size: int = 16 * 1024 * 1024
    max_total_size: int = 64 * 1024 * 1024
    max_compression_ratio: int = 100


@dataclass(frozen=True, slots=True)
class ArchiveValidationResult:
    identity: ArchiveIdentity
    package_sha256: str
    manifest: ArchiveManifest
    manifest_bytes: bytes
    checksums_bytes: bytes
    payloads: tuple[ArchiveEntry, ...]


class _ManifestFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    path: str
    sha256: str
    size: int


class _ManifestIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    package_root: str
    tenant_id: str
    project_id: str
    export_id: str
    package_id: str
    scope: str
    package_revision: int
    created_at: str


class _ParsedManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    format_version: Literal[ARCHIVE_FORMAT_VERSION]
    identity: _ManifestIdentity
    files: tuple[_ManifestFile, ...]
    package_sha256: str


def validate_archive(zip_bytes: bytes, limits: ArchiveLimits = ArchiveLimits()) -> ArchiveValidationResult:
    _validate_limits(limits)
    try:
        with ZipFile(BytesIO(zip_bytes), "r") as archive:
            infos = tuple(archive.infolist())
            root, relative_infos = _validate_infos(archive, infos, limits)
            contents = tuple((relative, archive.read(info)) for relative, info in relative_infos)
    except DeliveryInventoryError:
        raise
    except (BadZipFile, LargeZipFile, OSError, ValueError, UnicodeDecodeError, zlib.error, EOFError, RuntimeError, NotImplementedError) as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_INVALID", "Archive bytes cannot be opened safely.") from exc
    by_name = {relative: content for relative, content in contents}
    manifest_bytes = by_name.get(MANIFEST_NAME)
    checksums_bytes = by_name.get(CHECKSUMS_NAME)
    if manifest_bytes is None or checksums_bytes is None:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_INTEGRITY_FILES_MISSING", "Archive must contain one manifest and checksum file.")
    manifest = _parse_manifest(manifest_bytes)
    if manifest.identity.package_root != root:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_ROOT_MISMATCH", "Manifest package root does not match archive entry root.")
    payloads = tuple(ArchiveEntry(relative, content) for relative, content in contents if relative not in {MANIFEST_NAME, CHECKSUMS_NAME})
    for payload in payloads:
        assert_no_public_host_paths(payload.relative_path, payload.content)
    _validate_manifest_payloads(manifest, payloads)
    _validate_checksums(checksums_bytes, payloads, manifest_bytes)
    assert_no_credentials(by_name)
    return ArchiveValidationResult(manifest.identity, manifest.package_sha256, manifest, manifest_bytes, checksums_bytes, payloads)


def _validate_limits(limits: ArchiveLimits) -> None:
    values = (limits.max_entries, limits.max_file_size, limits.max_total_size, limits.max_compression_ratio)
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in values):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_LIMIT_INVALID", "Archive limits must be positive integers.")


def _validate_infos(archive: ZipFile, infos: tuple[ZipInfo, ...], limits: ArchiveLimits) -> tuple[str, tuple[tuple[str, ZipInfo], ...]]:
    if archive.comment or not infos or len(infos) > limits.max_entries or tuple(info.filename for info in infos) != tuple(sorted(info.filename for info in infos)):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_METADATA_INVALID", "Archive metadata or entry count violates the portable archive contract.")
    seen: set[str] = set()
    folded: set[str] = set()
    total = 0
    root = ""
    relative_infos: list[tuple[str, ZipInfo]] = []
    for info in infos:
        relative, entry_root = _relative_info(info)
        if not root:
            root = entry_root
        if root != entry_root or relative in seen or relative.casefold() in folded:
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_DUPLICATE", "Archive paths must share one root and be unique without case-fold collisions.")
        _validate_info_metadata(info, limits)
        total += info.file_size
        if total > limits.max_total_size:
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_SIZE_LIMIT", "Archive total uncompressed size exceeds its limit.")
        seen.add(relative)
        folded.add(relative.casefold())
        relative_infos.append((relative, info))
    if {MANIFEST_NAME, CHECKSUMS_NAME}.issubset(seen) and len({name for name in seen if name in {MANIFEST_NAME, CHECKSUMS_NAME}}) == 2:
        return root, tuple(relative_infos)
    raise DeliveryInventoryError("DELIVERY_ARCHIVE_INTEGRITY_FILES_MISSING", "Archive must contain one manifest and checksum file.")


def _relative_info(info: ZipInfo) -> tuple[str, str]:
    if info.is_dir() or info.filename.endswith("/"):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_NONREGULAR", "Archive cannot contain directory entries.")
    try:
        _safe_relative(info.filename)
    except DeliveryInventoryError as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_INVALID", "Archive contains an unsafe member path.") from exc
    root, separator, relative = info.filename.partition("/")
    if not separator or not relative:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_INVALID", "Archive members must be below one package root.")
    try:
        _safe_root(root)
        _safe_relative(relative)
    except DeliveryInventoryError as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PATH_INVALID", "Archive contains an unsafe member path.") from exc
    return relative, root


def _validate_info_metadata(info: ZipInfo, limits: ArchiveLimits) -> None:
    expected_flags = _UTF8_FLAG if not info.filename.isascii() else 0
    ratio = info.file_size / max(info.compress_size, 1)
    if info.flag_bits != expected_flags or info.date_time != ZIP_TIMESTAMP or info.create_system != 3 or info.external_attr != ZIP_MODE << 16 or info.extra or info.comment or info.compress_type != ZIP_DEFLATED or info.file_size > limits.max_file_size or ratio > limits.max_compression_ratio:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_METADATA_INVALID", "Archive entry metadata violates the portable archive contract.")


def _parse_manifest(manifest_bytes: bytes) -> ArchiveManifest:
    try:
        parsed = _ParsedManifest.model_validate_json(manifest_bytes)
    except ValidationError as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Archive manifest must be closed canonical JSON.") from exc
    identity = ArchiveIdentity(parsed.identity.package_root, parsed.identity.tenant_id, parsed.identity.project_id, parsed.identity.export_id, parsed.identity.package_id, parsed.identity.scope, parsed.identity.package_revision, parsed.identity.created_at)
    try:
        _validate_identity(identity)
        if _blocked_path(identity.package_root):
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Archive manifest root is blocked.")
    except DeliveryInventoryError as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Archive manifest identity is invalid.") from exc
    files = tuple(ArchiveFile(item.path, item.sha256, item.size) for item in parsed.files)
    if not files or parsed.package_sha256 != hashlib.sha256(_canonical_bytes(_preimage(identity, files))).hexdigest():
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PACKAGE_HASH_INVALID", "Archive manifest package hash does not bind its payload metadata.")
    manifest = ArchiveManifest(identity, files, parsed.package_sha256)
    if manifest_bytes != _canonical_bytes(_manifest_data(manifest)):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Archive manifest bytes are not canonical.")
    return manifest


def _validate_manifest_payloads(manifest: ArchiveManifest, payloads: tuple[ArchiveEntry, ...]) -> None:
    paths = tuple(item.relative_path for item in manifest.files)
    if tuple(sorted(paths)) != paths or len(set(paths)) != len(paths) or len({path.casefold() for path in paths}) != len(paths):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Manifest payload paths must be sorted and collision-free.")
    for item in manifest.files:
        try:
            _safe_relative(item.relative_path)
        except DeliveryInventoryError as exc:
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Manifest payload path is unsafe.") from exc
        if _blocked_path(item.relative_path):
            raise DeliveryInventoryError("DELIVERY_ARCHIVE_MANIFEST_INVALID", "Manifest payload path is blocked by archive policy.")
    expected = tuple((item.relative_path, item.sha256, item.size) for item in manifest.files)
    actual = tuple((entry.relative_path, hashlib.sha256(entry.content).hexdigest(), len(entry.content)) for entry in payloads)
    if expected != actual:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_PAYLOAD_MISMATCH", "Archive payload bytes do not match the manifest.")


def _validate_checksums(checksums_bytes: bytes, payloads: tuple[ArchiveEntry, ...], manifest_bytes: bytes) -> None:
    files = tuple(ArchiveFile(entry.relative_path, hashlib.sha256(entry.content).hexdigest(), len(entry.content)) for entry in payloads)
    if checksums_bytes != _checksums(files, manifest_bytes):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_CHECKSUM_INVALID", "Checksum file bytes are not canonical.")
    try:
        rows = tuple(line.split("  ", 1) for line in checksums_bytes.decode("utf-8").splitlines())
    except UnicodeDecodeError as exc:
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_CHECKSUM_INVALID", "Checksum file must be UTF-8.") from exc
    expected_entries = (*payloads, ArchiveEntry(MANIFEST_NAME, manifest_bytes))
    expected = tuple((hashlib.sha256(entry.content).hexdigest(), entry.relative_path) for entry in sorted(expected_entries, key=lambda item: item.relative_path))
    if tuple((row[0], row[1]) for row in rows if len(row) == 2) != expected or len(rows) != len(expected):
        raise DeliveryInventoryError("DELIVERY_ARCHIVE_CHECKSUM_INVALID", "Checksum file does not exactly bind archive payload entries.")


__all__ = ["ArchiveLimits", "ArchiveValidationResult", "validate_archive"]
