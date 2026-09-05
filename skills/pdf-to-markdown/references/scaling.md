# Scaling: huge single PDFs and collections

Large documents and collections require explicit page windows and ownership. Read this
when the source cannot be handled as a small set of bounded sections. Common problems:

1. **Clause numbers may not map to a clean fragment grid** — sections are deep, irregular, or unnumbered.
2. **One map agent cannot skim the whole document** — it can't read 1500 pages in a few calls to plan fragments.
3. **Unbounded concurrent work exceeds host capacity** and floods the coordinator's context.

Here is how to keep fidelity at that scale, and how to handle a shelf of related PDFs.

## Single huge PDF — the fan-out algorithm

### Step 0 — Probe (one cheap pass)

Run `scripts/pdf_probe.py`. You need: page count and size; a per-page text-layer-vs-scanned verdict; and the **embedded outline/bookmarks** (the probe dumps them). The outline is the key that unlocks everything — most large standards ship one, and each bookmark carries a destination page, which *is* a section→page map you don't have to reconstruct.

### Step 1 — Build the section index from structure, not clause numbers

In priority order:

- **Outline/bookmarks exist (best case).** Walk the outline. Each top- or second-level node becomes a candidate section spanning `[node.page, nextNode.page − 1]`. This replaces the human-supplied page anchors the small-document flow relied on. Use the bookmark title as the section title and source of the slug.
- **A printed TOC but no bookmarks.** Dispatch a **TOC-reader agent** that reads only the contents pages (bounded source-page reads) and returns `{title, printed_page}` rows; convert printed→PDF with the offset from `pdf_pagemap.py`.
- **Neither (worst case).** Fall back to **fixed page-window tiling**: slice the body into ~10–12-page windows. Section boundaries are recovered at convert time by the agent detecting headings within its window.

### Step 2 — Normalize sections to page-range windows (the map output)

Emit the same `MAP_SCHEMA` fragment records, but produced from the section index:

- Each fragment is a **window** of `pdf_pages` small enough for the available reader and context. Start around 10–15 pages and reduce the window for dense scans or tables. Read the actual host limits rather than assuming a universal page cap.
- If one bookmarked section spans more than ~30 pages, or its `est_lines` would exceed ~600, **sub-tile** it into `…a/b/c` windows at map time.
- Derive `target_file` from a slugified heading plus a **zero-padded ordinal** (`bacnet/0137-who-is.md`) so files sort in document order even without clause numbers.
- Carry a `parent_section` field so windows of the same logical section can be stitched later.

`scripts/plan_from_outline.py` implements Steps 1–2 for the outline case: it reads the probe JSON, makes one window per top/second-level section (sub-tiling any section longer than `--window` pages with a 1-page overlap), writes `_maps/<doc>.json`, and reports page-coverage over the body. On the 1532-page ASHRAE 135-2024 BACnet spec it produced **927 windows covering 100% of the 1519 body pages with zero gaps** — including the lettered annexes (Annex A–Z) a naive numeric parser would drop. Lettered/`Annex X` section numbers are parsed, so coverage is honest end-to-end.

### Step 3 — Convert, one agent per window (batched — see below)

Same convert contract as the base flow: read your `pdf_pages`, confirm you're on the right heading (search ±3 pages if off), write one fragment, return metadata.

### Step 4 — Stitch

Concatenate windows belonging to the same `parent_section` in page order; dedup the overlap (below); regenerate the manifest (`build_manifest.py`) and the README TOC from the section tree.

Concretely for a 1500-page spec: outline → ~150–400 sections → normalize to ~150–500 windows of ≤12 pages → batched-pipeline convert → stitch by parent.

## Concurrency — batch, never one giant barrier

Choose a bounded worker count from the host's available capacity, including any slots
used by the coordinator. Queue remaining fragments and persist results as each batch
finishes. When delegation is unavailable or adds no value, process the same windows
sequentially. The optional Claude adapter in references/claude-workflow.md describes
its Workflow templates; do not assume those primitives or model controls exist elsewhere.

## Boundary handling — own every page exactly once

