---
name: pdf-to-markdown
description: Convert PDFs — especially technical specifications, standards, and protocol documents (IEC, BACnet, Modbus, OPC UA, RFCs, datasheets, manuals) — into a faithful, navigable Markdown corpus an LLM or agent can load by section instead of re-parsing the PDF. Use this skill whenever the user wants to convert / turn / ingest / "markdownify" / extract a PDF or a folder of PDFs into Markdown, build a spec corpus, OCR a scanned standard, or prepare PDFs so an agent can read them by clause — even if they don't say "Markdown" and just ask to "parse", "read", "extract", or "get the text out of" a PDF. It runs a multi-agent dynamic Workflow (ultracode): a cheap map/plan fan-out, a parallel per-section conversion fan-out, an adversarial verify pass, and deterministic corpus validation — built for fidelity over speed and for documents one context window cannot hold, from a 50-page spec to a 1500-page / 20 MB standard, and for collections that need cross-document links. Prefer this over a one-shot `pdftotext` dump whenever fidelity matters (tables, bit/octet figures, clause numbering, cross-references) or the output will be fed back to an LLM; for a throwaway text grab of a tiny PDF, a plain dump is fine instead.
---

# PDF to Markdown

Turn a PDF — or a shelf of related PDFs — into a Markdown corpus that an LLM or a human can actually trust. The job is **fidelity, not text extraction**. A spec whose ASDU bit-layout collapses into prose, whose Type IDs or cause-of-transmission codes drift by one, or whose clause numbers are lost, is worse than the original PDF: a downstream agent will read it confidently and be wrong. Every decision in this skill trades time and tokens for faithfulness, because the corpus is meant to be loaded thousands of times after you build it once.

This is a **parallel, multi-agent job** for anything past a few pages. A single context cannot faithfully hold a 300-page standard, let alone a 1500-page one — it will silently truncate, average tables together, and lose the back half. So the skill fans the work out: a cheap **map** phase plans exact page ranges, an expensive **convert** phase runs one agent per section, an adversarial **verify** phase re-reads the source, and **deterministic validators** prove the corpus is complete and well-formed. Drive it with the **Workflow tool** (ultracode); the proven orchestration is bundled as a template you adapt, not rebuild.

## When to use the full pipeline (and when not)

Scale the effort to the document — but bias toward the full pipeline, because under-converting a spec is the expensive failure.

- **A few pages, born-digital, no hard tables** → one pass is fine. Run `scripts/pdf_probe.py`, then `pdftotext -layout` or a single conversion agent. You do not need a Workflow for a 3-page memo.
- **A spec / standard / manual (tens to hundreds of pages), tables, figures, numbered clauses** → the full `map → convert → verify → assemble` Workflow. This is the default and the reason the skill exists.
- **A huge single PDF (1000+ pages / 10+ MB) or a collection of related PDFs** → the full pipeline plus the scaling discipline in `references/scaling.md` (windowed sections, batched fan-out, page-coverage reconciliation, shared cross-document link index).

If the file is encrypted, corrupt, or not actually a PDF, stop and tell the user — that is blocking.

## Files in this skill

Read the references as you reach the phase that needs them; you do not need all of them for a small job.

