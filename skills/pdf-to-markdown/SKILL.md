---
name: pdf-to-markdown
description: Convert technical PDFs into a faithful, section-linked Markdown corpus. Use for reusable document ingestion, not ordinary PDF reading or summarization.
---
# PDF to Markdown

Produce the requested Markdown artifact with traceable source pages, preserved technical
content, and verified coverage. A simple document may need one file. A large standard or
collection benefits from indexed section files. Do not create a corpus for a request
that only asks to read or summarize a PDF.

## Choose the required detail

Run `scripts/pdf_probe.py` using its absolute path from this skill's directory to inspect
page count, text coverage, outline, and available tools. Use only dependencies needed for
the chosen path. Prefer an isolated Python environment for missing packages; requirements
are in `requirements.txt`. Source corruption or unavailable source content blocks the
affected conversion, not independent accessible documents.

Read [references/fidelity-rules.md](references/fidelity-rules.md) for transcription rules.
Then load only the references required by the output:

- For a multi-section corpus, read [references/architecture.md](references/architecture.md)
  and [references/output-conventions.md](references/output-conventions.md).
- For huge documents, overlapping page windows, or collections, also read
  [references/scaling.md](references/scaling.md).
- For original diagram images alongside transcription, read
  [references/figures.md](references/figures.md).

## Execute with available tools

Use text extraction for simple born-digital pages and rendered page inspection for scans,
tables, formulas, and diagrams whose meaning depends on layout. Use actual host tools for
rendering and viewing; do not assume a tool named Read or a fixed PDF page limit.

Process bounded sections directly or with available, authorized native delegation when
independent fragments justify it. Choose concurrency from current host capacity. Preserve
the session's model and effort unless an authorized configuration says otherwise.

Only when a compatible Claude Workflow tool is available and useful, read
[references/claude-workflow.md](references/claude-workflow.md) for the bundled adapters.
Missing Workflow support is not a blocker. Keep the conversion and verification contracts
regardless of execution host.

## Fidelity and completion

Preserve wording, clause identifiers, codes, numeric ranges, formulas, and table structure.
Keep uncertain regions explicitly marked rather than guessing. Validate source-page
mapping before converting affected sections. This is an agent evidence check, not a
mandatory user review checkpoint.

Give every fragment an exact source span and one output owner. Verify source coverage,
including content above headings and across page boundaries. Page assignment alone does
not prove content fidelity. Write only within the requested output root and preserve
unrelated existing files.

For corpora, regenerate the manifest with `scripts/build_manifest.py` and run
`scripts/validate_corpus.py`; inspect coverage warnings as well as errors. Repair actual
gaps and rerun affected checks. For a simple single-file conversion, compare the output
against all source pages without manufacturing a corpus solely to run its validator.

Report artifact paths, coverage, verification, and any unresolved unreadable regions.
Do not claim complete conversion while required content remains missing.
