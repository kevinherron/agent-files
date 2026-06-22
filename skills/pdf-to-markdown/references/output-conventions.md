# Output conventions (the corpus shape)

The exact structure the corpus must take, so it is navigable by a human and loadable by an agent, and so `scripts/validate_corpus.py` and `scripts/build_manifest.py` can check and regenerate it. These are conventions, not arbitrary rules — they exist so an agent can find the one fragment it needs from the manifest or a cross-link without loading anything else.

## Directory layout — one subdirectory per source document

```
md/                          # the output root (one literal absolute path, passed to every agent)
  README.md                  # human entry point: intro + TOC + quick-lookup tables
  manifest.json              # flat JSON array, one object per fragment (machine index)
  _maps/                     # planning artifacts (NOT fragments)
    <doc>.json               # per-document map plan (one per PDF)
    _all.json                # merged: {docMeta, linkIndex, fragments}
  <doc>/                     # one subdir per source document, named by its short id
    <clause>-<slug>.md       # one fragment per clause / catalogue entry
```

Name each document subdirectory by a short, stable id (`104`, `101`, `5-4`, `modbus`, `bacnet`). Every fragment lives under `md/<doc>/`, so a cross-document link is always `../<otherdoc>/<file>.md`. For a single-PDF job you still get one `<doc>/` subdir — it keeps links and the manifest uniform and makes adding a second document later free.

## Frontmatter

YAML frontmatter delimited by `---`, as the very first bytes of every fragment (the validator checks the first line is exactly `---`).

| Field | When | Type / format |
|-------|------|---------------|
| `source` | always | the document id, matching the subdirectory (`104`, `modbus`, …) |
| `clause` | always | the section/clause number, **always quoted**: `clause: "7.3.1.1"` |
| `title` | always | the section/entry title, quoted |
| `pdf_pages` | always | source PDF page span as a quoted string `"245-246"`, or single `"195"` |
| `type_id` | catalogue/ASDU entries only | integer, e.g. `type_id: 1` |
| `mnemonic` | catalogue/ASDU entries only | bare token, e.g. `mnemonic: M_SP_NA_1` |
| `printed_pages` | when printed ≠ pdf numbering matters (typical for scanned docs) | quoted string |

```yaml
---
source: 104
clause: "8.1"
title: "TYPE IDENT 58: C_SC_TA_1 Single command with time tag CP56Time2a"
pdf_pages: "181-182"
type_id: 58
mnemonic: C_SC_TA_1
---
```

Normalize, don't reproduce inconsistency: keep `source` a bare value, always quote `clause`/`title`/`pdf_pages`, and validate that `source` is one of the known document ids (the original corpus contained a stray `source: 99` typo — catch it).

## File naming

`<clause>-<slug>.md`, lowercase, hyphenated slug; the dotted clause number is preserved literally (dots kept):

- Plain clause: `5.3-startstop.md`, `7.2.3-cause-of-transmission.md`, `1-scope.md`.
- **Catalogue / ASDU entry**: `<clause>-t<NN>-<mnemonic>.md`, where `NN` is the type id **zero-padded to 2 digits** when ≤ 99 (`t01`…`t40`) and raw when ≥ 100 (`t100`, `t127`), mnemonic lowercased with underscores kept: `7.3.1-t01-m_sp_na_1.md`, `8.9-t127-f_sc_nb_1.md`.
- **Split files** (over the line budget): the clause with `a/b/c` suffixes before `.md`: `7.2.6a-information-elements.md`, `7.2.6b-…md`, … `7.4.11a–d`.
- Annexes / overviews: `annex-a-ft12-sync-stability.md`, `6-basic-application-functions-intro.md`.

Zero-padding and a leading ordinal where there are no clean clause numbers (`bacnet/0137-who-is.md`) keep files sorting in document order.

## Splitting rules

