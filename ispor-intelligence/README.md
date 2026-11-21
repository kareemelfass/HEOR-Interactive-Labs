# ISPOR Europe 2026 Research Atlas

**Dashboard:** https://kareemelfass.github.io/HEOR-Interactive-Labs/ispor-intelligence/

## Primary-source policy

The main dashboard uses **ISPOR's own configured public search-index service**, accessed from its [presentations database](https://www.ispor.org/heor-resources/presentations-database/results). The independent August 2026 abstract archive is not used as the dashboard's primary source or silently substituted.

This is a **search-index capture**, not certification of the final conference universe. The public search index changed its count during collection, and a separate ISPOR facet displayed a different count. Consequently, **no final-conference denominator is claimed**.

The captured ISPOR metadata comprise UIDs, presentation codes where provided, titles, URLs, raw authors/affiliations, topic groups and subtopic paths, disease categories, session labels, publication dates, citable flags, and available indexed media links. **Full abstract bodies are not republished.** Text hashes preserve a source identity check.

## Captured record status

A verified workflow captured **2,917 distinct items across two scans**, including **2,778 citable presentation records** and **139 conference-session records**. This is a *union*, not a complete, stable point-in-time census. The official index reported fluctuating totals during collection.

The old August 24 independent archive has **3,097 records**. It is used only for the comparison and discrepancy register.

## Published data

| File | Meaning |
| --- | --- |
| data/official-index-records.json | Direct ISPOR search-index metadata, with provenance |
| data/official-index-graph.json | Literal topic, category-path, disease and session links |
| data/official-index-summary.json | Indexed record counts, types and limitations |
| data/official-reconciliation.json | Row-by-row comparison with the independent archive, including all unmatched items |
| data/reviewed-claims.json | Ten author-reported results from selected abstracts, not independent replication |
| data/knowledge-gaps.json | Thirty-two analyst-proposed future directions, not measured conference-wide knowledge gaps |
| data/records-index.json | Historical independent-archive extract, not the dashboard's source |
| data/source-records.json | Source-faithful independent-archive metadata for reproducibility, not a primary source |

## What the KG can establish

The official search-index graph contains **literal, directly sourced fields**: topic classification, topic/subtopic classification, disease categorisation, and session classification. It does not infer method usage, clinical findings, sponsorship, author identity, superiority, causality, or methodological evidence gaps. Every edge contains its source record UID and field name.

The knowledge-gap section is a proposed research agenda with explicit labels. It is not represented as evidence that all 32 gaps were found in the conference.

## Outstanding verification limitations

1. **Census mismatch:** the official index changed while it was being queried; its result counts also differ from a publicly rendered ISPOR conference filter and from the historical independent archive.
2. **Broken individual pages:** the URLs originate from ISPOR's configured index, but not every target page has been individually checked. The pilot archive verification included two 404 links.
3. **Source differences:** changed URLs, code/title mismatches and unmatched records are retained, not silently dropped or guessed.
4. **Abstract text:** full copyrighted abstracts remain on ISPOR, so the local dashboard searches title, authors, classifications and other metadata, not complete methods or results text.
5. **Interpretation:** the index does not establish audience discussion intensity or year-on-year trends.

## Rebuild and audit

The official-index pipeline is in scripts/sync_official_index.py and runs using the GitHub Actions workflow .github/workflows/ispor-official-sync.yml. The official source and historical archive are independently recorded. Invalid or contradictory sources remain in a discrepancy register.

The dashboard is static HTML, CSS and JavaScript published through GitHub Pages. No live API key is required.

**Defensible claim:** the project reproduces metadata returned by ISPOR's own public search service and records discrepancies transparently. It does not claim an independently certified final-conference census or a full manuscript-level systematic review of every presentation.
