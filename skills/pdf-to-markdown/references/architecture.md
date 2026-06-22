# Architecture: the map → convert → verify → assemble Workflow

This is the proven orchestration for converting a spec-grade PDF into a faithful Markdown corpus. It was validated converting four IEC 60870-5 standards (≈1070 source pages) into 169 per-clause fragments with zero broken links and a verified manifest. Read it before you orchestrate; adapt `assets/workflow-template.js` rather than reinventing the control flow.

## Why a multi-agent Workflow at all

One agent cannot faithfully convert a large PDF in one pass. It runs out of context, averages tables together, and silently drops the back half — and you won't notice, because the output *looks* complete. Fidelity at scale requires:

- **Decomposition** — one small, self-contained unit of work per agent (a clause, an ASDU, a page-range window), each with an exact page range so it never has to hunt.
- **Isolation** — an agent that mangles one fragment doesn't corrupt the others; each owns one output file.
- **Independent verification** — a second agent re-reads the source and tries to find the error, instead of the author grading its own work.
- **Deterministic gates** — code, not an LLM, proves the corpus is complete (every page covered, every file on disk, every link resolves).

The Workflow tool (ultracode) gives you the fan-out primitives (`parallel`, `pipeline`), per-agent effort/schema control, and progress tracking. Use it.

## The shape

```
[probe + decide output root]                         ← scripts/pdf_probe.py
        │
   ┌────▼─────────────────────────────────────────┐
   │ PHASE 1 — MAP  (cheap, planner-only)          │  parallel(): 1 agent per PDF
   │   each agent → md/_maps/<doc>.json            │  effort: high
   └────┬─────────────────────────────────────────┘
        │
[REVIEW GATE — programmatic offset validation + merge]   ← pdf_pagemap.py, build_all_map.py
        │   md/_maps/_all.json = {docMeta, linkIndex, fragments}
        │
   ┌────▼─────────────────────────────────────────┐
   │ PHASE 2 — CONVERT  (expensive)                │  batched pipeline(): 1 agent per fragment
   │   each agent → md/<doc>/<target_file>         │  effort: effortFor(fragment)
   └────┬─────────────────────────────────────────┘
        │
   ┌────▼─────────────────────────────────────────┐
   │ PHASE 3 — VERIFY  (adversarial + reconvert)   │  pipeline() over a stratified sample
   │   verify → if real fidelity loss → reconvert  │  + deterministic validate_corpus.py
   └────┬─────────────────────────────────────────┘
        │
   ┌────▼─────────────────────────────────────────┐
   │ PHASE 4 — ASSEMBLE  (after verify)            │  build_manifest.py + 1 agent for README
   │   manifest.json + README.md                   │
   └───────────────────────────────────────────────┘
```

Two phases, run as two Workflows (or one with the gate inlined), with a human/orchestrator review gate between them. **Map is cheap planning; convert is the expensive production fan-out.** Splitting them lets you validate the page offsets — the one thing that, if wrong, ruins everything downstream — before you spend the convert budget. In the original run this was literally two `Workflow` invocations with a `python3` reconciliation step in the main thread between them.

## Phase 1 — Map (plan, don't convert)

One agent per PDF, fanned out with `parallel()` (a handful of docs — no batching needed). Each agent is a **planner**: it reads only enough pages to understand the structure and emit a JSON plan. It writes **no fragment content**.

What each map agent must resolve and return (see `MAP_SCHEMA` below):

- `clean_english_pdf_range` / the target region — for a bundle of redline+clean or multiple languages, which PDF pages are the ones to convert.
- `printed_to_pdf_offset` — the formula `printed = pdf − N`, valid within the clean region. **Resolve this programmatically for text-layer PDFs** (see the review gate); have the agent confirm by reading, not derive by eyeballing images.
- `fragments[]` — one record per output file, each carrying the **exact** `pdf_pages`, a `target_file` (relative to the output root), a `kind`, `figures`, `est_lines`, `cross_refs`, and (for catalogue entries) `type_ids`.

Granularity rule (encode in the map prompt): one fragment per second-level section by default; one fragment per **atomic catalogue entry** (e.g. one ASDU / Type ID per file); plan a split for anything projected over ~600 lines. `references/output-conventions.md` has the full rule and naming.

## The review gate (between map and convert)

