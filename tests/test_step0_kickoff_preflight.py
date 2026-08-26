from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.error import URLError

from services.agent_gateway.kickoff_preflight import (
    KickoffPreflightError,
    build_kickoff_preflight,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, url: str, status: int = 200) -> None:
        self._url = url
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def geturl(self) -> str:
        return self._url


class Step0KickoffPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = json.loads(
            (ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8")
        )
        self.deployment = self.project["market_deployments"][0]
        self.deployment["country_code"] = "DE"
        self.deployment["language"] = "de"
        self.deployment["market_phase"] = "active"
        self.deployment["provider_location_verification"] = {
            "status": "verified",
            "provider_id": "agentseo",
            "target_id": "agentseo-de-country",
            "target_type": "country",
            "location_name": "Germany",
            "provider_location_code": 2276,
            "verified_at": "2026-08-17T00:00:00Z",
            "verification_source": "provider_response",
        }
        self.project["planning_capacity"] = {
            "min": 10,
            "max": 10,
            "source": "operator_confirmed",
            "provisional": False,
            "confirmed_by": "operator-heartweb-admin",
            "confirmed_at": "2026-08-26T00:30:00Z",
        }
        self.intake = {
            "source_sha256": "a" * 64,
            "markdown": (
                "# Projektbriefing\n\n"
                "## Wettbewerber\n\n"
                "- Alpha - alpha.example\n"
                "- Beta - beta.example\n\n"
                "## Zielgruppe\n"
            ),
        }

    def test_builds_location_artifacts_and_bound_url_preflight(self) -> None:
        def opener(request: object, timeout: float) -> FakeResponse:
            self.assertEqual(10.0, timeout)
            url = request.full_url
            if url == "https://alpha.example":
                return FakeResponse(url, 200)
            if url == "https://beta.example":
                raise URLError("TLS unavailable")
            if url == "http://beta.example":
                return FakeResponse(url, 301)
            raise AssertionError(f"Unexpected URL: {url}")

        result = build_kickoff_preflight(
            project_v2=self.project,
            accepted_intake=self.intake,
            deployment_id=self.deployment["deployment_id"],
            location_table_path=ROOT / "standards/domain/provider-location-registry.json",
            manifest_schema_path=ROOT / "standards/manifest-v2.schema.json",
            opener=opener,
        )

        self.assertEqual("DE", result["country"])
        self.assertEqual(2276, result["location_code"])
        self.assertEqual("de", result["language"])
        self.assertEqual(
            {"min": 10, "max": 10, "source": "operator_confirmed", "provisional": False},
            result["capacity_hours_per_week"],
        )
        self.assertEqual(self.deployment, result["deployment_binding"])
        self.assertEqual(
            "outputs/1-pillar-themen.md",
            result["artifact_paths"]["pillar_inventory"],
        )
        self.assertEqual(
            ["https://alpha.example", "https://beta.example"],
            result["competitors"],
        )
        self.assertEqual(
            ["reachable_https", "reachable_http_only"],
            [item["status"] for item in result["competitor_preflight"]],
        )
        self.assertEqual(
            "WARN_COMPETITOR_HTTPS_UNAVAILABLE",
            result["competitor_preflight"][1]["warning_code"],
        )
        self.assertEqual(
            [None, None],
            [item["error_code"] for item in result["competitor_preflight"]],
        )
        self.assertEqual(self.intake["source_sha256"], result["source_binding"]["intake_source_sha256"])
        self.assertRegex(result["source_binding"]["project_v2_sha256"], r"^[a-f0-9]{64}$")
        self.assertRegex(result["source_binding"]["provider_location_registry_sha256"], r"^[a-f0-9]{64}$")
        self.assertRegex(result["source_binding"]["manifest_schema_sha256"], r"^[a-f0-9]{64}$")

    def test_rejects_project_without_confirmed_planning_capacity(self) -> None:
        self.project.pop("planning_capacity")

        with self.assertRaisesRegex(KickoffPreflightError, "ERROR_PLANNING_CAPACITY_REQUIRED"):
            build_kickoff_preflight(
                project_v2=self.project,
                accepted_intake=self.intake,
                deployment_id=self.deployment["deployment_id"],
                location_table_path=ROOT / "standards/domain/provider-location-registry.json",
                manifest_schema_path=ROOT / "standards/manifest-v2.schema.json",
            )

    def test_rejects_active_deployment_without_persisted_verified_target(self) -> None:
        self.deployment["provider_location_verification"] = {
            "status": "unknown",
            "provider_id": "agentseo",
            "target_id": "agentseo-de-country",
            "target_type": "country",
            "location_name": "Germany",
            "provider_location_code": None,
            "verified_at": None,
            "verification_source": None,
        }

        with self.assertRaisesRegex(KickoffPreflightError, "ERROR_LOCATION_UNVERIFIED"):
            build_kickoff_preflight(
                project_v2=self.project,
                accepted_intake=self.intake,
                deployment_id=self.deployment["deployment_id"],
                location_table_path=ROOT / "standards/domain/provider-location-registry.json",
                manifest_schema_path=ROOT / "standards/manifest-v2.schema.json",
            )

    def test_rejects_intake_without_bound_competitor_urls(self) -> None:
        self.intake["markdown"] = "# Projektbriefing\n\n## Wettbewerber\n\nKeine benannt.\n"

        with self.assertRaisesRegex(KickoffPreflightError, "ERROR_COMPETITOR_PREFLIGHT_INPUT_MISSING"):
            build_kickoff_preflight(
                project_v2=self.project,
                accepted_intake=self.intake,
                deployment_id=self.deployment["deployment_id"],
                location_table_path=ROOT / "standards/domain/provider-location-registry.json",
                manifest_schema_path=ROOT / "standards/manifest-v2.schema.json",
            )


if __name__ == "__main__":
    unittest.main()
