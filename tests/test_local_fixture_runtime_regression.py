from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_local_runtime import (
    ROOT,
    RUN,
    _profile,
    _request,
    _service,
    _seed,
    _validator,
)


EXPECTED_HASHES = {
    "provider_outputs": "adeb1e847aabbbf75d7a932051640a81a23e8872f6407091c8d0d4c893da4bb5",
    "context_package": "a18b5f9f5b805590f6f77e30e2d6b64e1c6654fcd76145a715face58e98fbc73",
    "llm_request": "3190d0c048fcb86fc2f325857ee510adb6d86f59a5054fa863c56c90f5a314e3",
    "llm_result": "23bc49b7d4f167226fe590892e7b0413796a92278c06b82b84c3869f6d7fe695",
    "context-packages.json": "0606b8946472274719b9cd28abce1bc66906f12c0b50d1ab982fc6de0e33f960",
    "llm-runs.json": "05da1d3dad93b2f6e867878c587143f22090a4b2f205252f6ffed2850541c5b4",
    f"runs/{RUN}.json": "5977142ee341186c136aa8b53d681708e3084d7fc21648b71fb650ceb2667ce9",
}


class LocalFixtureRuntimeRegressionTests(unittest.TestCase):
    def test_step_zero_simulated_execution_preserves_runtime_bytes_on_exact_replay(self) -> None:
        # Given: the deterministic Step 0 local fixture runtime
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _seed(workspace, "0")
            service = _service(repository)
            request = _request("0", service.fixture_provider.fixture_sha256)
            projection_paths = (
                "context-packages.json",
                "llm-runs.json",
                f"runs/{RUN}.json",
            )

            # When: the same simulated request is prepared twice
            prepared = service.prepare_step(repository, ROOT, _validator(), _profile(), request)
            first_projection = {
                relative: (workspace / "v2" / "operator" / relative).read_bytes()
                for relative in projection_paths
            }
            replayed = service.prepare_step(repository, ROOT, _validator(), _profile(), request)
            replayed_projection = {
                relative: (workspace / "v2" / "operator" / relative).read_bytes()
                for relative in projection_paths
            }

            # Then: the candidate, canonical contracts, and existing projections are exact
            self.assertEqual(b"candidate output", prepared.candidate_bytes)
            self.assertEqual(prepared, replayed)
            self.assertEqual(first_projection, replayed_projection)
            self.assertEqual(
                EXPECTED_HASHES,
                {
                    "provider_outputs": prepared.provider_outputs.canonical_sha256,
                    "context_package": hashlib.sha256(
                        json.dumps(prepared.context_package, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                    "llm_request": hashlib.sha256(
                        json.dumps(prepared.llm_request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                    "llm_result": hashlib.sha256(
                        json.dumps(prepared.llm_result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                    **{relative: hashlib.sha256(content).hexdigest() for relative, content in first_projection.items()},
                },
            )


if __name__ == "__main__":
    unittest.main()
