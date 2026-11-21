#!/usr/bin/env python3
"""Build a provenance-aware ISPOR Europe 2026 metadata knowledge graph.

This tool does not redistribute abstract bodies and never converts keyword
associations into scientific findings. The input is an independent archive,
not an official conference census.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_SOURCE = "https://justinsyu.github.io/ispor-eu-nov-2026/ispor_europe_2026_abstracts.json"
ISPOR_HOST = re.compile(r"^https://(?:www\.)?ispor\.org/", re.I)

PATTERNS = {
    "JCA": r"\bJCA\b|joint clinical assessment|EU HTA regulation|\bHTAR\b",
    "AI": r"\bartificial intelligence\b|\bAI[- ](?:assisted|enabled|based|driven|agent)\b|\blarge language models?\b|\bLLMs?\b|generative AI|machine learning",
    "Economic evaluation": r"cost[- ]effective|cost[- ]utility|budget impact|economic evaluation|\bQALY\b|\bICER\b",
    "RWE": r"real[- ]world (?:evidence|data)|\bRWE\b|\bRWD\b|electronic (?:health|medical) record|claims database",
    "Causal inference": r"target trial emulation|causal inference|propensity score|external control arm|marginal structural model",
    "Indirect comparisons": r"indirect treatment comparison|\bMAIC\b|\bSTC\b|network meta.analysis|\bNMA\b",
    "ML-NMR": r"\bML[- ]?NMR\b|multilevel network meta.regression",
    "Survival modelling": r"survival extrapolat|survival model|Kaplan.Meier|flexible parametric|M.spline|mortality extrapolat",
    "Bayesian methods": r"\bBayesian\b|\bposterior\b|\bprior distribution\b",
    "MFN pricing": r"most.fav(?:or|our)ed.nation|\bMFN\b|TrumpRx",
    "Market access": r"market access|launch sequenc|reimbursement|price referencing|pricing polic|affordability",
    "Evidence synthesis": r"systematic literature review|\bSLR\b|evidence synthesis|meta.analysis",
    "PICO": r"\bPICO\b|population.intervention.comparator.outcome",
    "Estimands": r"\bestimands?\b|intercurrent event",
    "Patient-reported outcomes": r"patient.reported outcome|\bPROMs?\b|\bEQ.5D\b|health.utility",
    "Medical devices": r"medical devices?|digital therapeutics|health technology|diagnostic accuracy",
}
DISEASES = {
    "Oncology": r"\boncolog|\bcancer\b|\btumou?r\b|\bcarcinoma\b|\bleukemia\b|\bmyeloma\b",
    "Rare disease": r"rare diseases?|orphan medicines?|ultra.rare",
    "Metabolic / obesity": r"\bobesity\b|\bdiabetes\b|\bmetabolic\b|\bGLP.1\b",
    "Cardiovascular": r"cardiovascular|\bheart failure\b|\bstroke\b|\batrial fibrillation\b",
    "Neurology": r"neurolog|\balzheimer|\bparkinson|\bmultiple sclerosis\b",
    "Respiratory": r"\basthma\b|\bCOPD\b|respiratory",
    "Infectious disease": r"\binfection\b|\bHIV\b|\bviral\b|\bantibiotic\b",
}
ABSTRACT_KEYS = ("abstract_text", "abstract", "structured_abstract", "abstract_body",
                 "summary", "objectives", "objective", "methods", "results",
                 "conclusions", "background", "full_text", "body")


def canonical_key(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def get(obj, *names):
    if not isinstance(obj, dict):
        return None
    keys = {canonical_key(k): k for k in obj}
    for name in names:
        k = keys.get(canonical_key(name))
        if k is not None and obj[k] is not None:
            return obj[k]
    return None


def flatten(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, (tuple, list)):
        return " ".join(filter(None, map(flatten, value)))
    if isinstance(value, dict):
        return " ".join(filter(None, map(flatten, value.values())))
    return ""


def extract_rows(value):
    if isinstance(value, list):
        return value
    arrays = []

    def walk(v, depth):
        if depth > 3:
            return
        if isinstance(v, list):
            if v and isinstance(v[0], dict):
                arrays.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x, depth + 1)

    walk(value, 0)
    arrays.sort(
        key=lambda rows: len(rows) + (
            100000 if get(rows[0], "title", "presentation_title", "abstract_title") else 0
        ),
        reverse=True,
    )
    return arrays[0] if arrays else []


def official_url(row):
    options = [
        get(row, "source_url", "ispor_url", "presentation_url", "original_url",
            "url", "source_link", "link", "href"),
        get(get(row, "source", "metadata", "links"), "url", "source_url", "href", "official_url"),
    ]
    for item in options:
        if isinstance(item, str) and ISPOR_HOST.match(item):
            return item
    match = re.search(
        r"https://(?:www\.)?ispor\.org/[^\s\"'<>]+",
        flatten(get(row, "source", "citation", "source_metadata", "source_reference")),
        flags=re.I,
    )
    return match.group(0) if match else None


def classify(text, patterns):
    return [name for name, pattern in patterns.items() if re.search(pattern, text, flags=re.I)]


def normalize(row, index):
    title = flatten(get(row, "title", "presentation_title", "abstract_title", "name", "paper_title")).strip()
    if len(title) < 8:
        return None
    parts = [get(row, key) for key in ABSTRACT_KEYS]
    abstract = flatten([x for x in parts if x is not None])
    topics = flatten(get(row, "topic_groups", "topics", "topic", "categories", "category", "topic_area"))
    diseases = flatten(get(row, "disease_areas", "disease_area", "diseases", "disease"))
    txt = " ".join([title, abstract, topics])
    code = flatten(get(row, "abstract_number", "presentation_code", "presentation_id",
                       "abstract_id", "code", "number", "id")).strip()[:80]
    code = code or "hash-" + hashlib.sha256(title.lower().encode()).hexdigest()[:15]
    return {
        "id": code,
        "title": title,
        "url": official_url(row),
        "year": 2026,
        "tags": classify(txt, PATTERNS),
        "diseases": classify(" ".join([title, abstract, diseases]), DISEASES),
        "has_abstract": len(abstract.strip()) > 40,
    }


def build(source, *, allow_small=False):
    rows = extract_rows(source)
    if len(rows) < 1000 and not allow_small:
        raise ValueError(f"Only {len(rows)} candidate input rows: refusing to replace full-corpus KG")
    result = []
    seen = set()
    for i, row in enumerate(rows):
        r = normalize(row, i)
        if not r:
            continue
        key = r["url"] or re.sub(r"\s+", " ", r["title"].lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(r)
    if len(result) < 1000 and not allow_small:
        raise ValueError(f"Only {len(result)} usable records: refusing partial-corpus KG")
    return result, len(rows)


def outputs(records, input_rows, source_url):
    themes = sorted({tag for r in records for tag in r["tags"]})
    nodes = [
        {"id": "topic:" + t, "label": t, "type": "theme",
         "provenance": "Reproducible keyword mention"} for t in themes
    ]
    edges = []
    for i, r in enumerate(records):
        pid = "presentation:" + re.sub(r"[^a-zA-Z0-9_-]", "_", r["id"]) + "_" + str(i)
        nodes.append({"id": pid, "label": r["title"],
                      "type": "presentation", "url": r["url"], "abstract_code": r["id"]})
        for t in r["tags"]:
            edges.append({"source": pid, "target": "topic:" + t, "relation": "MENTIONS",
                          "provenance": "Keyword pattern applied to title and abstract; not a validated finding"})
    metadata = {
        "conference": "ISPOR Europe 2026",
        "input": source_url,
        "snapshot": "Independent pre-conference archive collected 2026-08-24",
        "official_final_census": False,
        "method": "Multi-label regex-based metadata extraction; not author-validated",
        "interpretation": "Edges indicate keyword associations only, not causal relationships or methodological findings.",
        "input_rows": input_rows,
        "unique_usable_records": len(records),
        "linked_ispor_records": sum(bool(r["url"]) for r in records),
        "abstract_text_present": sum(r["has_abstract"] for r in records),
    }
    graph = {"metadata": metadata, "nodes": nodes, "edges": edges}
    index = {
        "metadata": metadata,
        "records": [{k: v for k, v in r.items() if k != "has_abstract"} for r in records],
    }
    summary = {
        "metadata": metadata,
        "themes": dict(collections.Counter(t for r in records for t in r["tags"]).most_common()),
        "diseases": dict(collections.Counter(t for r in records for t in r["diseases"]).most_common()),
    }
    return graph, index, summary



def attach_reviewed_claims(graph, claims_payload):
    """Add manually checked author-claim nodes to the keyword graph."""
    record_ids = {n.get("url"): n["id"] for n in graph["nodes"]
                  if n.get("type") == "presentation" and n.get("url")}
    known_nodes = {n["id"] for n in graph["nodes"]}
    topic_ids = {n["id"] for n in graph["nodes"] if n.get("type") in ("topic", "theme")}
    applied = 0
    for c in claims_payload.get("claims", []):
        url = c.get("source_url")
        if not url or not ISPOR_HOST.match(url):
            continue
        pid = record_ids.get(url)
        if pid is None:
            pid = "presentation:verified:" + re.sub(r"[^a-zA-Z0-9_-]", "_", c["presentation_code"])
            if pid not in known_nodes:
                graph["nodes"].append({"id": pid, "type": "presentation",
                    "label": "Verified ISPOR " + c["presentation_code"],
                    "url": url, "abstract_code": c["presentation_code"],
                    "provenance": "Manually checked official ISPOR page"})
                known_nodes.add(pid)
            record_ids[url] = pid
        cid = "claim:" + c["id"]
        graph["nodes"].append({"id": cid, "type": "reported_claim",
            "label": c["claim"], "claim_type": c["type"],
            "qualifier": c["qualifier"], "source_section": c["source_section"],
            "source_url": url, "reviewed_on": claims_payload["metadata"]["reviewed_on"]})
        graph["edges"].append({"source": pid, "target": cid,
            "relation": "REPORTS",
            "provenance": "Author-reported abstract finding, manually checked, not independently validated"})
        tid = "topic:" + c["topic"]
        if tid in topic_ids:
            graph["edges"].append({"source": cid, "target": tid,
                "relation": "ABOUT", "provenance": "Manual claim-topic classification"})
        applied += 1
    graph["metadata"]["reviewed_claims"] = applied
    graph["metadata"]["claim_scope"] = "Author-reported findings; no independent validation"
    return graph

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="HTTP(S) JSON URL or local JSON file")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parents[1] / "data"))
    parser.add_argument("--allow-small", action="store_true", help="Only for unit tests, never for publishing.")
    args = parser.parse_args()
    if args.source.startswith(("https://", "http://")):
        request = urllib.request.Request(args.source, headers={"User-Agent": "ISPOR-Research-Atlas/1.0"})
        with urllib.request.urlopen(request, timeout=80) as res:
            raw = json.load(res)
    else:
        with open(args.source, "r", encoding="utf-8") as f:
            raw = json.load(f)
    records, input_rows = build(raw, allow_small=args.allow_small)
    graph, index, summary = outputs(records, input_rows, args.source)
    claim_path = Path(__file__).resolve().parents[1] / "data" / "reviewed-claims.json"
    if claim_path.exists():
        claims_payload = json.loads(claim_path.read_text(encoding="utf-8"))
        attach_reviewed_claims(graph, claims_payload)
    path = Path(args.output_dir)
    path.mkdir(parents=True, exist_ok=True)
    for name, payload in [
        ("knowledge-graph.json", graph),
        ("records-index.json", index),
        ("summary.json", summary),
    ]:
        (path / name).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"Wrote {path / name} ({len(payload.get('nodes', payload.get('records', [])))} entries)")
    print(json.dumps(summary["metadata"], indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Build failed without overwriting published data: " + str(exc), file=sys.stderr)
        raise