- `references/architecture.md` — the two-phase `map → convert → verify → assemble` Workflow pattern in depth: why the phases split where they do, the agent return schemas, effort tiering, and the review gate between map and convert. **Read before orchestrating.**
- `references/fidelity-rules.md` — the conversion contract: tables → GFM, bit/octet figures → field tables that keep the figure number, formal `:=` definitions → fenced blocks, checklists → tables with `[ ]`/`[X]`, sequence/state diagrams → ordered step lists, cross-references → links not duplication, the verbatim-but-flag-corrections policy, and the highest-risk OCR errors. **This is the prompt material every convert agent must receive.**
- `references/output-conventions.md` — the exact output shape: directory-per-source layout, YAML frontmatter, file-naming, the ~600-line split rule, `manifest.json`, and the `README.md` table-of-contents + quick-lookup tables.
- `references/scaling.md` — how to handle a 1500-page PDF with no clean clause numbers (probe → outline/TOC → page-range windows → batched pipeline → overlap & stitch → coverage reconciliation) and collections of PDFs. **Read before converting anything large.**
- `assets/map-workflow-template.js` — the map-phase Workflow: one planner agent per PDF emitting a JSON fragment plan with exact page ranges. Adapt for the planning phase (or, for a large PDF with an embedded outline, build the plan from the probe's outline instead).
- `assets/workflow-template.js` — the convert → verify → assemble Workflow: the schemas, `effortFor`, the fidelity-bearing convert prompt, batched fan-out, and adversarial verify with inline reconvert. Fill in the output root and run it through the Workflow tool.
- `scripts/pdf_probe.py` — triage: page count, per-page text-layer coverage, embedded outline/bookmarks, a born-digital / scanned / mixed verdict, and tool availability. **Run first.**
- `scripts/pdf_pagemap.py` — for text-layer PDFs that bundle redline+clean and/or multiple languages: classify every page (language, redline-vs-final, printed page number) and derive the printed→PDF offset and clean page range *programmatically*. Resolves the offset that image-reading gets wrong.
- `scripts/plan_from_outline.py` — for large PDFs with an embedded outline: turn the probe's outline into a full fragment plan of page-range *windows* (one per top/second-level section, oversized ones sub-tiled with a 1-page overlap) and report page-coverage over the body. The deterministic outline→windows mapping for big documents.
- `scripts/build_all_map.py` — merge per-document map plans into one `_all.json` with a `linkIndex`, so convert agents link across documents instead of duplicating.
- `scripts/build_manifest.py` — regenerate `manifest.json` deterministically from the fragments' frontmatter on disk (don't let an agent hand-write it).
- `scripts/validate_corpus.py` — the quality gate: manifest↔disk reconcile, broken internal-link check, oversize-fragment check, frontmatter check, and page-coverage reconciliation. Run after convert and again after every fix.

## Workflow

Read `references/architecture.md` first. For a large or multi-PDF job also read `references/scaling.md`. Then:

**0. Probe (triage).** Run `python3 scripts/pdf_probe.py <pdf>` on each input. It reports page count, per-page text-layer coverage, the embedded outline, and a born-digital / scanned / mixed verdict. The verdict picks the conversion path: text-layer pages are cross-checked with `pdftotext -layout`; scanned pages are read as images (the Read tool renders every PDF page to an image regardless — that is how figures and scans get "seen"). Decide the output root now and pass it everywhere as one literal absolute path.

