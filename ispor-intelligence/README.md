# ISPOR Europe 2026 Research Atlas

**Dashboard:** https://kareemelfass.github.io/HEOR-Interactive-Labs/ispor-intelligence/

## Primary-source policy

The main dashboard displays **individual research presentations, excluding conference sessions, from ISPOR's own configured public search-index service**, accessed from its [presentations database](https://www.ispor.org/heor-resources/presentations-database/results). The independent abstract archive, whose collection date is unverified, is not used as the dashboard's primary source or silently substituted.

This is a **search-index capture**, not certification of the final conference universe. The 2,778-presentation index is not a final census. At the first historical check, 30 further official pages matched code and title outside that index. Thus **2,808 distinct presentations were documented across those two historical observations**. This is not a point-in-time count of currently reachable pages. After a transport-controlled recheck, the dashboard derives a new documented floor from the **latest matched outside-index pages only**, while retaining the first-check 30 as history. The public search index changed its count during collection, and a separate ISPOR facet displayed a different count. Consequently, **no final-conference denominator is claimed**.

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
| data/official-index-scan-manifest.json | Generated on the next sync, with per-scan UID membership and source-page fingerprints |
| data/official-page-recheck-latest.json | Generated on the next manual refresh, timestamped repeat archived-URL observations |
| data/official-page-verified-supplement.json | First-check title/code matches outside the current indexed set; not current live-page certification |
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

The recommended source refresh is the manually dispatched **.github/workflows/ispor-refresh-pipeline.yml**. It runs index sync, typed-graph repair, a ten-URL transport-control check, archived-URL recheck with a 55-minute time budget, supplement rebuilding, integrity and behavioural tests, **both** browser smoke checks before commit, an audit-artifact upload, and one atomic data commit in that order. It explicitly dispatches the UI-validation workflow after the generated commit because GitHub does not normally run downstream push workflows for a push made with the workflow token. The four older individual writer workflows are now **read-only, artifact-only audits**. They do not push to main or dispatch deployment, so they cannot publish a mixed snapshot.

The index sync preserves per-scan UID membership, timestamps and response hashes (not full copyrighted abstract text). The original November 21 union **cannot** be retrospectively reconstructed at per-scan level. The recheck script samples ten stable `url_match` ISPOR page controls before inspecting discrepant archived URLs. If even one control fails, the run aborts before publication; this is a conservative transport check, not proof of the validity of other HTTP 404s. Short within-run retries record repeated observations. A cross-run status is assigned only when 404 responses persist across *separate, control-validated runs at least one hour apart*. Unattempted URLs after the time budget are explicitly classified `not_checked_run_time_budget`. Even this is not proof of withdrawal or non-existence. The historical page-response ledger stays intact and the latest recheck appears separately after the first manual refresh.

All pushes on main invoke a fast shared-site check; the expensive ISPOR browser and graph checks run only when ISPOR code, data or workflows change (or on explicit dispatch). GitHub Pages deployment remains gated on a successful main validation run.

The dashboard is static HTML, CSS and JavaScript published through GitHub Pages. No live API key is required.

**Defensible claim:** the project reproduces metadata returned by ISPOR's own public search service and records discrepancies transparently. It does not claim an independently certified final-conference census or a full manuscript-level systematic review of every presentation.


## Remaining audit limitations (21 November 2026)

The third-party archive's raw SHA-256 is **not yet pinned**. We will not invent a digest; pin and verify the downloaded bytes before considering the reconciliation independently reproducible. No controlled page recheck has run yet, and the ten transport controls cannot exclude selective or geographic filtering of responses. A real ISPOR page fixture for body-fallback parsing remains to be captured and checked. The unified pipeline's direct push depends on repository branch-protection and Actions-token permissions; both must be verified on its first actual run. The draft PR does not alter the live dashboard.