This is where the original run prevented disaster, and where a naive single-Workflow version fails. Before the convert fan-out:

1. **Validate the offset programmatically.** For text-layer PDFs, run `scripts/pdf_pagemap.py`. It classifies every page (language, redline-vs-final, printed page number from the running header) and derives the offset. Image-header reading mis-attributes pages whenever a document repeats the same printed numbers across redline/clean or language blocks — and produces a confident, wrong offset.
2. **Confirm the offset is constant** at ≥3 anchors spanning the body — front matter, a middle table/figure, a back annex. A drift between anchors means there's an extra cover page or a second numbering region; capture both offsets in `docMeta`.
3. **Merge** the per-doc plans into `_all.json` with `scripts/build_all_map.py`. This produces `{docMeta, linkIndex, fragments}` — the single handoff artifact the convert phase loads. `docMeta[doc]` holds the per-document `pdf_file`, `offset`, and a `clean` directive string; `linkIndex` maps mnemonics and `"<doc> §<clause>"` keys to target files so convert agents link instead of duplicate.

Treat the map as untrusted until the offset is proven. Everything else is cheap to redo; a wrong offset is silent, corpus-wide corruption.

## Phase 2 — Convert (fan out, batched)

One agent per fragment. Each receives its fragment record, `docMeta[doc]` (the clean/offset directive), the fidelity rules, and the `linkIndex`, and:

1. Reads its exact `pdf_pages` with the Read tool (which renders pages as images — essential for bit-layout figures and scanned pages). For scanned bilingual docs, transcribe only the target-language pages.
2. Self-checks it is on the right page: the running header should show `pdf − offset`; the content must be the right language and the clean (not redline) version. **If wrong, search ±3 pages** to relocate the clean section before converting.
3. Writes one fragment (or `a/b/c` split files) to `<root>/<target_file>` and returns metadata.

**Effort tiering** keeps cost proportional to difficulty:

```js
function effortFor(f) {
  if (f.scanned) return 'high'                                   // OCR from page image
  if (['asdu','coding-table','checklist','bitfield'].includes(f.kind)) return 'high'
  return 'medium'                                                // prose clauses
}
```

**Batch the fan-out.** A handful of documents in Phase 1 can be one `parallel()`. Hundreds of fragments in Phase 2 must **not** be a single `parallel()` barrier — the concurrency ceiling is ~16, and a giant barrier wastes wall-clock and floods the orchestrator's context with hundreds of simultaneous returns. Process waves of ~12–16 (a `pipeline`, or chunk and `await parallel(batch)` in a loop). `references/scaling.md` covers this for large jobs. Each agent owns a unique `target_file`, so no worktree isolation is needed.

## Phase 3 — Verify (adversarial sample + deterministic whole-corpus)

A small adversarial sample is necessary but **not sufficient** — it will miss a whole fragment that never got written and links that dangle. Run both:

- **Adversarial sample** (`pipeline`): pick a stratified sample — a few per `kind`, a few per document/region, and weight it toward the densest table/figure fragments. Each verifier agent re-reads the *source pages* and the produced file and checks: every Type ID / code / field / numeric range present and correct; bit-layout rendered as a field table with the right figure number; tables and checklist boxes complete; no OCR garble, wrong-language, redline, or hallucinated content; frontmatter present. Verdict policy: **a named wrong number, code, or exponent is a real failure → reconvert**; purely cosmetic wording is a note. The reconvert stage reuses the convert prompt with the specific problems appended ("the prior version FAILED verification; fix these:") and runs inline in the same pipeline.
- **Deterministic** (`scripts/validate_corpus.py`): manifest↔disk reconcile, broken internal-link check, oversize-fragment check, frontmatter check, page-coverage reconcile. These are the gates the LLM verifier can't provide. Any failure is a concrete gap — re-dispatch that fragment or fix the link.

Verify runs **before** assemble so the manifest and README reflect repaired files.

## Phase 4 — Assemble (after verify)

Regenerate `manifest.json` deterministically from the on-disk frontmatter with `scripts/build_manifest.py` — do not let an agent hand-write the manifest (it will drift from the files). Then one agent writes `README.md`: the intro, a full linked table of contents, and the quick-lookup tables (`references/output-conventions.md` specifies them). The assemble agent may read a couple of authoritative fragments to build a master code/type table.

## The agent return schemas