**1. Map (plan, don't convert).** One planner agent per PDF. Each reads only enough pages (`Read` with `pages=`, ≤15 per call) to emit a JSON plan: for every fragment, the **exact** `pdf_pages` to read, a `target_file`, a `kind`, figures, estimated size, and cross-references. The agent writes no content. For a PDF that bundles redline+clean or multiple languages, do **not** eyeball page images to find the offset — run `scripts/pdf_pagemap.py` and let the page classifier resolve it. For a large PDF with a usable embedded outline, build the plan deterministically with `scripts/plan_from_outline.py` (it windows every section and reports page-coverage) rather than having one agent skim hundreds of pages. Granularity: one fragment per second-level section; one fragment per atomic catalogue entry (e.g. one ASDU/Type per file); split anything projected over ~600 lines. See `references/output-conventions.md`.

**2. Validate the map — this is the review gate, and it is blocking.** Before paying for the convert fan-out, prove the page offset is **constant** by spot-reading the assigned pages at ≥3 anchors spanning the whole body (front, a middle table/figure, a back annex). A wrong offset silently turns every fragment into redline or wrong-language garbage. Merge the per-doc plans with `scripts/build_all_map.py` into `_all.json` (`{docMeta, linkIndex, fragments}`). Only proceed once the map is trustworthy.

**3. Convert (fan out).** Run the convert Workflow from `assets/workflow-template.js`: one agent per fragment, each handed its fragment record, the document's clean/offset directive, the fidelity rules (`references/fidelity-rules.md`), and the `linkIndex`. Tier effort with `effortFor` (scanned pages and dense tables/figures → high; prose → medium). **Batch the fan-out** — process waves of ~12–16 agents (a `pipeline`), never one giant `parallel` over hundreds of fragments; the concurrency ceiling is ~16 and a single barrier wastes wall-clock and floods context. Each agent writes **only under the one output root** (never interpolate a document id into the path) and returns its metadata.

**4. Verify — adversarially *and* deterministically.** Both, because each catches what the other misses:
   - **Adversarial sample**: a `pipeline` over a stratified sample (a few per `kind`, a few per document/region) where each agent re-reads the *source pages* and checks every Type ID / code / field / range, table completeness, and the absence of OCR garble / wrong-language / redline contamination. Real fidelity loss → reconvert inline; cosmetic issues → note only. A named wrong number or code is real, not cosmetic.
   - **Deterministic**: `python3 scripts/validate_corpus.py` over the whole corpus — manifest↔disk reconcile (catches the agent that reported success but wrote nothing), broken-link check, oversize check, frontmatter check, page-coverage reconcile (catches dropped pages). Any failure is a gap to re-dispatch.

**5. Assemble (after verify).** Regenerate `manifest.json` with `scripts/build_manifest.py`, then have one agent write `README.md` — intro, full linked table of contents, and the quick-lookup tables (per `references/output-conventions.md`). Assemble runs after verify so the index reflects the final, repaired files.

**6. Reconcile and deliver.** Re-run `validate_corpus.py` until clean. Report to the user: documents and page counts, fragments produced, the conversion path per document, anything marked low-confidence or `[unreadable]`, and any pages a human should spot-check. Never delete stray output blind — verify ownership (mtime + content) and ask first.

## Scaling to huge PDFs and collections

A 1500-page PDF breaks three assumptions a small spec lets you keep: clause numbers may not map to a clean fragment grid, one map agent cannot skim the whole document, and a single parallel barrier over every section overruns the concurrency ceiling. `references/scaling.md` is the playbook; the essentials: derive the section index from the embedded **outline/bookmarks** (fall back to a TOC-reader agent, then to fixed page-window tiling); normalize sections to **page-range windows** small enough to read in ≤2 calls, sub-tiling big ones; **overlap windows by one page** and stitch on heading identity so a section straddling a boundary is captured whole; run convert as a **batched pipeline**; and make **page-coverage reconciliation** the load-bearing check — every body page must be covered by some fragment, or it was dropped. For collections, run one map per document in parallel, merge into a shared `linkIndex`, namespace the tree by document (`md/<doc>/…`), and link across documents instead of duplicating shared definitions.

## Boundaries

- **Preserve, do not improve.** Keep the document's own wording, clause numbers, codes, and table structure. Do not summarize, reorder, or paraphrase the source.
- **Verbatim, but flag corrections.** Transcribe source text as-is, including obvious typos. If you correct an evident error, leave an HTML comment marking the deviation (`<!-- source reads "UI16"; obvious typo for UI6 -->`) so it stays auditable.
- **Low confidence is a flagged result, not a silent guess.** Mark uncertain scan regions with a `> [unreadable: …]` blockquote that names exactly what is approximate *and* what is exact; surface those pages to the user.
- **Write only under one corpus root.** Every agent receives the root as a single literal path and writes beneath it. A returned path outside the root is a bug — reject or relocate it; never substitute a document id into the directory path.
- **Trust nothing self-reported.** An agent's `status: ok` is not proof a file exists. The filesystem and `validate_corpus.py` are the source of truth.

## Things that produce bad conversions

- **Deriving the page offset by reading rendered page images.** Redline/clean and multilingual bundles repeat the same printed page numbers and figure numbers across blocks; image-header reading mis-attributes pages and corrupts an entire document. Use `pdf_pagemap.py` on text-layer PDFs and confirm the offset is constant across the body.
- **Believing `files_written`.** The headline "162/162 converted, 0 failures" once hid four fragments that were reported but never landed on disk. Always reconcile against the filesystem.
- **One giant `parallel()` over every fragment.** Past ~16 concurrent agents it stalls and floods the orchestrator's context. Batch.
- **Tables flattened into run-on lines, or headings demoted to bold,** because a text-layer dump was used where layout-aware or image-based reading was needed.
- **Clause/section numbers silently renumbered or dropped,** which breaks every cross-reference that points at them.
- **Cross-references to documents outside the corpus rendered as links** (they dangle) instead of plain text; and split `a/b/c` files whose inbound links still point at the pre-split name.
- **OCR exponent and index slips** (`2^(1-i)` read as `2^(-i)`, `i-1` vs `1-i`) — the highest-risk scanned-page error; verify repeated formulae are internally consistent.
- **Silent truncation of a long document** — converting the first N pages and never noticing the tail is missing. Page-coverage reconciliation is what catches it.
