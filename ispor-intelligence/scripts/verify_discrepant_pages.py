#!/usr/bin/env python3
"""Conservative, repeatable verification of archived ISPOR URL discrepancies.

This DOES NOT overwrite the first historical check and DOES NOT claim a
404 means a withdrawn/nonexistent presentation. Run manually with a separate
capture timestamp. One serial client performs three requests for negative
responses; observations and attempts are retained. A positive identification
requires title evidence from the page heading or metadata, plus the presentation
code in the page's main content. Anything ambiguous stays unverified.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import os
import unicodedata
from collections import Counter
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DATA = Path(__file__).resolve().parents[1] / "data"
RECON = DATA / "official-reconciliation.json"
INDEX = DATA / "official-index-records.json"
OUT = DATA / "official-page-recheck-latest.json"
CONTROL_OUT = DATA / "official-page-controls-latest.json"
RECHECK_BUDGET_SECONDS = 55 * 60
HOST_PREFIX = "https://www.ispor.org/heor-resources/presentations-database/"
USER_AGENT = "Mozilla/5.0 (ISPOR metadata integrity recheck; serial; no abstract redistribution)"

def now():
    return datetime.now(timezone.utc).isoformat()

def norm(value):
    value = unicodedata.normalize("NFKD", html.unescape(value or "")).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))

class PrimaryPage(HTMLParser):
    """Collect only visible page headings and main content, not sidebar titles."""
    def __init__(self):
        super().__init__()
        self.title_chunks = []
        self.headings = []
        self.main_chunks = []
        self.body_chunks = []
        self.has_main = False
        self.meta_title = ""
        self._in_title = 0
        self._in_h1 = 0
        self._in_main = 0
        self._in_body = 0
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        elif tag == "title":
            self._in_title += 1
        elif tag == "h1":
            self._in_h1 += 1
        elif tag == "main":
            self._in_main += 1
            self.has_main = True
        elif tag == "body":
            self._in_body += 1
        elif tag == "meta" and attr.get("property") == "og:title":
            self.meta_title = html.unescape(attr.get("content") or "")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1
        elif tag == "title" and self._in_title:
            self._in_title -= 1
        elif tag == "h1" and self._in_h1:
            self._in_h1 -= 1
        elif tag == "main" and self._in_main:
            self._in_main -= 1
        elif tag == "body" and self._in_body:
            self._in_body -= 1

    def handle_data(self, data):
        if self._skip:
            return
        value = html.unescape(data).strip()
        if not value:
            return
        if self._in_title:
            self.title_chunks.append(value)
        if self._in_h1:
            self.headings.append(value)
        if self._in_main:
            self.main_chunks.append(value)
        if self._in_body:
            self.body_chunks.append(value)

def code_in(text, code):
    token = (code or "").strip()
    if not token or len(token) > 32:
        return False
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(token.lower()) + r"(?![a-z0-9])", text.lower()))

def heading_matches(parser, title):
    expected = norm(title)
    if not expected:
        return False
    candidates = [" ".join(parser.headings), parser.meta_title, " ".join(parser.title_chunks)]
    for candidate in candidates:
        if norm(candidate) == expected:
            return True
        # Apply the site-suffix check BEFORE normalisation removes punctuation.
        # Avoid arbitrary prefix matches, which could confuse distinct study titles.
        for separator in (" | ", " - ", " – ", " — "):
            if separator in candidate and norm(candidate.split(separator, 1)[0]) == expected:
                return True
    return False

def examine(url, archived_title, current_title, code):
    attempts = []
    for k in range(3):
        attempt = {"checked_at_utc": now(), "http_status": None}
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            with urlopen(req, timeout=12) as response:
                attempt["http_status"] = response.status
                attempt["final_url"] = response.geturl()
                raw = response.read(2_000_000).decode("utf-8", "replace")
            parser = PrimaryPage()
            parser.feed(raw)
            archived_match = heading_matches(parser, archived_title)
            current_match = heading_matches(parser, current_title)
            # Some live pages have no semantic <main>. A title match plus a
            # code elsewhere in visible body text is preferable to a false negative.
            content_text = " ".join(parser.main_chunks if parser.has_main else parser.body_chunks)
            code_match = code_in(content_text, code)
            attempt.update({
                "page_html_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "archived_title_match_heading_or_meta": archived_match,
                "current_index_title_match_heading_or_meta": current_match,
                "code_match_in_primary_content": code_match,
                "code_match_in_main": code_match if parser.has_main else None,
                "code_match_scope": "main" if parser.has_main else "body_fallback",
                "page_has_main_content": bool(parser.main_chunks),
            })
            attempts.append(attempt)
            if code_match and archived_match:
                return "heading_and_code_verified", attempts
            if code_match and current_match:
                return "revised_heading_and_code_verified", attempts
            return "reachable_needs_manual_review", attempts
        except HTTPError as exc:
            attempt["http_status"] = exc.code
            attempts.append(attempt)
        except (URLError, TimeoutError, ConnectionError) as exc:
            attempt["error"] = type(exc).__name__ + ": " + str(exc)[:100]
            attempts.append(attempt)
        except Exception as exc:
            attempt["error"] = "unexpected_" + type(exc).__name__ + ": " + str(exc)[:100]
            attempts.append(attempt)
        if k < 2:
            time.sleep((k + 1) * 1.5)
    if all(a.get("http_status") == 404 for a in attempts):
        return "repeated_http_404_unconfirmed", attempts
    if all(a.get("http_status") == 403 for a in attempts):
        return "repeated_http_403_unconfirmed", attempts
    return "inconsistent_http_or_network_unverified", attempts

def spaced_404_observation(status, previous, checked_at=None, previous_controls_passed=False):
    """Return prior observation time only for HTTP 404 seen on runs >=1 hour apart."""
    if status != "repeated_http_404_unconfirmed" or not previous or not previous_controls_passed:
        return None
    if previous.get("classification") not in ("repeated_http_404_unconfirmed",
                                              "cross_run_http_404_unconfirmed"):
        return None
    observations = previous.get("observations") or []
    if not observations:
        return None
    try:
        first = observations[0]["checked_at_utc"]
        prior_time = datetime.fromisoformat(first)
        current_time = checked_at or datetime.now(timezone.utc)
        if current_time - prior_time >= timedelta(hours=1):
            return first
    except (KeyError, ValueError, TypeError):
        return None
    return None

def select_controls(reconciliation, n=10):
    """Stable, independently identifiable URL-matched controls from the same index."""
    candidates = {}
    for row in reconciliation.get("archive_to_official", []):
        url = row.get("archive_url") or ""
        if row.get("status") == "url_match" and url.startswith(HOST_PREFIX):
            candidates[url] = row
    ordered = sorted(candidates, key=lambda url: hashlib.sha256(url.encode("utf-8")).hexdigest())
    if len(ordered) < n:
        raise RuntimeError(f"Need {n} matched controls, found {len(ordered)}")
    return [candidates[url] for url in ordered[:n]]


def check_transport_controls(reconciliation, index_payload, opener=urlopen):
    """A control returning 404/403/5xx indicates an unreliable runner or URL sample.

    This guard is deliberately conservative: one failed control aborts the recheck,
    but a pass does not prove that every negative response is genuine.
    """
    controls = select_controls(reconciliation)
    observations = []
    for row in controls:
        url = row["archive_url"]
        item = {"url": url, "checked_at_utc": now(), "http_status": None}
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            with opener(req, timeout=12) as response:
                item["http_status"] = response.status
                item["final_url"] = response.geturl()
                # Basic source check, without redistributing copyrighted content.
                item["content_type"] = response.headers.get("Content-Type", "")
                item["is_ispor_response"] = item["final_url"].startswith(HOST_PREFIX)
        except HTTPError as exc:
            item["http_status"] = exc.code
        except (URLError, TimeoutError, ConnectionError) as exc:
            item["error"] = type(exc).__name__ + ": " + str(exc)[:100]
        observations.append(item)
        time.sleep(0.15)
    passed = len(observations) == 10 and all(
        o["http_status"] == 200 and o.get("is_ispor_response") for o in observations
    )
    payload = {
        "metadata": {
            "checked_at_utc": now(),
            "index_capture_utc": index_payload.get("metadata", {}).get("retrieved_at_utc"),
            "candidate_definition": "exact URL-matched archive-to-current-index records",
            "sampling": "first 10 URLs in SHA-256 digest sort, deterministic for the snapshot",
            "tested_controls": len(observations),
            "controls_passed": passed,
            "negative_responses_not_evidence_of_presentation_absence": True,
        },
        "results": observations,
    }
    CONTROL_OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if not passed:
        print("CONTROL_CHECK_FAILED_NO_RECHECK_PUBLICATION", observations, flush=True)
    else:
        print("CONTROL_CHECK_PASS", len(observations), flush=True)
    return payload


def main():
    start = time.monotonic()
    reconciliation = json.loads(RECON.read_text(encoding="utf-8"))
    index_payload = json.loads(INDEX.read_text(encoding="utf-8"))
    indexed = index_payload["records"]
    control_audit = check_transport_controls(reconciliation, index_payload)
    if not control_audit["metadata"]["controls_passed"]:
        raise RuntimeError("ISPOR transport-control check failed; do not publish page recheck")
    code_to_current_titles = {}
    for row in indexed:
        if row.get("code") and row.get("index_content_kind") == "Confex Presentation":
            code_to_current_titles.setdefault(row["code"], set()).add(row["title"])
    targets = [r for r in reconciliation["archive_to_official"] if r["status"] != "url_match"]
    targets.sort(key=lambda r: (r.get("archive_code") or "", r.get("archive_url") or ""))
    previous = {}
    previous_controls_passed = False
    if OUT.exists():
        prior = json.loads(OUT.read_text(encoding="utf-8"))
        previous_controls_passed = bool(prior.get("metadata", {}).get("controls_passed"))
        previous = {(r["archive_code"], r["archived_url"]): r
                    for r in prior.get("results", [])}
    result = []
    for i, task in enumerate(targets, 1):
        code = task.get("archive_code") or ""
        url = task.get("archive_url") or ""
        current_titles = code_to_current_titles.get(code, set())
        current_title = list(current_titles)[0] if len(current_titles) == 1 else ""
        if time.monotonic() - start >= RECHECK_BUDGET_SECONDS:
            status, attempts = "not_checked_run_time_budget", []
        elif not url.startswith(HOST_PREFIX):
            status, attempts = "invalid_or_non_ispor_archive_url", []
        else:
            status, attempts = examine(url, task.get("archive_title") or "", current_title, code)
        old = previous.get((code, url))
        previous_observation = spaced_404_observation(status, old, previous_controls_passed=previous_controls_passed)
        persistent_404_across_runs = previous_observation is not None
        if persistent_404_across_runs:
            status = "cross_run_http_404_unconfirmed"
        result.append({
            "persistent_404_observed_across_spaced_runs": persistent_404_across_runs,
            "previous_observation_utc": previous_observation,
            "archive_code": code,
            "archived_url": url,
            "archived_title": task.get("archive_title"),
            "original_reconciliation_status": task["status"],
            "current_index_title": current_title or None,
            "classification": status,
            "observations": attempts,
            "inferences_about_presentation_withdrawal": None,
        })
        if i % 25 == 0:
            print("RECHECK_PROGRESS", i, len(targets), dict(Counter(x["classification"] for x in result)), flush=True)
        time.sleep(0.5)
    counts = Counter(x["classification"] for x in result)
    completed = sum(bool(x["observations"]) for x in result)
    output = {
        "metadata": {
            "checked_at_utc": now(),
            "source": "Direct HTTP requests to archived ISPOR URLs",
            "registered_targets": len(targets),
            "checked_targets": completed,
            "not_checked_run_time_budget": counts.get("not_checked_run_time_budget", 0),
            "run_time_budget_seconds": RECHECK_BUDGET_SECONDS,
            "http_request_timeout_seconds": 12,
            "controls_passed": True,
            "control_audit_file": CONTROL_OUT.name,
            "controls_count": control_audit["metadata"]["tested_controls"],
            "index_capture_utc": index_payload.get("metadata", {}).get("retrieved_at_utc"),
            "worker_count": 1,
            "max_attempts_per_target": 3,
            "prior_initial_observations_preserved_in": "official-page-checks.json",
            "repeated_404_does_not_prove_presentation_absence": True,
            "title_comparison_requires_primary_heading_or_meta": True,
            "code_comparison_requires_main_content": False,
            "code_comparison_uses_body_only_if_main_absent": True,
            "cross_run_404_confirmation_minimum_spacing_hours": 1,
            "cross_run_404_remains_unconfirmed_as_absence": True,
            "fully_exhaustive_final_programme_verified": False,
        },
        "counts": dict(counts),
        "results": result,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("RECHECK_COMPLETE", json.dumps(output["counts"]), flush=True)

if __name__ == "__main__":
    main()
