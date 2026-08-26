"""Regression coverage for native Hermes MCP tool identities."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from services.operator_api.step_agents import load_step_agent_registry


ROOT = Path(__file__).resolve().parents[1]


class McpToolIdentityTests(unittest.TestCase):
    def test_every_gateway_operation_uses_native_hermes_mcp_name(self) -> None:
        prompt_registry = json.loads(
            (ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")
        )
        registry = load_step_agent_registry(ROOT, prompt_registry)

        operations = [
            operation
            for step_id in ("0", "1", "1b", "1c", "2", "3", "4a", "4b")
            for operation in registry.for_step(step_id).allowed_operations
        ]

        self.assertTrue(operations)
        for operation in operations:
            self.assertEqual(
                operation["tool_name"],
                f"mcp__heartweb__{operation['operation_id']}",
            )


if __name__ == "__main__":
    unittest.main()
