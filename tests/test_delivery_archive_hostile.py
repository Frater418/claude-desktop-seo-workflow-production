from __future__ import annotations

from io import BytesIO
import hashlib
import unittest
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from services.delivery.archive import CHECKSUMS_NAME, MANIFEST_NAME, ZIP_MODE, ZIP_TIMESTAMP, ArchiveEntry, ArchiveFile, ArchiveIdentity, ArchiveManifest, _canonical_bytes, _checksums, _manifest_data, _preimage
from services.delivery.archive_validation import validate_archive
from services.delivery.record_normalization import DeliveryInventoryError


class DeliveryArchiveHostileTests(unittest.TestCase):
    def _archive(self, members: tuple[tuple[str, int, bytes], ...], comment: bytes = b"") -> bytes:
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            archive.comment = comment
            for name, mode, content in members:
                info = ZipInfo(name, ZIP_TIMESTAMP)
                info.create_system = 3
                info.external_attr = mode << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, content, compress_type=ZIP_DEFLATED, compresslevel=9)
        return output.getvalue()

    def _rejects(self, members: tuple[tuple[str, int, bytes], ...], code: str) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, code):
            validate_archive(self._archive(members))

    def _canonical_hostile(self, path: str, content: bytes) -> bytes:
        identity = ArchiveIdentity("delivery-demo", "tenant-demo", "project-demo", "delivery-export-demo-0001", "delivery-package-demo-0001", "checkpoint", 1, "2026-08-20T12:00:00Z")
        file = ArchiveFile(path, hashlib.sha256(content).hexdigest(), len(content))
        package_sha256 = hashlib.sha256(_canonical_bytes(_preimage(identity, (file,)))).hexdigest()
        manifest = ArchiveManifest(identity, (file,), package_sha256)
        manifest_bytes = _canonical_bytes(_manifest_data(manifest))
        checksums = _checksums((file,), manifest_bytes)
        entries = ((path, content), (MANIFEST_NAME, manifest_bytes), (CHECKSUMS_NAME, checksums))
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, value in sorted(entries):
                info = ZipInfo(f"delivery-demo/{name}", ZIP_TIMESTAMP)
                info.create_system, info.external_attr, info.compress_type = 3, ZIP_MODE << 16, ZIP_DEFLATED
                archive.writestr(info, value, compress_type=ZIP_DEFLATED, compresslevel=9)
        return output.getvalue()

    def test_rejects_directory_only_member(self) -> None:
        self._rejects((("delivery-demo/", ZIP_MODE, b""),), "DELIVERY_ARCHIVE_NONREGULAR")

    def test_rejects_symlink_only_member(self) -> None:
        self._rejects((("delivery-demo/link", 0o120777, b"target"),), "DELIVERY_ARCHIVE_METADATA_INVALID")

    def test_rejects_exact_duplicate_only_members(self) -> None:
        self._rejects((("delivery-demo/same.txt", ZIP_MODE, b"a"), ("delivery-demo/same.txt", ZIP_MODE, b"b")), "DELIVERY_ARCHIVE_PATH_DUPLICATE")

    def test_rejects_casefold_duplicate_only_members(self) -> None:
        self._rejects((("delivery-demo/A.txt", ZIP_MODE, b"a"), ("delivery-demo/a.txt", ZIP_MODE, b"b")), "DELIVERY_ARCHIVE_PATH_DUPLICATE")

    def test_rejects_multiple_top_level_roots(self) -> None:
        self._rejects((("alpha/a.txt", ZIP_MODE, b"a"), ("beta/b.txt", ZIP_MODE, b"b")), "DELIVERY_ARCHIVE_PATH_DUPLICATE")

    def test_rejects_archive_comment(self) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_METADATA_INVALID"):
            validate_archive(self._archive((("delivery-demo/a.txt", ZIP_MODE, b"a"),), b"comment"))

    def test_rejects_per_entry_comment(self) -> None:
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            info = ZipInfo("delivery-demo/a.txt", ZIP_TIMESTAMP)
            info.create_system, info.external_attr, info.compress_type, info.comment = 3, ZIP_MODE << 16, ZIP_DEFLATED, b"comment"
            archive.writestr(info, b"a", compress_type=ZIP_DEFLATED)
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_METADATA_INVALID"):
            validate_archive(output.getvalue())

    def test_rejects_unicode_filename_without_utf8_flag(self) -> None:
        altered = bytearray(self._archive((("delivery-demo/über.txt", ZIP_MODE, b"a"),)))
        central = altered.index(b"PK\x01\x02")
        altered[central + 9] &= ~8
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_METADATA_INVALID"):
            validate_archive(bytes(altered))

    def test_normalizes_invalid_zip_bytes(self) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_INVALID"):
            validate_archive(b"PK\x03\x04\x00")

    def test_validator_rejects_public_manifest_source_host_path(self) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PUBLIC_HOST_PATH"):
            validate_archive(self._canonical_hostile("public-manifest.json", b'{"source":"C:\\\\Users\\\\Alice\\\\project.json"}'))

    def test_validator_rejects_public_manifest_workspace_root_host_path(self) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PUBLIC_HOST_PATH"):
            validate_archive(self._canonical_hostile("public-manifest.json", b'{"workspace_root":"C:\\\\Users\\\\Alice\\\\project.json"}'))

    def test_validator_rejects_host_paths_in_canonical_non_manifest_payloads(self) -> None:
        hostile = (
            ("artifact.md", b"C:\\Users\\Alice\\project.md"),
            ("notes.txt", b"\\\\server\\share\\project.txt"),
            ("keywords.csv", b"/home/alice/keywords.csv"),
            ("data.json", b"file:///opt/heartweb/data.json"),
        )
        for path, content in hostile:
            with self.subTest(path=path):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PUBLIC_HOST_PATH"):
                    validate_archive(self._canonical_hostile(path, content))

    def test_validator_accepts_canonical_non_manifest_https_and_relative_payloads(self) -> None:
        allowed = (
            ("reference.md", b"https://example.test/project.md"),
            ("reference.txt", b"relative/project.txt"),
            ("reference.csv", b"relative/project.csv"),
            ("reference.json", b'{"path":"relative/project.json"}'),
        )
        for path, content in allowed:
            with self.subTest(path=path):
                validate_archive(self._canonical_hostile(path, content))

    def test_validator_rejects_access_token_payload(self) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, "NOTION_CREDENTIAL_LEAK"):
            validate_archive(self._canonical_hostile("safe.txt", b"access_token=ya29.abcdefghijklmnop"))

    def test_validator_rejects_aws_session_token_payload(self) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, "NOTION_CREDENTIAL_LEAK"):
            validate_archive(self._canonical_hostile("safe.txt", b"aws_session_token=IQoJb3abcdefghijklmnop"))

    def test_validator_rejects_windows_device_paths(self) -> None:
        for path in ("CONIN$", "CONOUT$", "COM¹.txt", "LPT².txt"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PATH_INVALID"):
                    validate_archive(self._canonical_hostile(path, b"safe"))

    def test_normalizes_negative_local_header_offset(self) -> None:
        altered = bytearray(self._canonical_hostile("safe.txt", b"safe"))
        central = altered.index(b"PK\x01\x02")
        altered[central + 42:central + 46] = (0xFFFFFFFF).to_bytes(4, "little")
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_INVALID"):
            validate_archive(bytes(altered))

    def test_normalizes_invalid_utf8_central_filename(self) -> None:
        altered = bytearray(self._canonical_hostile("über.txt", b"safe"))
        start = 0
        while True:
            central = altered.index(b"PK\x01\x02", start)
            if int.from_bytes(altered[central + 8:central + 10], "little") & 0x800:
                altered[central + 46] = 0xFF
                break
            start = central + 4
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_INVALID"):
            validate_archive(bytes(altered))


if __name__ == "__main__":
    unittest.main()
