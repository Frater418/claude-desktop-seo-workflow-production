from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_repository_index import GENERATED_PATHS, generate_outputs

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "00_admin/repository-index/DOCUMENT_REGISTRY.json"


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class RepositoryIndexTests(unittest.TestCase):
    def test_generated_registry_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/build_repository_index.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_generation_is_byte_identical(self) -> None:
        first = generate_outputs(ROOT)
        second = generate_outputs(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(set(first), GENERATED_PATHS)

    def test_registry_entries_have_valid_paths_hashes_and_ids(self) -> None:
        entries = _registry()["entries"]
        self.assertEqual(entries, sorted(entries, key=lambda entry: entry["path"]))
        self.assertEqual(len({entry["document_id"] for entry in entries}), len(entries))
        self.assertEqual(len({entry["path"] for entry in entries}), len(entries))
        for entry in entries:
            path = ROOT / entry["path"]
            self.assertTrue(path.is_file(), entry["path"])
            data = path.read_bytes()
            self.assertEqual(entry["size_bytes"], len(data))
            self.assertEqual(entry["content_sha256"], hashlib.sha256(data).hexdigest())
            self.assertNotIn("\\", entry["path"])

    def test_critical_authorities_and_warnings_are_classified(self) -> None:
        by_path = {entry["path"]: entry for entry in _registry()["entries"]}
        self.assertEqual(by_path["00_admin/PROJECT_STATE.md"]["authority_level"], 100)
        self.assertTrue(by_path["00_admin/PROJECT_STATE.md"]["default_retrieval"])
        self.assertEqual(by_path["00_admin/DECISIONS.md"]["lifecycle"], "current_authority")
        self.assertEqual(
            by_path[".hermes/plans/2026-08-22-repository-authority-rag-index.md"]["lifecycle"],
            "active_plan",
        )
        for entry_document in ("AGENTS.md", "CLAUDE.md", "README.md"):
            self.assertEqual(by_path[entry_document]["lifecycle"], "current_authority")
            self.assertTrue(by_path[entry_document]["default_retrieval"])

    def test_stale_and_evidence_documents_are_opt_in(self) -> None:
        for entry in _registry()["entries"]:
            if entry["lifecycle"] in {"historical", "superseded", "evidence"}:
                self.assertFalse(entry["default_retrieval"], entry["path"])

    def test_historical_and_superseded_markdown_docs_have_visible_lifecycle_banner(self) -> None:
        for entry in _registry()["entries"]:
            if entry["format"] != "md" or entry["lifecycle"] not in {"historical", "superseded"}:
                continue
            if not entry["path"].startswith(("docs/", ".hermes/plans/")):
                continue
            text = (ROOT / entry["path"]).read_text(encoding="utf-8")
            self.assertIn("Lifecycle:", text[:1200], entry["path"])

    def test_related_and_supersession_targets_resolve(self) -> None:
        for entry in _registry()["entries"]:
            for related in entry["related_paths"]:
                self.assertTrue((ROOT / related).exists(), (entry["path"], related))
            if entry["superseded_by"] is not None:
                self.assertTrue((ROOT / entry["superseded_by"]).exists(), entry["path"])

    def test_generated_outputs_are_not_recursive_sources(self) -> None:
        indexed = {entry["path"] for entry in _registry()["entries"]}
        self.assertFalse(indexed.intersection(GENERATED_PATHS))

    def test_no_sensitive_or_customer_paths_are_indexed(self) -> None:
        for entry in _registry()["entries"]:
            lower = entry["path"].casefold()
            self.assertNotIn("/.env", lower)
            self.assertNotIn("/credentials", lower)
            self.assertNotIn("/secrets", lower)
            self.assertNotIn("/tokens", lower)
            self.assertNotIn("kunden/", lower)

    def test_generated_markdown_has_no_forbidden_dash_characters(self) -> None:
        for relative in GENERATED_PATHS:
            if not relative.endswith(".md"):
                continue
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("\u2014", text, relative)
            self.assertNotIn("\u2013", text, relative)

    def test_generated_markdown_relative_links_resolve(self) -> None:
        for relative in GENERATED_PATHS:
            if not relative.endswith(".md"):
                continue
            source = ROOT / relative
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                target_path = target.split("#", 1)[0]
                resolved = (source.parent / target_path).resolve()
                resolved.relative_to(ROOT.resolve())
                self.assertTrue(resolved.exists(), f"{relative} -> {target}")

    def test_session_bootstrap_has_binding_read_order(self) -> None:
        text = (ROOT / "00_admin/SESSION_BOOTSTRAP.md").read_text(encoding="utf-8")
        project_pos = text.index("00_admin/PROJECT_STATE.md")
        decisions_pos = text.index("00_admin/DECISIONS.md")
        index_pos = text.index("00_admin/REPOSITORY_INDEX.md")
        plans_pos = text.index(".hermes/plans/INDEX.md")
        self.assertLess(project_pos, decisions_pos)
        self.assertLess(decisions_pos, index_pos)
        self.assertLess(index_pos, plans_pos)
        self.assertIn("semantic retriever", text.casefold())

    def test_jsonl_matches_registry_order_and_content(self) -> None:
        registry_entries = _registry()["entries"]
        lines = (ROOT / "00_admin/repository-index/DOCUMENT_REGISTRY.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual([json.loads(line) for line in lines], registry_entries)

    def test_check_detects_drift(self) -> None:
        outputs = generate_outputs(ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)
            for relative, data in outputs.items():
                target = output_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            drift_target = output_root / "docs/INDEX.md"
            drift_target.write_text("drift\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_repository_index.py",
                    "--check",
                    "--output-root",
                    str(output_root),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("docs/INDEX.md", result.stdout)

    def test_schema_declares_closed_registry_and_entry_records(self) -> None:
        schema = json.loads(
            (ROOT / "standards/documentation/document-registry.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["entry"]["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {"schema_version", "registry_version", "source_commit", "authority_order", "entries"},
        )


if __name__ == "__main__":
    unittest.main()