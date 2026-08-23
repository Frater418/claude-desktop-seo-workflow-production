from __future__ import annotations

import unittest

from pydantic import ValidationError

from services.operator_api.gate_context import GateEvidenceDocument
from services.operator_api.step_validation import GateContext


def _evidence_document(classification: str = "local_validation") -> dict[str, str]:
    return {
        "evidence_id": "evidence-gate-proof-001",
        "tool": "jsonschema",
        "report_sha256": "a" * 64,
        "subject_content_sha256": "b" * 64,
        "classification": classification,
        "source": "local fixture validation",
    }


class GateContextTests(unittest.TestCase):
    def test_accepts_local_validation_evidence_document(self) -> None:
        # Given: closed local validation provenance
        payload = _evidence_document("local_validation")
        # When: the context parses the evidence document
        context = GateContext.model_validate({"evidence_by_gate": {}, "evidence_documents": [payload]})
        # Then: the classification is preserved
        self.assertEqual("local_validation", context.evidence_documents[0].classification)

    def test_accepts_local_simulated_evidence_document(self) -> None:
        # Given: closed locally simulated provenance
        payload = _evidence_document("local_simulated")
        # When: the context parses the evidence document
        context = GateContext.model_validate({"evidence_by_gate": {}, "evidence_documents": [payload]})
        # Then: the classification is preserved
        self.assertEqual("local_simulated", context.evidence_documents[0].classification)

    def test_accepts_external_report_evidence_document(self) -> None:
        # Given: closed external-report provenance
        payload = _evidence_document("external_report")
        # When: the context parses the evidence document
        context = GateContext.model_validate({"evidence_by_gate": {}, "evidence_documents": [payload]})
        # Then: the classification is preserved
        self.assertEqual("external_report", context.evidence_documents[0].classification)

    def test_rejects_evidence_document_with_malformed_hash(self) -> None:
        # Given: evidence whose report hash is not lowercase SHA-256
        payload = _evidence_document()
        payload["report_sha256"] = "A" * 64
        # When: the context parses the evidence document
        with self.assertRaises(ValidationError):
            GateEvidenceDocument.model_validate(payload)
        # Then: the malformed provenance is rejected

    def test_rejects_evidence_document_with_blank_tool(self) -> None:
        # Given: evidence without a meaningful tool name
        payload = _evidence_document()
        payload["tool"] = " \t"
        # When: the context parses the evidence document
        with self.assertRaises(ValidationError):
            GateEvidenceDocument.model_validate(payload)
        # Then: blank provenance is rejected

    def test_rejects_evidence_document_with_blank_source(self) -> None:
        # Given: evidence without a meaningful source
        payload = _evidence_document()
        payload["source"] = "\n"
        # When: the context parses the evidence document
        with self.assertRaises(ValidationError):
            GateEvidenceDocument.model_validate(payload)
        # Then: blank provenance is rejected

    def test_rejects_evidence_document_with_unsupported_classification(self) -> None:
        # Given: evidence with an unrecognized classification
        payload = _evidence_document("provider_snapshot")
        # When: the context parses the evidence document
        with self.assertRaises(ValidationError):
            GateEvidenceDocument.model_validate(payload)
        # Then: only closed classifications are accepted

    def test_rejects_evidence_document_with_extra_field(self) -> None:
        # Given: evidence with an unknown field
        payload = _evidence_document()
        payload["untrusted"] = "value"
        # When: the context parses the evidence document
        with self.assertRaises(ValidationError):
            GateEvidenceDocument.model_validate(payload)
        # Then: the evidence schema remains closed


if __name__ == "__main__":
    unittest.main()
