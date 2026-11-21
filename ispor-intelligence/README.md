# ISPOR Europe 2026 Research Atlas

**Dashboard:** https://kareemelfass.github.io/HEOR-Interactive-Labs/ispor-intelligence/

## Primary-source policy

The main dashboard displays **individual research presentations, excluding conference sessions, from ISPOR's own configured public search-index service**, accessed from its [presentations database](https://www.ispor.org/heor-resources/presentations-database/results). The independent abstract archive, whose collection date is unverified, is not used as the dashboard's primary source or silently substituted.

This is a **search-index capture**, not certification of the final conference universe. The 2,778-presentation headline is a lower bound on *presentations documented by these sources at their respective check times*: 30 further official presentation pages matched code/title during the initial check but were not captured in the index. They are not proof of current availability or a point-in-time final census. The public search index changed its count during collection, and a separate ISPOR facet displayed a different count. Consequently, **no final-conference denominator is claimed**.

The captured ISPOR metadata comprise UIDs, presentation codes where provided, titles, URLs, raw authors/affiliations, topic groups and subtopic paths, disease categories, session labels, publication dates, citable flags, and available indexed media links. **Full abstract bodies are not republished.** Text hashes preserve a source identity check.

## Individual official-page reconciliation

One contemporaneous audit of 374 non-identical archived URLs recorded **46 title/code matches**, **13 reachable pages with old-title differences**, and **315 HTTP 404 responses from archived URLs**. These were single-time observations, not reproducible evidence that 315 presentations are missing. Independent rechecks of a small sample later reached matching official pages. [The original response ledger](data/official-page-checks.json) remains unchanged; the 315 must be treated as **unconfirmed historical HTTP observations** until repeat checks establish their current availability.

Among 333 archive-only candidates, **30 had matching code/title on an official page during the first check** and are preserved in the [separate source-linked supplement](data/official-page-verified-supplement.json), without entering the indexed denominator. A later independent recheck found additional old links live, so the supplement is **not an exhaustive list of missing indexed presentations**.

## Captured record status

An earlier workflow captured **2,917 distinct search-index items across two scans**, including **2,778 citable research presentation records** (the dashboard's denominator) and **139 conference-session records** (excluded from descriptive charts and record browsing). This is a *union*, not a complete, stable point-in-time census. The official index reported fluctuating totals during collection.

The independent pre-conference archive has **3,097 records** with an **unverified collection date**. It is used only for historical comparisons. Its contents must not establish a definitive conference denominator.

## Published data

| File | Meaning |
| --- | --- |
| data/official-index-records.json | Direct ISPOR search-index metadata, with provenance |
| data/official-index-graph.json | Literal topic, category-path, disease and session links |
| data/official-index-summary.json | Indexed record counts, types and limitations |
| data/official-reconciliation.json | Row-by-row comparison with the independent archive, including all unmatched items |
| data/reviewed-claims.json | Ten author-reported statements from five abstracts (seven results, one limitation, one conclusion, one recommendation), not independent replication |
| data/knowledge-gaps.json | Thirty-two unverified editorial hypotheses organised under 16 legacy keyword-theme names, not official topic groups or systematic evidence gaps |
| data/records-index.json | Historical independent-archive extract with deprecated, partly circular keyword classifications; not the dashboard's source |
| data/source-records.json | Source-faithful independent-archive metadata for reproducibility, not a primary source |

## What the KG can establish

The official search-index graph contains **literal, directly sourced fields**: topic classification, topic/subtopic classification, disease categorisation, and session classification. It does not infer method usage, clinical findings, sponsorship, author identity, superiority, causality, or methodological evidence gaps. Every edge contains its source record UID and field name.

The **Proposed research questions** section is an editorial research agenda, not a systematic review or a list of gaps demonstrated by the conference. The 16 themes are inherited editorial labels, **not** the official 12 topic groups. Linked author-reported statements serve as context only.

## Outstanding verification limitations

1. **Census mismatch:** the official index changed while it was being queried; its result counts also differ from a publicly rendered ISPOR conference filter and from the historical independent archive.
2. **Direct-page uncertainty:** the 315 archived-URL HTTP 404 responses are historical observations, not proof of nonexistent or withdrawn abstracts. Independent later tests reached some of those pages. All individual indexed presentation URLs still require checking before calling the entire corpus page-verified.
3. **Source differences:** changed URLs, code/title mismatches and unmatched records are retained, not silently dropped or guessed.
4. **Abstract text:** full copyrighted abstracts remain on ISPOR, so the local dashboard searches title, authors, classifications and other metadata, not complete methods or results text.
5. **Interpretation:** the index does not establish audience discussion intensity or year-on-year trends.

## Rebuild and audit

The official-index pipeline is in scripts/sync_official_index.py and may be manually refreshed through .github/workflows/ispor-official-sync.yml. Future runs preserve per-scan UID membership, page timestamps and response hashes (not full copyrighted abstract text). The original November 21 union **cannot** be retrospectively reconstructed at per-scan level. The official source and historical archive are independently recorded. Source refreshes are manual and serialised to avoid mixed snapshots; GitHub Pages deployment is gated on the unified official-source validation workflow.

The dashboard is static HTML, CSS and JavaScript published through GitHub Pages. No live API key is required.

**Defensible claim:** the project reproduces metadata returned by ISPOR's own public search service and records discrepancies transparently. It does not claim an independently certified final-conference census or a full manuscript-level systematic review of every presentation.
