# Corpus conversion and verification

Read this for multi-section technical corpora. The phases apply to direct execution and
authorized delegation alike. Each fragment has exact source pages and one output owner.
Large inputs need bounded page windows and durable artifacts, not necessarily multiple
agents or any particular host.

## Map the source

Probe the PDF and identify the intended language, edition, clean versus redline region,
and source page range. Prefer an embedded outline; use the contents pages or fixed windows
when needed. Use `scripts/plan_from_outline.py` for large outlined inputs. For text-layer
PDFs with repeated numbering or mixed regions, use `scripts/pdf_pagemap.py` to establish
printed-to-PDF mapping. Confirm source regions at anchors spanning the document.

Record each fragment's `pdf_pages`, `target_file`, section identity, and relevant
cross-references. Validate constant offsets only within regions where they are actually
constant; use explicit PDF page spans across numbering changes. Repair conflicting map
evidence before converting affected regions. This check does not require user approval.
For collections, `scripts/build_all_map.py` merges maps into `_all.json` with document
metadata, fragments, and a shared link index.

## Convert bounded fragments

Read the assigned source pages, including figures and table layout. Verify language,
edition, and headings before transcribing. Give each worker the absolute corpus root,
its fragment record, relevant source mapping, fidelity rules, and link index. A worker
writes only its assigned files under that root. Direct sequential processing uses the
same boundaries. Follow references/scaling.md for overlap ownership on windowed inputs.

## Verify evidence and artifacts

Compare source pages against a stratified sample spanning document regions and fragment
kinds, weighted toward dense tables, diagrams, scans, formulas, and boundaries. Correct
wrong identifiers, ranges, exponents, missing content, and wrong-source contamination.
Use independent review when available and useful; otherwise conduct a separate source
comparison pass and disclose consequential verification limits.

Generate the manifest with `scripts/build_manifest.py`, then run
`scripts/validate_corpus.py`. Inspect coverage warnings as well as errors. Assignment of
a page does not prove every line was transcribed. Reconcile intentionally excluded pages
explicitly; repair unexplained gaps. Check that reported files exist and internal links
resolve. Repeat affected validation after repairs.

## Assemble and deliver

Write the corpus README and linked contents from the final files, following
references/output-conventions.md. Regenerate the manifest and validate the final corpus
after changes to fragments, links, or figures. Report source coverage, artifacts,
verification, and unresolved low-confidence regions. Do not call partial conversion
complete merely because deterministic checks passed.