These force complete, machine-usable returns. They live in `assets/workflow-template.js` as JS objects; reproduced here as the contract.

**MAP_SCHEMA** (per-document plan):

```json
{
  "type": "object", "additionalProperties": true,
  "required": ["doc", "total_pdf_pages", "target_pdf_range", "printed_to_pdf_offset", "fragments"],
  "properties": {
    "doc": {"type": "string"},
    "pdf_file": {"type": "string"},
    "total_pdf_pages": {"type": "number"},
    "language_layout": {"type": "string", "description": "how languages are arranged, if multilingual"},
    "version_split": {"type": "string", "description": "how redline vs clean/consolidated are arranged, if bundled"},
    "printed_to_pdf_offset": {"type": "string", "description": "formula: printed = pdf - N, within the target region"},
    "target_pdf_range": {"type": "array", "items": {"type": "number"}, "description": "[start, end] PDF pages of the body to convert"},
    "structure_notes": {"type": "string"},
    "fragments": {
      "type": "array",
      "items": {
        "type": "object", "additionalProperties": true,
        "required": ["clause", "title", "pdf_pages", "target_file", "kind"],
        "properties": {
          "clause": {"type": "string"},
          "title": {"type": "string"},
          "printed_pages": {"type": "string"},
          "pdf_pages": {"type": "string", "description": "EXACT pdf page range to read, e.g. \"232-235\""},
          "target_file": {"type": "string", "description": "path relative to the output root, e.g. \"104/5.3-startstop.md\""},
          "kind": {"type": "string", "enum": ["clause","asdu","checklist","coding-table","bitfield","procedure","overview"]},
          "scanned": {"type": "boolean", "description": "true if these pages have no text layer (OCR from image)"},
          "type_ids": {"type": "array", "items": {"type": "object", "additionalProperties": true}},
          "figures": {"type": "array", "items": {"type": "string"}},
          "est_lines": {"type": "number"},
          "cross_refs": {"type": "array", "items": {"type": "string"}},
          "notes": {"type": "string"}
        }
      }
    }
  }
}
```

**CONVERT_SCHEMA** (per-fragment result):

```json
{
  "type": "object", "additionalProperties": true,
  "required": ["target_file", "files_written", "status"],
  "properties": {
    "target_file": {"type": "string"},
    "files_written": {"type": "array", "items": {"type": "string"}, "description": "every file actually written (incl. a/b/c splits)"},
    "doc": {"type": "string"}, "clause": {"type": "string"}, "title": {"type": "string"}, "pdf_pages": {"type": "string"},
    "type_ids": {"type": "array", "items": {"type": "object", "additionalProperties": true}},
    "codes": {"type": "array", "items": {"type": "object", "additionalProperties": true}, "description": "any code table this fragment defines"},
    "unreadable": {"type": "array", "items": {"type": "string"}, "description": "pages/regions marked [unreadable]"},
    "status": {"type": "string", "enum": ["ok", "partial"]},
    "notes": {"type": "string"}
  }
}
```

**VERIFY_SCHEMA** (per-sample verdict):

```json
{
  "type": "object", "additionalProperties": true,
  "required": ["file", "verdict", "needs_reconvert"],
  "properties": {
    "file": {"type": "string"},
    "verdict": {"type": "string", "enum": ["ok", "minor", "fail"]},
    "problems": {"type": "array", "items": {"type": "string"}},
    "needs_reconvert": {"type": "boolean"}
  }
}
```

## Adapting the template

`assets/workflow-template.js` is the convert/verify/assemble Workflow with the schemas, `effortFor`, and the prompt builders wired up. To use it:

1. Fill in `ROOT` (the single output-root literal) and the `DOC_PROFILES` (per-doc `pdf_file`, `offset`, `clean` directive, `scanned` flag) — or load them from `_all.json` if you ran `build_all_map.py`.
2. Confirm the convert prompt embeds the contents of `references/fidelity-rules.md`.
3. Tune the verify `SAMPLE` to cover every `kind` your document has.
4. Run it through the Workflow tool. For large jobs, switch the convert `parallel()` to the batched pipeline shown in `references/scaling.md`.

Keep the map phase as a separate, earlier step — `assets/map-workflow-template.js` (its own small Workflow), inline agents, or (for a large PDF with an embedded outline) a plan built directly from the probe's outline — so the review gate stays between map and convert.
