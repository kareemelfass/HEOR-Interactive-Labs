#!/usr/bin/env python3
"""Actual rendered-DOM assertions shared by pull-request CI and pre-commit refresh.

Serve the repository root on http://127.0.0.1:8765 before running.
No external services are contacted by this test.
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
browser = shutil.which("google-chrome") or shutil.which("chromium")
assert browser, "Chromium/Chrome executable missing"
url = "http://127.0.0.1:8765/ispor-intelligence/index.html"
result = subprocess.run(
    [browser, "--headless", "--no-sandbox", "--disable-gpu",
     "--virtual-time-budget=20000", "--dump-dom", url],
    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90
)
assert result.returncode == 0, f"Chrome failed: {result.stderr[-1500:]}"
html = result.stdout
rows = json.loads((ROOT / "ispor-intelligence/data/official-index-records.json").read_text())["records"]
presentations = sum(r["index_content_kind"] == "Confex Presentation" for r in rows)
sessions = sum(r["index_content_kind"] == "Confex Session" for r in rows)
assert presentations >= 2500 and sessions > 0 and presentations + sessions == len(rows)
assert f'id="metricRecords">{presentations:,}<' in html, "Dashboard denominator includes sessions"
assert 'id="sourceName">Official ISPOR search index<' in html
assert 'id="diseaseMissing">' in html
assert "16 of 16 editorial topics · 32 proposed hypotheses" in html
assert "Archived URL returned HTTP 404 at check time (unconfirmed)" in html
assert "archive only, not in captured official index" in html.lower()
assert "Related ISPOR presentations" not in html
print("ISPOR_CORRECTIVE_BROWSER_PASS", {
    "presentations": presentations, "sessions_excluded": sessions,
    "hypotheses": 32, "provisional_404_label": True
})