A page-window must transcribe **every** line in its range, and each page's content must be transcribed by **exactly one** window — no drop, no duplication. The trap (caught on BACnet `13.3.8`): two sections share a page — the tail of section N (its last condition, a transition figure, a notification table) sits *above* the heading of section N+1. If each window is merely told to "start at its first heading," that tail is dropped by *both* windows — and page-coverage still reports the page as covered, so nothing flags it.

Two mechanisms, used together:

1. **Cut windows at child-section boundaries, not arbitrary page counts.** `scripts/plan_from_outline.py` ends each window at the page before the next child section begins, so a long section is never split at a no-heading page (a single child larger than the window is page-tiled as a fallback). Each windowed fragment carries `prev_end` — the previous window's last page — for the ownership rule below.
2. **Own pages by a precise rule in the convert prompt.** Pass each window its `prev_end` and instruct: *Read your full range, but page `prev_end` is context only — do not re-transcribe it (the previous window owns it). Begin new transcription at `prev_end + 1`, top to bottom, including any content above the first heading (it is the tail of a section continued from the previous window — emit it under a `> _(continued from previous window: …)_` note). If a section runs past your last page, transcribe what is on your pages and set `continues: true`.* This captures the shared-page tail (no drop) without re-emitting the overlap page (no duplication). Verified on BACnet: with this rule, window 2 of `13.3` correctly leads with `13.3.8`'s carried-over condition (m), its transition figure, and its notification-parameters table — content that "start at the first heading" silently dropped.

A wide table that visually straddles a page boundary is the residual case: each window transcribes its portion and notes "table continues"; the verification pass joins the portions against the source. Rare, and far less costly than a silent drop.

## Keeping accuracy high at scale

- **Page-coverage reconciliation is the load-bearing check.** After convert, prove every body page is covered: the union of all fragments' `pdf_pages` must equal `[bodyStart..bodyEnd]` with no gaps (overlaps expected). `scripts/validate_corpus.py --coverage` does this from the manifest/maps. **A gap means a dropped window → re-dispatch it.** This is what catches silent truncation of a long document — the failure mode that's invisible from reading the output. **Caveat:** coverage proves every page is *assigned* to a window, not that every page's *content* was emitted — content can be dropped *within* an assigned page (see Boundary handling), and an alternating-language scan legitimately leaves pages uncovered. So `validate_corpus.py` treats coverage as a **warning**, not a hard failure: a genuinely dropped *fragment* is caught hard by manifest↔disk reconcile, and content dropped within a covered page is caught by the page-ownership rule plus the adversarial verify pass.
- **Trust returns, verify on disk.** `status: ok` is not proof of a written file. Manifest↔disk reconcile (also in `validate_corpus.py`) caught four fragments that were reported converted but never written.
- **Verify a stratified sample, not everything.** A few per `kind`, a few per region, **boosted on the densest table/figure windows** and a random tail. At 1500 pages an exhaustive adversarial re-read isn't worth it; a good sample plus the deterministic gates is.
- **Internal-link integrity sweep and 600-line re-check** after assemble, as in the base flow.

## Collections of PDFs

- **One map per document**, processed directly or with bounded authorized delegation. Each produces `_maps/<doc>.json` with its own offset, target region, and fragments.
- **Merge into a shared index.** `scripts/build_all_map.py` builds `_all.json = {docMeta, linkIndex, fragments}` where `fragments` is the flat union tagged with `doc`, `docMeta[doc]` holds `{pdf_file, offset, clean}`, and `linkIndex` maps shared identifiers (mnemonics, named clauses) to files across the whole collection. Every convert agent receives the whole `linkIndex`, so any fragment can link to any other.
- **Namespace by document** (`md/<doc>/…`) so slugs don't collide across documents and every cross-link resolves with a single `../`.
- **Link, don't duplicate, across documents.** Where document A references a definition in document B, link `../<docB>/<file>` rather than re-converting B's content. Pick an **anchor document** for the README intro that explains how the documents relate (the original used 104 as the network-access anchor that selects 101's ASDUs and maps to 5-5's functions).
- **Run the deterministic gates per document** — each has its own body span and offset, so page-coverage reconciliation is per-doc; link integrity and manifest↔disk run across the whole tree.
