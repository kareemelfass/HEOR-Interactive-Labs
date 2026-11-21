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
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DATA = Path(__file__).resolve().parents[1] / "data"
RECON = DATA / "official-reconciliation.json"
INDEX = DATA / "official-index-records.json"
OUT = DATA / "official-page-recheck-latest.json"
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
        self.meta_title = ""
        self._in_title = 0
        self._in_h1 = 0
        self._in_main = 0
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

def code_in(text, code):
    token = (code or "").strip()
    if not token or len(token) > 32:
        return False
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(token.lower()) + r"(?![a-z0-9])", text.lower()))

def heading_matches(parser, title):
    expected = norm(title)
    if not expected:
        return False
    candidates = [norm(" ".join(parser.headings)), norm(parser.meta_title), norm(" ".join(parser.title_chunks))]
    return any(candidate == expected or candidate.startswith(expected + " |") or candidate.startswith(expected + " -")
               for candidate in candidates if candidate)

def examine(url, archived_title, current_title, code):
    attempts = []
    for k in range(3):
        attempt = {"checked_at_utc": now(), "http_status": None}
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            with urlopen(req, timeout=35) as response:
                attempt["http_status"] = response.status
                attempt["final_url"] = response.geturl()
                raw = response.read(2_000_000).decode("utf-8", "replace")
            parser = PrimaryPage()
            parser.feed(raw)
            archived_match = heading_matches(parser, archived_title)
            current_match = heading_matches(parser, current_title)
            main_text = " ".join(parser.main_chunks)
            code_match = code_in(main_text, code)
            attempt.update({
                "page_html_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "archived_title_match_heading_or_meta": archived_match,
                "current_index_title_match_heading_or_meta": current_match,
                "code_match_in_main": code_match,
                "page_has_main_content": bool(main_text),
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

def main():
    reconciliation = json.loads(RECON.read_text(encoding="utf-8"))
    indexed = json.loads(INDEX.read_text(encoding="utf-8"))["records"]
    code_to_current_titles = {}
    for row in indexed:
        if row.get("code") and row.get("index_content_kind") == "Confex Presentation":
            code_to_current_titles.setdefault(row["code"], set()).add(row["title"])
    targets = [r for r in reconciliation["archive_to_official"] if r["status"] != "url_match"]
    targets.sort(key=lambda r: (r.get("archive_code") or "", r.get("archive_url") or ""))
    result = []
    for i, task in enumerate(targets, 1):
        code = task.get("archive_code") or ""
        url = task.get("archive_url") or ""
        current_titles = code_to_current_titles.get(code, set())
        current_title = list(current_titles)[0] if len(current_titles) == 1 else ""
        if not url.startswith(HOST_PREFIX):
            status, attempts = "invalid_or_non_ispor_archive_url", []
        else:
            status, attempts = examine(url, task.get("archive_title") or "", current_title, code)
        result.append({
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
    output = {
        "metadata": {
            "checked_at_utc": now(),
            "source": "Direct HTTP requests to archived ISPOR URLs",
            "checked_targets": len(targets),
            "worker_count": 1,
            "max_attempts_per_target": 3,
            "prior_initial_observations_preserved_in": "official-page-checks.json",
            "repeated_404_does_not_prove_presentation_absence": True,
            "title_comparison_requires_primary_heading_or_meta": True,
            "code_comparison_requires_main_content": True,
            "fully_exhaustive_final_programme_verified": False,
        },
        "counts": dict(counts),
        "results": result,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("RECHECK_COMPLETE", json.dumps(output["counts"]), flush=True)

if __name__ == "__main__":
    main()
