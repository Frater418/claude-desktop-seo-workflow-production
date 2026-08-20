"""Tests for the Screaming Frog quality gate runner.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from services.quality_gate_runner.screaming_frog import (
    DEFAULT_EXPORT_TABS,
    QualityGateError,
    build_crawl_command,
    build_evidence,
    resolve_evidence_output_folder,
    parse_capabilities,
    run_crawl,
    summarize_exports,
)


def create_directory_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            shell=False,
        )
        return
    link.symlink_to(target, target_is_directory=True)


def remove_directory_link(link: Path) -> None:
    if os.name == "nt":
        link.rmdir()
        return
    link.unlink()


class ScreamingFrogQualityGateTests(unittest.TestCase):
    def test_parse_capabilities_requires_every_contract_option(self):
        help_text = "--crawl --headless --output-folder --export-format --overwrite --export-tabs --save-report"
        export_text = "\n".join(DEFAULT_EXPORT_TABS)
        report_text = "Crawl Overview\nIssues Overview\nRedirects:Redirect Chains"

        result = parse_capabilities(help_text, export_text, report_text)

        self.assertTrue(result["valid"])
        self.assertEqual([], result["missing_options"])
        self.assertEqual([], result["missing_export_tabs"])

    def test_parse_capabilities_fails_when_required_tab_is_missing(self):
        help_text = "--crawl --headless --output-folder --export-format --overwrite --export-tabs --save-report"
        export_text = "\n".join(tab for tab in DEFAULT_EXPORT_TABS if tab != "Structured Data:All")
        report_text = "Crawl Overview\nIssues Overview\nRedirects:Redirect Chains"

        result = parse_capabilities(help_text, export_text, report_text)

        self.assertFalse(result["valid"])
        self.assertIn("Structured Data:All", result["missing_export_tabs"])

    def test_build_command_rejects_non_http_url(self):
        with self.assertRaises(QualityGateError) as ctx:
            build_crawl_command(
                binary=Path("C:/tools/sf.exe"),
                start_url="ftp://example.com",
                output_folder=Path("C:/crawl"),
            )
        self.assertEqual("ERROR_SCREAMING_FROG_URL_INVALID", ctx.exception.code)

    def test_build_command_uses_argument_list_and_verified_exports(self):
        command = build_crawl_command(
            binary=Path("C:/tools/sf.exe"),
            start_url="https://example.com/",
            output_folder=Path("C:/crawl"),
        )

        self.assertEqual("C:/tools/sf.exe", command[0].replace("\\", "/"))
        self.assertIn("--headless", command)
        self.assertIn("--export-tabs", command)
        self.assertIn(",".join(DEFAULT_EXPORT_TABS), command)
        self.assertNotIn("--save-crawl", command)

    def test_evidence_output_is_derived_beneath_controlled_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            root.mkdir()

            output = resolve_evidence_output_folder(root, "tenant-heartweb", "project-example", "run-example-001")

            self.assertEqual(root.resolve() / "tenants" / "tenant-heartweb" / "projects" / "project-example" / "runs" / "run-example-001" / "screaming-frog", output)

    def test_run_crawl_rejects_nonempty_derived_output_before_mutation_or_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            root.mkdir()
            output = resolve_evidence_output_folder(root, "tenant-heartweb", "project-example", "run-example-001")
            output.mkdir(parents=True)
            (output / "prior-crawl.csv").write_text("Address\nhttps://example.test/\n", encoding="utf-8")

            with patch.object(Path, "mkdir", autospec=True) as mkdir:
                with patch("services.quality_gate_runner.screaming_frog.preflight") as preflight:
                    with patch("services.quality_gate_runner.screaming_frog.subprocess.run") as subprocess_run:
                        with self.assertRaises(QualityGateError) as context:
                            run_crawl(
                                "https://example.test/", root, "tenant-heartweb", "run-example-001",
                                "project-example", "dep-example-de",
                            )

        self.assertEqual("ERROR_SCREAMING_FROG_OUTPUT_NOT_EMPTY", context.exception.code)
        mkdir.assert_not_called()
        preflight.assert_not_called()
        subprocess_run.assert_not_called()

    def test_intermediate_symlink_escape_is_rejected_before_mkdir_preflight_or_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            sentinel = outside / "external-target-sentinel.txt"
            sentinel.write_text("must-survive-link-cleanup", encoding="utf-8")
            (root / "tenants").mkdir()
            tenant_link = root / "tenants" / "tenant-heartweb"
            create_directory_link(tenant_link, outside)

            try:
                with patch.object(Path, "mkdir", autospec=True) as mkdir:
                    with patch("services.quality_gate_runner.screaming_frog.preflight") as preflight:
                        with patch("services.quality_gate_runner.screaming_frog.subprocess.run") as subprocess_run:
                            with self.assertRaises(QualityGateError) as context:
                                run_crawl(
                                    "https://example.test/", root, "tenant-heartweb", "run-example-001",
                                    "project-example", "dep-example-de",
                                )
            finally:
                remove_directory_link(tenant_link)

            self.assertEqual("ERROR_SCREAMING_FROG_OUTPUT_PATH_INVALID", context.exception.code)
            mkdir.assert_not_called()
            preflight.assert_not_called()
            subprocess_run.assert_not_called()
            self.assertFalse((outside / "projects").exists())
            self.assertTrue(outside.is_dir())
            self.assertEqual("must-survive-link-cleanup", sentinel.read_text(encoding="utf-8"))

    def test_hostile_tenant_is_rejected_before_preflight_mkdir_or_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            root.mkdir()
            with patch("services.quality_gate_runner.screaming_frog.preflight") as preflight:
                with self.assertRaises(QualityGateError) as context:
                    run_crawl(
                        "https://example.test/", root, "../tenant-escape", "run-example-001",
                        "project-example", "dep-example-de",
                    )

            self.assertEqual("ERROR_SCREAMING_FROG_ID_INVALID", context.exception.code)
            preflight.assert_not_called()
            self.assertFalse((root / "tenants").exists())

    def test_summarize_exports_counts_unique_urls_and_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            internal = root / "internal_all.csv"
            with internal.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Address",
                        "Content Type",
                        "Status Code",
                        "Indexability",
                        "Title 1",
                        "Meta Description 1",
                        "H1-1",
                        "Canonical Link Element 1",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Address": "https://example.com/",
                        "Content Type": "text/html; charset=UTF-8",
                        "Status Code": "200",
                        "Indexability": "Indexable",
                        "Title 1": "Home",
                        "Meta Description 1": "Description",
                        "H1-1": "Welcome",
                        "Canonical Link Element 1": "https://example.com/",
                    }
                )
                writer.writerow(
                    {
                        "Address": "https://example.com/missing",
                        "Content Type": "text/html",
                        "Status Code": "404",
                        "Indexability": "Non-Indexable",
                        "Title 1": "",
                        "Meta Description 1": "",
                        "H1-1": "",
                        "Canonical Link Element 1": "",
                    }
                )
                writer.writerow(
                    {
                        "Address": "https://example.com/site.css",
                        "Content Type": "text/css",
                        "Status Code": "200",
                        "Indexability": "Indexable",
                        "Title 1": "",
                        "Meta Description 1": "",
                        "H1-1": "",
                        "Canonical Link Element 1": "",
                    }
                )

            external = root / "response_codes_all.csv"
            with external.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["Address", "Content Type", "Status Code"])
                writer.writeheader()
                writer.writerow(
                    {
                        "Address": "https://external.example/page",
                        "Content Type": "text/html",
                        "Status Code": "200",
                    }
                )

            summary = summarize_exports(root)

            self.assertEqual(3, summary["url_count"])
            self.assertEqual(2, summary["html_url_count"])
            self.assertEqual(1, summary["findings"]["status_4xx"])
            self.assertEqual(1, summary["findings"]["non_indexable"])
            self.assertEqual(1, summary["findings"]["missing_titles"])
            self.assertEqual(1, summary["findings"]["canonical_issues"])

    def test_summary_separates_resource_404_and_records_final_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            internal = root / "internal_all.csv"
            with internal.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Address", "Content Type", "Status Code", "Crawl Depth", "Indexability",
                        "Title 1", "Meta Description 1", "H1-1", "H2-1", "Canonical Link Element 1",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Address": "https://example.com/", "Content Type": "text/html", "Status Code": "200",
                        "Crawl Depth": "0", "Indexability": "Indexable", "Title 1": "Home",
                        "Meta Description 1": "Description", "H1-1": "Home", "H2-1": "Details",
                        "Canonical Link Element 1": "https://example.com/",
                    }
                )
                writer.writerow(
                    {
                        "Address": "https://example.com/missing.png", "Content Type": "text/html", "Status Code": "404",
                        "Crawl Depth": "1", "Indexability": "Non-Indexable", "Title 1": "",
                        "Meta Description 1": "", "H1-1": "", "H2-1": "", "Canonical Link Element 1": "",
                    }
                )
            summary = summarize_exports(root)
            self.assertEqual("https://example.com/", summary["final_url"])
            self.assertEqual(1, summary["findings"]["resource_4xx"])
            self.assertEqual(0, summary["findings"]["internal_html_4xx"])
            self.assertEqual(0, summary["findings"]["broken_internal_links"])

    def test_evidence_validates_against_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = root / "internal_all.csv"
            export.write_text("Address,Status Code\nhttps://example.com/,200\n", encoding="utf-8")
            summary = summarize_exports(root)
            evidence = build_evidence(
                run_id="run-example-001",
                project_id="project-example",
                deployment_id="dep-example-de",
                start_url="https://example.com/",
                binary_path="C:/tools/sf.exe",
                capability_hash="a" * 64,
                started_at="2026-08-19T03:00:00Z",
                completed_at="2026-08-19T03:01:00Z",
                output_folder=root,
                summary=summary,
                url_limit=500,
            )
            schema_path = Path(__file__).resolve().parents[1] / "standards" / "quality" / "screaming-frog-crawl.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
            self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
