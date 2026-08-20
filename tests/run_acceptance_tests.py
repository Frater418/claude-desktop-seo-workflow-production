#!/usr/bin/env python3
"""
Automatisierter Akzeptanztest-Runner fuer das Heartweb SEO & GEO Framework
Autor: Raphael Rechberger
Version: 1.4.0
"""

import sys
import os
import json
import subprocess
from pathlib import Path

def run_test(name: str, fn):
    print(f"[RUNNING] {name} ... ", end="", flush=True)
    try:
        fn()
        print("OK")
        return True, None
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

def test_manifest_schema():
    import jsonschema
    schema_path = Path("standards/manifest.schema.json")
    manifest_path = Path("tests/fixtures/sample_manifest.json")
    
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    jsonschema.validate(instance=manifest, schema=schema)

def test_solver():
    cmd = [
        sys.executable,
        "mcp/tools/capacity_matrix_solver.py",
        "--input", "tests/fixtures/sample_cluster_keywords.json",
        "--weeks", "17"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "# 120-Tage-Content-Plan" in res.stdout
    assert "Interne Verlinkungs-Map" in res.stdout
    assert "GEO-Typ" in res.stdout

def test_jsonld_validator():
    cmd = [
        sys.executable,
        "mcp/tools/validate_schema_jsonld.py",
        "--input", "tests/fixtures/sample_schema_graph.json",
        "--strict"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "[BESTANDEN]" in res.stdout

def test_design_system():
    css_path = Path("standards/design-system.css")
    css = css_path.read_text(encoding="utf-8")
    assert ".definition-block" in css
    assert ".evidence-container" in css
    assert ".comparison-table" in css
    assert "@import" not in css

def test_fail_fast_prompts():
    prompts = list(Path("prompts").glob("*.xml.md"))
    assert len(prompts) == 9
    for p in prompts:
        content = p.read_text(encoding="utf-8")
        assert "<prompt_metadata>" in content
        assert "<validation_rules>" in content
        assert "ERROR_" in content or "Regel" in content

def test_end_to_end_fixtures():
    # 1. Test sample_briefing.md
    briefing_path = Path("tests/fixtures/sample_briefing.md")
    assert briefing_path.exists()
    cmd1 = [sys.executable, "mcp/tools/validate_schema_jsonld.py", "--input", str(briefing_path), "--strict"]
    res1 = subprocess.run(cmd1, capture_output=True, text=True, check=True)
    assert "[BESTANDEN]" in res1.stdout

    # 2. Test sample_landingpage.html
    html_path = Path("tests/fixtures/sample_landingpage.html")
    assert html_path.exists()
    cmd2 = [sys.executable, "mcp/tools/validate_schema_jsonld.py", "--input", str(html_path), "--strict"]
    res2 = subprocess.run(cmd2, capture_output=True, text=True, check=True)
    assert "[BESTANDEN]" in res2.stdout

def test_prompt0_operational_contract():
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_prompt0_contract.py",
        "-v",
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)

def main():
    print("==================================================")
    print("Heartweb SEO/GEO Framework - Acceptance Test Suite")
    print("Autor: Raphael Rechberger | Version: 1.4.0")
    print("==================================================")
    
    tests = [
        ("TEST-01: Manifest Schema & Fixture Validation", test_manifest_schema),
        ("TEST-02: Deterministic Capacity Matrix Solver v1.3.0", test_solver),
        ("TEST-03: Schema.org JSON-LD Validator CLI & GEO Graph", test_jsonld_validator),
        ("TEST-04: Standalone Design System CSS & GEO Tokens", test_design_system),
        ("TEST-05: Strict Fail-Fast Validation Across All 9 Prompts", test_fail_fast_prompts),
        ("TEST-06: End-to-End Briefing & Landingpage Fixtures", test_end_to_end_fixtures),
        ("TEST-07: Step-0 Operational Contract", test_prompt0_operational_contract)
    ]
    
    passed = 0
    for name, fn in tests:
        ok, _ = run_test(name, fn)
        if ok:
            passed += 1
            
    print("==================================================")
    print(f"Ergebnis: {passed}/{len(tests)} Tests erfolgreich bestanden.")
    print("==================================================")
    sys.exit(0 if passed == len(tests) else 1)

if __name__ == "__main__":
    main()
