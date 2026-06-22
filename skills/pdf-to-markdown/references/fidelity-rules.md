# Fidelity rules (the conversion contract)

This is the contract every **convert** agent must follow, and what every **verify** agent checks against. Embed it (or a document-tailored version) in the convert prompt. The corpus exists to preserve exact detail; these rules are how that survives the trip through an LLM. Reasons are given so you can adapt sensibly to a document that doesn't look like a protocol spec — the principles generalize to datasheets, manuals, and standards of any kind.

## The first principle: preserve, don't improve

Convert what is on the page. Do not summarize, reorder, paraphrase, or "clean up" the source. A downstream agent will treat this corpus as ground truth; if you rewrite a sentence or normalize a table, you have invented a primary source. Preserve **exactly**: every identifier, code, mnemonic, field/bit name, qualifier, enumerated value, and numeric range. In a spec these *are* the content — a Type ID off by one or a dropped cause-of-transmission code is a silent, load-bearing error.

### Verbatim, but flag corrections

Transcribe source text as-is, **including obvious typos**. The source is authoritative even when wrong. If you encounter an evident error and choose to correct it, mark the deviation with an HTML comment so it stays auditable:

```markdown
CP56Time2c := UI6[11..16]  <!-- source reads "UI16[11..16]"; a 6-bit field cannot be UI16 — obvious typo -->
```

This keeps the corpus faithful while not propagating a known mistake unannotated. A verify agent should specifically watch for *silent* corrections and flag them.

### Do not fabricate structure

Preserving means not *adding*, either. A figure that is a diagram — a protocol stack, a network topology, a flow chart — is transcribed as a faithful labeled list (or, for a flow, an ordered step list); do **not** invent table column headers it never had. Do not synthesize "summary" or "overview" tables the source doesn't contain, and do not add cross-references beyond those in the link index. Correct-but-absent structure is still a deviation: if a reader can't find it on the page, it doesn't belong in the fragment unless you mark it with an explicit editorial HTML comment. The verify pass flags *added* structure, not only dropped content. (In testing, convert agents tended to over-help — rendering a stack diagram as a table with invented headers, or synthesizing a reserved-codes summary table — which is exactly what this rule exists to prevent.)

## Frontmatter

Open every fragment with YAML frontmatter. Core fields (full spec in `references/output-conventions.md`):

```yaml
---
source: 104                  # the document id = the subdirectory name (NOT the PDF filename)
clause: "7.3.1.1"            # quoted; the section/clause number
title: "M_SP_NA_1 - Single-point information without time tag"
pdf_pages: "245-246"         # quoted; the source pages this came from
# only on catalogue/ASDU entries:
type_id: 1
mnemonic: M_SP_NA_1
# only when printed != pdf numbering matters (typical for scanned docs):
printed_pages: "33-43"
---
```

The H1 title line follows the frontmatter; an italic provenance line citing source clause + page is a nice touch under headings.

## Tables → GitHub-Flavored Markdown

Every tabular structure becomes a GFM table. Never let a table flatten into space-separated prose — that destroys the structure the table existed to convey.

**Bit/octet wire-format layout** (ASDU/PDU structure) → an **Octet | Field | Description** table that keeps octet ranges and *points at* the defining clause instead of duplicating it:

```markdown
| Octet | Field | Description |
|-------|-------|-------------|
| 1 | Type identification | = 1 (`0000 0001`) |
| 2 | Variable structure qualifier | SQ, number of objects (defined in 7.2.2) |
| 3-4 | Cause of transmission | defined in 7.2.3 |
| 10 | SIQ | `IV NT SB BL 0 0 0 SPI`; defined in 7.2.6.1 |
```

**Octet bit map** (the bit layout of one octet) → header is the bit numbers `8..1`; use Unicode superscripts for powers (`2⁷`, `2⁰`, `2⁻¹³`):

```markdown
| Bit | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |
|-----|---|---|---|---|---|---|---|---|
| Field | ER | 2⁶ | 2⁵ | 2⁴ | 2³ | 2² | 2¹ | 2⁰ |
```

**General coding tables** → straightforward GFM, preserving every row including ranges written as single rows (`14..19`, `48..63`).

## Bit/octet and structural FIGURES → field tables, keep the figure number

A figure that defines a wire format or coding is **data**, not decoration. Render it as a field table (above), under a heading that **retains the original figure number and caption** so the figure's identity survives:

```markdown
## Figure 22 - Sequence of information objects (SQ = 0)
```

