from __future__ import annotations

import unittest
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from io import BytesIO
import hashlib
import json
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from services.delivery.archive import CHECKSUMS_NAME, MANIFEST_NAME, ZIP_MODE, ZIP_TIMESTAMP, ArchiveBuildRequest, ArchiveEntry, ArchiveIdentity, ArchiveResult, build_archive
from services.delivery.archive_validation import ArchiveLimits, validate_archive
from services.delivery.record_normalization import DeliveryInventoryError


class DeliveryArchiveTests(unittest.TestCase):
    def _identity(self) -> ArchiveIdentity:
        return ArchiveIdentity("delivery-demo", "tenant-demo", "project-demo", "delivery-export-demo-0001", "delivery-package-demo-0001", "checkpoint", 1, "2026-08-20T12:00:00Z")

    def _result(self) -> ArchiveResult:
        return build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("zeta.txt", b"zeta"), ArchiveEntry("alpha/über.txt", b"alpha"))))

    def _rewrite(self, source: bytes, replacements: dict[str, bytes], compression: int = ZIP_DEFLATED, mutate: Callable[[ZipInfo], None] | None = None) -> bytes:
        output = BytesIO()
        with ZipFile(BytesIO(source), "r") as original, ZipFile(output, "w", compression=compression, compresslevel=9) as rewritten:
            for original_info in original.infolist():
                info = ZipInfo(original_info.filename, ZIP_TIMESTAMP)
                info.create_system = 3
                info.external_attr = ZIP_MODE << 16
                info.compress_type = compression
                if mutate is not None:
                    mutate(info)
                rewritten.writestr(info, replacements.get(original_info.filename, original.read(original_info)), compress_type=compression, compresslevel=9)
        return output.getvalue()

    def _encrypted(self, source: bytes) -> bytes:
        altered = bytearray(source)
        for signature, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            start = 0
            while True:
                index = altered.find(signature, start)
                if index < 0:
                    break
                altered[index + offset] |= 1
                start = index + len(signature)
        return bytes(altered)

    def test_reordered_entries_build_byte_identical_archive(self) -> None:
        identity = self._identity()
        entries = (ArchiveEntry("zeta.txt", b"zeta"), ArchiveEntry("alpha/über.txt", b"alpha"))

        first = build_archive(ArchiveBuildRequest(identity, entries))
        second = build_archive(ArchiveBuildRequest(identity, tuple(reversed(entries))))

        self.assertEqual(first.zip_bytes, second.zip_bytes)
        self.assertEqual(first.zip_sha256, second.zip_sha256)

    def test_manifest_checksums_metadata_and_safe_extraction_validate_every_byte(self) -> None:
        result = self._result()

        validated = validate_archive(result.zip_bytes)
        with ZipFile(BytesIO(result.zip_bytes), "r") as archive:
            infos = archive.infolist()
            self.assertEqual(sorted(info.filename for info in infos), [info.filename for info in infos])
            self.assertEqual(["delivery-demo/alpha/über.txt", "delivery-demo/checksums.sha256", "delivery-demo/export-manifest.json", "delivery-demo/zeta.txt"], [info.filename for info in infos])
            for info in infos:
                self.assertEqual(ZIP_TIMESTAMP, info.date_time)
                self.assertEqual(3, info.create_system)
                self.assertEqual(ZIP_MODE << 16, info.external_attr)
                self.assertEqual(ZIP_DEFLATED, info.compress_type)
                self.assertFalse(info.extra)
                self.assertFalse(info.comment)
        manifest = json.loads(result.manifest_bytes)
        self.assertNotIn("zip_sha256", manifest)
        self.assertEqual(result.package_sha256, manifest["package_sha256"])
        checksum_paths = tuple(line.split("  ", 1)[1] for line in result.checksums_bytes.decode("utf-8").splitlines())
        self.assertEqual(("alpha/über.txt", MANIFEST_NAME, "zeta.txt"), checksum_paths)
        self.assertNotIn(CHECKSUMS_NAME, checksum_paths)
        self.assertEqual(result.zip_sha256, hashlib.sha256(result.zip_bytes).hexdigest())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for entry in validated.payloads:
                target = root / entry.relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(entry.content)
            self.assertEqual(b"alpha", (root / "alpha/über.txt").read_bytes())
            self.assertEqual(b"zeta", (root / "zeta.txt").read_bytes())

    def test_builder_rejects_unsafe_reserved_duplicate_and_secret_inputs_without_mutation(self) -> None:
        request = ArchiveBuildRequest(self._identity(), (ArchiveEntry("safe.txt", b"safe"),))
        before = request.entries
        unsafe = ("", "/absolute", "C:/windows", "//host/share", "\\\\?\\C:\\device", "file:///host", "dir\\file", "dir//file", "../escape", "dir/../escape", "control\x00.txt", ".env", "cache/file.txt", "file.swp", MANIFEST_NAME, CHECKSUMS_NAME)
        for path in unsafe:
            with self.subTest(path=path):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry(path, b"safe"),)))
        for entries in ((ArchiveEntry("same.txt", b"a"), ArchiveEntry("same.txt", b"b")), (ArchiveEntry("Name.txt", b"a"), ArchiveEntry("name.txt", b"b"))):
            with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PATH_DUPLICATE"):
                build_archive(ArchiveBuildRequest(self._identity(), entries))
        for path, content in (("safe.txt", b"-----BEGIN PRIVATE KEY-----"), ("safe.txt", b"AKIA1234567890ABCDEF"), ("safe.txt", b"ghp_abcdefghijklmnopqrstuvwx"), ("safe.txt", b"xoxb-123456789012345"), ("safe.txt", b"sk-proj-12345678"), ("safe.txt", b"Bearer abcdefghijklmnop"), ("safe.txt", b"api-key: abcdefghijklmnop"), ("password.txt", b"safe")):
            with self.subTest(path=path, content=content):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry(path, content),)))
        build_archive(request)
        self.assertEqual(before, request.entries)

    def test_builder_rejects_host_paths_in_every_payload_type_and_keeps_public_relative_content(self) -> None:
        hostile = (
            ("artifact.md", b"C:\\Users\\Alice\\project.md"),
            ("notes.txt", b"\\\\server\\share\\project.txt"),
            ("keywords.csv", b"/workspace/heartweb/keywords.csv"),
            ("data.json", b"file:///var/lib/heartweb/data.json"),
        )
        for path, content in hostile:
            with self.subTest(path=path):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PUBLIC_HOST_PATH"):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry(path, content),)))
        allowed = (
            ArchiveEntry("reference.md", b"https://example.test/project.md"),
            ArchiveEntry("reference.txt", b"relative/project.txt"),
            ArchiveEntry("reference.csv", b"relative/project.csv"),
            ArchiveEntry("reference.json", b'{"path":"relative/project.json"}'),
        )
        self.assertEqual(tuple(sorted(entry.relative_path for entry in allowed)), tuple(item.relative_path for item in validate_archive(build_archive(ArchiveBuildRequest(self._identity(), allowed)).zip_bytes).payloads))

    def test_validator_rejects_hostile_names_modes_duplicates_and_metadata_drift(self) -> None:
        result = self._result()
        hostile = BytesIO()
        with ZipFile(hostile, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, mode in (("delivery-demo/", ZIP_MODE), ("delivery-demo/link", 0o120777), ("delivery-demo/same.txt", ZIP_MODE), ("delivery-demo/SAME.txt", ZIP_MODE)):
                info = ZipInfo(name, ZIP_TIMESTAMP)
                info.create_system = 3
                info.external_attr = mode << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, b"x", compress_type=ZIP_DEFLATED, compresslevel=9)
        with self.assertRaises(DeliveryInventoryError):
            validate_archive(hostile.getvalue())
        for compression, mutate in ((ZIP_STORED, None), (ZIP_DEFLATED, lambda info: setattr(info, "date_time", (1981, 1, 1, 0, 0, 0))), (ZIP_DEFLATED, lambda info: setattr(info, "external_attr", 0o100600 << 16)), (ZIP_DEFLATED, lambda info: setattr(info, "extra", b"x"))):
            with self.subTest(compression=compression, mutate=mutate):
                with self.assertRaises(DeliveryInventoryError):
                    validate_archive(self._rewrite(result.zip_bytes, {}, compression, mutate))
        with self.assertRaises(DeliveryInventoryError):
            validate_archive(self._encrypted(result.zip_bytes))
        unsorted = BytesIO()
        with ZipFile(BytesIO(result.zip_bytes), "r") as original, ZipFile(unsorted, "w", compression=ZIP_DEFLATED, compresslevel=9) as rewritten:
            for original_info in reversed(original.infolist()):
                info = ZipInfo(original_info.filename, ZIP_TIMESTAMP)
                info.create_system = 3
                info.external_attr = ZIP_MODE << 16
                info.compress_type = ZIP_DEFLATED
                rewritten.writestr(info, original.read(original_info), compress_type=ZIP_DEFLATED, compresslevel=9)
        with self.assertRaises(DeliveryInventoryError):
            validate_archive(unsorted.getvalue())

    def test_validator_rejects_integrity_tampering_extra_missing_and_limits(self) -> None:
        result = self._result()
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PAYLOAD_MISMATCH"):
            validate_archive(self._rewrite(result.zip_bytes, {"delivery-demo/zeta.txt": b"tampered"}))
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_CHECKSUM_INVALID"):
            validate_archive(self._rewrite(result.zip_bytes, {"delivery-demo/checksums.sha256": b"0" * 64 + b"  zeta.txt\n"}))
        manifest = json.loads(result.manifest_bytes)
        manifest["package_sha256"] = "0" * 64
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PACKAGE_HASH_INVALID"):
            validate_archive(self._rewrite(result.zip_bytes, {"delivery-demo/export-manifest.json": json.dumps(manifest, separators=(",", ":")).encode()}))
        for omitted in ("delivery-demo/export-manifest.json", "delivery-demo/checksums.sha256"):
            altered = BytesIO()
            with ZipFile(BytesIO(result.zip_bytes), "r") as original, ZipFile(altered, "w", compression=ZIP_DEFLATED, compresslevel=9) as rewritten:
                for original_info in original.infolist():
                    if original_info.filename != omitted:
                        info = ZipInfo(original_info.filename, ZIP_TIMESTAMP)
                        info.create_system = 3
                        info.external_attr = ZIP_MODE << 16
                        info.compress_type = ZIP_DEFLATED
                        rewritten.writestr(info, original.read(original_info), compress_type=ZIP_DEFLATED, compresslevel=9)
            with self.subTest(omitted=omitted):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_INTEGRITY_FILES_MISSING"):
                    validate_archive(altered.getvalue())
        extra = BytesIO()
        with ZipFile(BytesIO(result.zip_bytes), "r") as original, ZipFile(extra, "w", compression=ZIP_DEFLATED, compresslevel=9) as rewritten:
            entries = [(info.filename, original.read(info)) for info in original.infolist()]
            entries.append(("delivery-demo/unlisted.txt", b"unlisted"))
            for name, content in sorted(entries):
                info = ZipInfo(name, ZIP_TIMESTAMP)
                info.create_system = 3
                info.external_attr = ZIP_MODE << 16
                info.compress_type = ZIP_DEFLATED
                rewritten.writestr(info, content, compress_type=ZIP_DEFLATED, compresslevel=9)
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_ARCHIVE_PAYLOAD_MISMATCH"):
            validate_archive(extra.getvalue())
        with self.assertRaises(DeliveryInventoryError):
            validate_archive(self._rewrite(result.zip_bytes, {"delivery-demo/zeta.txt": b""}), ArchiveLimits(max_entries=3))
        for limits in (ArchiveLimits(max_file_size=1), ArchiveLimits(max_total_size=1), ArchiveLimits(max_compression_ratio=1)):
            with self.subTest(limits=limits):
                with self.assertRaises(DeliveryInventoryError):
                    validate_archive(result.zip_bytes, limits)

    def test_results_are_frozen_and_validator_returns_deterministic_payload_view(self) -> None:
        result = self._result()
        validated = validate_archive(result.zip_bytes)

        with self.assertRaises(FrozenInstanceError):
            result.package_sha256 = "changed"
        self.assertEqual(("alpha/über.txt", "zeta.txt"), tuple(item.relative_path for item in validated.payloads))
        self.assertEqual(validated, validate_archive(result.zip_bytes))


if __name__ == "__main__":
    unittest.main()
