from __future__ import annotations

from collections.abc import Sequence
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import TYPE_CHECKING

from .record_normalization import CanonicalRecord, DeliveryInventoryError

if TYPE_CHECKING:
    from .inventory import InventoryFile, SelectedWorkspaceFile


_CREDENTIAL_NAMES = frozenset((".env", ".npmrc", ".netrc", ".pfx", ".pem", ".key", "api_key", "apikey", "client_secret", "oauth", "credentials", "secret", "secrets", "token", "id_rsa"))


def collect_files(root: Path, selected: Sequence["SelectedWorkspaceFile"], artifacts: tuple[CanonicalRecord, ...]) -> tuple["InventoryFile", ...]:
    from .inventory import InventoryFile, SelectedWorkspaceFile
    checked_root = _root(root)
    known = {artifact.record_id: artifact.content_sha256 for artifact in artifacts}
    paths: set[str] = set()
    files: list[InventoryFile] = []
    for selection in selected:
        if not isinstance(selection, SelectedWorkspaceFile):
            raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Selected file is malformed.")
        source, output = _contained(checked_root, selection.source_path), _relative(selection.output_path)
        if output in paths:
            raise DeliveryInventoryError("DELIVERY_OUTPUT_PATH_DUPLICATE", "Selected output paths are duplicated.")
        paths.add(output)
        if selection.artifact_id not in known:
            raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Selected artifact is unknown.")
        try:
            content = source.read_bytes()
        except OSError as exc:
            raise DeliveryInventoryError("DELIVERY_FILE_UNREADABLE", "Selected file is unreadable.") from exc
        actual = hashlib.sha256(content).hexdigest()
        if actual != selection.source_sha256 or actual != known[selection.artifact_id]:
            raise DeliveryInventoryError("DELIVERY_FILE_HASH_MISMATCH", "Selected file hash does not bind its canonical artifact.")
        files.append(InventoryFile(selection.artifact_id, output, actual, len(content)))
    return tuple(sorted(files, key=lambda item: (item.output_path, item.artifact_id)))


def _root(root: Path) -> Path:
    if _link(root):
        raise DeliveryInventoryError("DELIVERY_PATH_LINK", "Workspace root traverses a link or reparse point.")
    _ancestors(root)
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise DeliveryInventoryError("DELIVERY_WORKSPACE_ROOT_INVALID", "Registered workspace is inaccessible.") from exc
    if not resolved.is_dir():
        raise DeliveryInventoryError("DELIVERY_WORKSPACE_ROOT_INVALID", "Registered workspace is not a directory.")
    return resolved


def _contained(root: Path, raw: str) -> Path:
    relative = _relative(raw)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if _link(current):
            raise DeliveryInventoryError("DELIVERY_PATH_LINK", "Selected path traverses a link or reparse point.")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except ValueError as exc:
        raise DeliveryInventoryError("DELIVERY_PATH_ESCAPE", "Selected path escapes the workspace.") from exc
    except OSError as exc:
        raise DeliveryInventoryError("DELIVERY_FILE_UNREADABLE", "Selected file is unavailable.") from exc
    if not resolved.is_file():
        raise DeliveryInventoryError("DELIVERY_FILE_NOT_REGULAR", "Selected path is not a regular file.")
    return resolved


def _relative(raw: str) -> str:
    if not isinstance(raw, str):
        raise DeliveryInventoryError("DELIVERY_PATH_TRAVERSAL", "Path is invalid.")
    normalized = raw.replace("\\", "/")
    path = PurePosixPath(normalized)
    windows = normalized.startswith("//") or normalized.startswith("//?/") or normalized.startswith("//./") or (len(normalized) >= 2 and normalized[1] == ":")
    if not normalized or normalized.lower().startswith("file:") or path.is_absolute() or windows:
        raise DeliveryInventoryError("DELIVERY_PATH_ABSOLUTE", "Path is host-qualified.")
    if ".." in path.parts:
        raise DeliveryInventoryError("DELIVERY_PATH_TRAVERSAL", "Path traverses upward.")
    if path.as_posix() == "." or any(_credential(part) for part in path.parts):
        raise DeliveryInventoryError("DELIVERY_FILE_CREDENTIAL_LIKE", "Selected path is credential-like.")
    return path.as_posix()


def _credential(part: str) -> bool:
    name = part.lower()
    stem = name.rsplit(".", 1)[0]
    tokens = frozenset(token for token in re.split(r"[._-]+", name) if token)
    return (
        name in _CREDENTIAL_NAMES
        or stem in _CREDENTIAL_NAMES
        or name.endswith((".pfx", ".p12", ".pem", ".key"))
        or bool(tokens.intersection({"credential", "credentials", "oauth", "secret", "secrets", "token", "password", "apikey", "ssh"}))
        or {"access", "token"}.issubset(tokens)
        or {"database", "password"}.issubset(tokens)
        or {"private", "key"}.issubset(tokens)
        or {"client", "secret"}.issubset(tokens)
        or {"api", "key"}.issubset(tokens)
        or {"id", "rsa"}.issubset(tokens)
        or {"id", "ed25519"}.issubset(tokens)
    )


def _ancestors(path: Path) -> None:
    for ancestor in reversed(path.absolute().parents):
        if _link(ancestor):
            raise DeliveryInventoryError("DELIVERY_PATH_LINK", "Workspace root traverses a link or reparse point.")


def _link(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise DeliveryInventoryError("DELIVERY_FILE_UNREADABLE", "Path metadata is unavailable.") from exc
    return stat.S_ISLNK(metadata.st_mode) or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)