Capture the type-identification value, the variable-structure qualifier (SQ + count), and *every* information-element field. For protocol command/monitor types, follow with the full "causes of transmission used with TYPE IDENT n" list — split into control-direction and monitor-direction sub-tables if the source does.

## Formal `:=` / BNF definitions → fenced code blocks

Preserve formal definitions verbatim in a plain fenced block (no language tag), so spacing and structure are exact:

````markdown
```
CP56Time2a := CP56 { Milliseconds, Minutes, RES1, IV, Hours, RES2, SU,
                     Day of month, Day of week, Months, RES3, Years, RES4 }
```
````

Single-line definitions may be inline-coded with backticks instead.

## Diagrams that can't be drawn → ordered step lists or tables

Sequence diagrams, state machines, and timing diagrams can't be drawn in Markdown — but their *content* must survive. Transcribe under the figure heading (keep the number + caption), prefaced by a one-line note on the notation:

- **State machines** → a list using `event[condition]/action` notation, e.g. ``STOPPED, on `STARTDT act[]`/Send STARTDT con → **STARTED**``.
- **Sequence diagrams** → a GFM table `| # | Initiator | Service / PDU | Responder | Notes |` with arrow glyphs (`→`, `←`, `-->`) and `OPTIONAL`/`(dashed)` annotations, or a numbered step list capturing each state, event, condition, and action in order.

The goal: a reader can reconstruct the protocol exchange without the picture.

## Selection / interoperability checklists → tables with the boxes intact

Render selection sheets as GFM tables whose cells keep the literal Markdown checkbox `[ ]` (and `[X]` where ticked), preceded by an italic note on the marking convention. In a large selection matrix, defined-but-blank cells are `[ ]`, not-applicable cells use a shading glyph (`▒`), footnote markers use superscripts (`ᵃ`), and angle-bracket type ids in headers are backslash-escaped for GFM (`\<123\>`).

## Cross-references → link, don't duplicate

When a fragment references a definition that lives in another fragment, **link to it**; do not copy its content. Duplication is how a corpus goes stale and self-contradictory.

- Fragments live under `<root>/<doc>/`, so a cross-document link climbs one level: `[101 §7.2.6](../101/7.2.6-information-elements.md)`.
- Use the `linkIndex` (passed into every convert agent) to resolve a mnemonic or `"<doc> §<clause>"` to its target file.
- A trailing `--- ` then `See also:` line at the end of a fragment can link sibling/next clauses. Verify link text matches the target.
- **References to documents *outside* the corpus must be plain text, not links** — a link to a fragment that was never produced dangles. (The original run shipped 14 broken links by linking every normative reference as if its fragment existed.)
- When a clause is split into `a/b/c`, every inbound cross-reference must point at the split target, not the pre-split name. Keep an alias map if needed.

## Unreadable / low-confidence scans → mark, never invent

Do not hallucinate content for an illegible scan. Emit a blockquote at the affected spot that states precisely **what is approximate and what is exact**, and record the page in the agent's `unreadable[]` return field so it surfaces in verification:

```markdown
> [unreadable shading detail: pp.156-157 — the exact shaded vs defined-blank pattern of
> individual matrix cells is approximate; the rendered scan does not permit cell-by-cell
> certainty. The structure, type IDs, mnemonics, and column headers are exact.]
```

## OCR: the highest-risk errors

On scanned pages you are transcribing from a rendered image, and small glyphs are where fidelity dies. Watch especially for:

- **Exponents and indices** — `2^(1-i)` misread as `2^(-i)`, `i-1` vs `1-i`, sub/superscripts dropped. These are the single most common scanned-spec error.
- **Internal consistency** — if the same quantity's formula appears twice in a fragment, the two must match (and match the source). A mismatch you introduce is a real defect, not a cosmetic one.
- **Look-alike characters** — `0/O`, `1/l/I`, `8/B`, `5/S`, decimal points vs commas in numbers.
- **Wrong-language bleed** — on a bilingual scan, the facing page is the *other* language; transcribe only the target-language pages and never blend a stray line from the twin.

## Per-fragment self-check (put this in the convert prompt)

Before writing, the agent confirms it is on the right page:

1. The running header shows the expected printed page (`pdf − offset`).
2. The content is the target language and the clean/final version (no redline change-bars, struck or colored text).
3. The heading matches the fragment's `clause`/`title`. **If any check fails, search ±3 pages** to relocate the correct clean section — do not convert the wrong page.

## Token efficiency is a non-goal during conversion

Be faithful and complete. Do not abbreviate tables, drop "obvious" rows, or summarize to save space — the whole point of the corpus is that the detail is all there. (Efficiency comes later, from the *reader* loading only the fragment it needs.)
