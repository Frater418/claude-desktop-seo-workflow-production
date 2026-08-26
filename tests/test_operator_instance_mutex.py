from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from scripts.start_operator_console import (
    HermesRuntimeSettings,
    HermesRuntimeStartupError,
    OperatorInstanceMutex,
    _ensure_hermes_runtime,
    _tool_search_disabled,
)


class OperatorInstanceMutexTests(unittest.TestCase):
    def test_abandoned_windows_mutex_transfers_ownership_to_waiter(self) -> None:
        kernel32 = Mock()
        kernel32.WaitForSingleObject.return_value = 0x00000080
        mutex = OperatorInstanceMutex(handle=123, owned=False)

        with patch("scripts.start_operator_console.ctypes.WinDLL", return_value=kernel32):
            self.assertTrue(mutex.wait_for_ownership(1.0))
            self.assertTrue(mutex.owned)
            mutex.close()

        kernel32.ReleaseMutex.assert_called_once()
        kernel32.CloseHandle.assert_called_once()
        self.assertIsNone(mutex.handle)


class HermesRuntimeProfileTests(unittest.TestCase):
    def test_tool_search_must_be_explicitly_disabled(self) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.yaml"
            path.write_text("tools:\n  tool_search:\n    enabled: 'off'\n", encoding="utf-8")
            self.assertTrue(_tool_search_disabled(path))

            path.write_text("tools:\n  tool_search:\n    enabled: auto\n", encoding="utf-8")
            self.assertFalse(_tool_search_disabled(path))

    def test_runtime_start_fails_before_healthcheck_when_tool_search_is_not_disabled(self) -> None:
        settings = HermesRuntimeSettings("http://127.0.0.1:8642", "test-key")
        with (
            patch("scripts.start_operator_console._tool_search_disabled", return_value=False),
            patch("scripts.start_operator_console._health_ready") as health_ready,
            self.assertRaises(HermesRuntimeStartupError) as raised,
        ):
            _ensure_hermes_runtime(settings)

        self.assertIn("tools.tool_search.enabled=off", str(raised.exception))
        health_ready.assert_not_called()


if __name__ == "__main__":
    unittest.main()
