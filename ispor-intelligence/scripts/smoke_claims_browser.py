#!/usr/bin/env python3
"""Render the deployed dashboard locally and verify real reviewed-claim membership.

Requires: python -m pip install playwright, plus an installed Chrome/Chromium.
Run with an HTTP server serving the repository at http://127.0.0.1:8765/.
"""
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
raw = json.loads((DATA / "official-index-records.json").read_text())["records"]
claims = json.loads((DATA / "reviewed-claims.json").read_text())["claims"]
records = [r for r in raw if r.get("index_content_kind") == "Confex Presentation"]
topics = sorted({t for r in records for t in r.get("topic_groups", [])})
chrome = shutil.which("google-chrome") or shutil.which("chromium")
assert chrome, "A local Chrome/Chromium executable is required"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=chrome,
                                args=["--no-sandbox", "--disable-gpu"])
    page = browser.new_page()
    page.goto("http://127.0.0.1:8765/ispor-intelligence/index.html",
              wait_until="networkidle", timeout=30000)
    page.wait_for_function(
        "(n) => document.getElementById('metricRecords').textContent.replace(/,/g,'') === String(n)",
        arg=len(records), timeout=20000
    )
    # The graph selector lives inside a tab-hidden panel until the user opens it.
    page.locator('button[data-tab="graph"]').click()
    page.locator("#graphFocus").wait_for(state="visible")
    positives = 0
    for topic in topics:
        members = [r for r in records if topic in r.get("topic_groups", [])]
        urls = {r.get("url") for r in members if r.get("url")}
        codes = {str(r.get("code") or "").strip().upper() for r in members if r.get("code")}
        expected = sum(
            c.get("source_url") in urls or
            str(c.get("presentation_code") or "").strip().upper() in codes
            for c in claims
        )
        page.locator("#graphFocus").select_option(topic)
        actual = page.locator("#claimsList .claim-card").count()
        assert actual == min(expected, 8), (
            f"{topic}: expected {min(expected, 8)} reviewed claims, saw {actual}"
        )
        positives += (expected > 0)
    assert positives > 1, "Fixture must test claims in multiple official topic groups"
    hta = [r for r in records if "Health Technology Assessment" in r.get("topic_groups", [])]
    hta_urls = {r.get("url") for r in hta}
    hta_codes = {str(r.get("code") or "").strip().upper() for r in hta}
    assert any(c.get("source_url") in hta_urls or
               str(c.get("presentation_code") or "").strip().upper() in hta_codes
               for c in claims), "HTA focus must have a linked reviewed claim"
    browser.close()
    print("ISPOR_REVIEWED_CLAIMS_BROWSER_PASS", {"topics_tested": len(topics),
                                               "positive_topics": positives})