1. **One fragment per second-level section** (e.g. `X.Y`) by default.
2. **One fragment per atomic catalogue entry.** A type/object/function catalogue (an ASDU table, an object-type list, an opcode table) gets one file *per entry*, not one file for the whole catalogue — this is what makes the corpus loadable by the unit a reader actually wants.
3. **~600-line cap.** If a fragment's Markdown would exceed ~600 lines, split it into `a/b/c` sibling files and return *all* of them in `files_written`. Plan the split at map time (via `est_lines`); enforce it post-hoc — `validate_corpus.py` flags any file over the budget.

## Body conventions

Full detail in `references/fidelity-rules.md`; in brief: H1 title line after the frontmatter; an optional italic provenance line (`*101 §7.3.1, Fig. 22*`); GFM tables for all tabular/wire-format data; fenced blocks for formal `:=` definitions; figure headings that keep the figure number; `[ ]`/`[X]` for checklist boxes; `> [unreadable …]` blockquotes for low-confidence scans.

## manifest.json

A **flat JSON array**, one object per fragment **file** (so a/b/c splits are separate entries), sorted by `doc` then `clause`. Regenerate it deterministically with `scripts/build_manifest.py` from the on-disk frontmatter — never hand-write it.

| Field | Type | Notes |
|-------|------|-------|
| `doc` | string | document id |
| `clause` | string | dotted clause (catalogue entries may use a zero-padded sub-index, e.g. `"7.3.1.01"`) |
| `title` | string | full title |
| `file` | string | repo-relative path, `"101/1-scope.md"` |
| `pdf_pages` | string \| null | `"245-246"`, `"195"`, or `null` if unknown |

```json
[
  { "doc": "101", "clause": "1", "title": "Scope and object", "file": "101/1-scope.md", "pdf_pages": "195" },
  { "doc": "104", "clause": "8.1", "title": "TYPE IDENT 58: C_SC_TA_1 Single command with time tag CP56Time2a", "file": "104/8.1-t58-c_sc_ta_1.md", "pdf_pages": "181-182" }
]
```

## _maps/ — the planning artifacts

The map phase writes one `<doc>.json` per PDF (the `MAP_SCHEMA` plan), and `build_all_map.py` merges them into `_all.json`. These are not fragments; they live in `_maps/` and drive the convert phase.

`_all.json` shape:

```json
{
  "docMeta": {
    "104": { "pdf_file": "iec…104….pdf", "offset": 144,
             "clean": "FINAL English only (PDF 145-214, printed = PDF - 144); no French/redline in range." }
  },
  "linkIndex": {
    "byMnemonic": { "C_SC_TA_1": "104/8.1-t58-c_sc_ta_1.md" },
    "byClause":   { "104 §1": "104/1-scope.md" }
  },
  "fragments": [ /* every fragment record, tagged with doc + pdf_file */ ]
}
```

`docMeta[doc].clean` is the per-document directive handed to every convert agent (which pages, which language, which version). `linkIndex` is how convert agents author cross-links without duplicating content.

## README.md

The single human entry point. Sections in order:

1. **Intro** — a short paragraph per document and a "how the documents relate" paragraph naming the anchor document and the resolution chain between them (for a collection). For a single document, one paragraph on what it is and how the corpus is organized.
2. **Table of contents** — one block per document, nested links to every fragment. Sections that have no dedicated file (because their entries live in a lookup table) are plain text pointing at that table.
3. **Quick-lookup tables** — the indexes that make the corpus fast to use. For a protocol spec these were:
   - **Type/object id ↔ mnemonic ↔ defining fragment** — one row per catalogue entry, sorted by id, last column a link, noting which document defines it.
   - **Code tables** (e.g. cause-of-transmission) — code ↔ name, linked to the defining fragment.
   - **Clause map per document** — a compact `Clause | Title | File` table per doc.
   - **Cross-reference maps** — e.g. "document A §7.x → document B §6.x" mapping tables, with links.

   Generalize the lookup tables to whatever the document's primary index is (opcodes, object types, registers, message types). The principle: surface the document's own master tables as linked Markdown so a reader jumps straight to the defining fragment.
