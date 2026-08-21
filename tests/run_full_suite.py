#!/usr/bin/env python3
"""Run the complete local Heartweb verification suite.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unittest
from collections.abc import Iterator
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
CONTRACTS = TESTS / "contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ACCEPTANCE_COUNT = re.compile(r"Ergebnis: (\d+)/(\d+) Tests erfolgreich bestanden\.")
PHASE_COUNT = re.compile(r"\[PHASE PASSED\] .+: (\d+) tests")


def iter_tests(suite: unittest.TestSuite) -> Iterator[unittest.TestCase]:
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from iter_tests(test)
        else:
            yield test


def module_path(test: unittest.TestCase) -> Path | None:
    module = sys.modules.get(test.__class__.__module__)
    module_file = getattr(module, "__file__", None)
    return Path(module_file).resolve() if module_file else None


def discover_root_suite() -> unittest.TestSuite:
    discovered = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py")
    root_suite = unittest.TestSuite()
    for test in iter_tests(discovered):
        path = module_path(test)
        if path is None or CONTRACTS not in path.parents:
            root_suite.addTest(test)
    return root_suite


def discover_contract_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.discover(str(CONTRACTS), pattern="test_*.py")


def run_unittest_phase(phase: str) -> int:
    suites = {
        "root": ("Root unittest discovery", discover_root_suite),
        "contracts": ("Contract unittest discovery", discover_contract_suite),
    }
    label, discover = suites[phase]
    suite = discover()
    count = suite.countTestCases()
    if count == 0:
        print(f"[PHASE FAILED] {label}: discovered zero tests. Check the test directory and pattern.", flush=True)
        return 1

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    print(f"[PHASE PASSED] {label}: {count} tests", flush=True)
    return 0


def run_acceptance_phase() -> int:
    label = "Acceptance runner"
    print(f"\n[PHASE] {label}", flush=True)
    completed = subprocess.run(
        [sys.executable, "tests/run_acceptance_tests.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    print(completed.stdout, end="", flush=True)
    print(completed.stderr, end="", file=sys.stderr, flush=True)
    if completed.returncode != 0:
        print(f"[PHASE FAILED] {label}: exited with code {completed.returncode}.", flush=True)
        return completed.returncode

    count_match = ACCEPTANCE_COUNT.search(completed.stdout)
    if count_match is None:
        print(f"[PHASE FAILED] {label}: did not report a test count.", flush=True)
        return 1
    passed, total = (int(value) for value in count_match.groups())
    if passed != total or total == 0:
        print(f"[PHASE FAILED] {label}: reported {passed}/{total} successful tests.", flush=True)
        return 1

    print(f"[PHASE PASSED] {label}: {total} tests", flush=True)
    return total


def run_phase(label: str, command: list[str]) -> int:
    print(f"\n[PHASE] {label}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True, capture_output=True)
    print(completed.stdout, end="", flush=True)
    print(completed.stderr, end="", file=sys.stderr, flush=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    count_match = PHASE_COUNT.search(completed.stdout)
    if count_match is None:
        print(f"[PHASE FAILED] {label}: did not report a test count.", flush=True)
        raise SystemExit(1)
    return int(count_match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unittest-phase", choices=("root", "contracts"))
    arguments = parser.parse_args()
    if arguments.unittest_phase:
        return run_unittest_phase(arguments.unittest_phase)

    acceptance_count = run_acceptance_phase()
    if acceptance_count == 0:
        return 1

    root_count = run_phase(
        "Root unittest discovery excluding tests/contracts",
        [sys.executable, str(Path(__file__).resolve()), "--unittest-phase", "root"],
    )
    contract_count = run_phase(
        "Contract unittest discovery",
        [sys.executable, str(Path(__file__).resolve()), "--unittest-phase", "contracts"],
    )
    total_count = acceptance_count + root_count + contract_count
    print(
        "\n[FULL SUITE PASSED] "
        f"Acceptance: {acceptance_count} tests. "
        f"Root unittest discovery: {root_count} tests. "
        f"Contract unittest discovery: {contract_count} tests. "
        f"Total: {total_count} tests.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
