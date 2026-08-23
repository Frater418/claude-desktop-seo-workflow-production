from __future__ import annotations

import unittest

from services.delivery.archive import ArchiveBuildRequest, ArchiveEntry, ArchiveIdentity, build_archive
from services.delivery.record_normalization import DeliveryInventoryError


class DeliveryArchiveSecurityTests(unittest.TestCase):
    def _identity(self, **changes: str | int) -> ArchiveIdentity:
        values: dict[str, str | int] = {"package_root": "delivery-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "export_id": "delivery-export-demo-0001", "package_id": "delivery-package-demo-0001", "scope": "checkpoint", "package_revision": 1, "created_at": "2026-08-20T12:00:00Z"}
        values.update(changes)
        return ArchiveIdentity(**values)

    def test_rejects_invalid_identity_fields_and_accepts_offset_time(self) -> None:
        for field, value in (("tenant_id", "tenant-x"), ("project_id", "project-x"), ("export_id", "export-x"), ("package_id", "package-x"), ("scope", "bogus"), ("package_revision", 0), ("package_revision", True), ("created_at", "2026-08-20"), ("created_at", "2026-08-20T12:00:00"), ("created_at", "not-a-time")):
            with self.subTest(field=field, value=value):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(**{field: value}), (ArchiveEntry("safe.txt", b"safe"),)))
        build_archive(ArchiveBuildRequest(self._identity(created_at="2026-08-20T14:00:00+02:00"), (ArchiveEntry("safe.txt", b"safe"),)))

    def test_rejects_portability_credential_and_host_path_inputs(self) -> None:
        paths = ("CON", "NUL.txt", "file.txt:ads", "file. ", "\u0080.txt", "\u200e.txt", "cafe\u0301.txt", "EXPORT-MANIFEST.JSON", "aws_access_key_id.txt", "aws_secret_access_key.txt", "service-account.json", "refresh-token.json")
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry(path, b"safe"),)))
        for content in (b"aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", b"refresh_token=1//0gabcdefghijklmnop", b"Authorization: Basic dXNlcjpwYXNz", b'{"private_key":"-----BEGIN PRIVATE KEY-----"}'):
            with self.subTest(content=content):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("safe.txt", content),)))
        for value in ("/home/alice/project.json", "C:\\Users\\Alice\\project.json", "\\\\host\\share\\file", "file:///host/file"):
            content = ("{\"source_path\":\"" + value.replace("\\", "\\\\") + "\"}").encode()
            with self.subTest(value=value):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("public-manifest.json", content),)))

    def test_rejects_session_and_access_tokens_without_rejecting_prose(self) -> None:
        for content in (b"aws_session_token = IQoJb3abcdefghijklmnop", b"access_token : ya29.abcdefghijklmnop"):
            with self.subTest(content=content):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("safe.txt", content),)))
        build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("notes.txt", b"Discuss access tokens during onboarding."),)))

    def test_rejects_extended_host_context_and_windows_device_aliases(self) -> None:
        for path in ("CONIN$", "CONOUT$", "COM¹.txt", "LPT².txt"):
            with self.subTest(path=path):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry(path, b"safe"),)))
        for key, value in (("source", "C:\\Users\\Alice\\x"), ("workspace_root", "\\\\host\\share\\x"), ("location", "/home/alice/x")):
            content = ("{\"" + key + "\":\"" + value.replace("\\", "\\\\") + "\"}").encode()
            with self.subTest(key=key):
                with self.assertRaises(DeliveryInventoryError):
                    build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("public-manifest.json", content),)))
        build_archive(ArchiveBuildRequest(self._identity(), (ArchiveEntry("public-manifest.json", b'{"route":"/services","url":"https://example.test/services"}'),)))
