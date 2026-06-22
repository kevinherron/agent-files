// =============================================================================
// pdf-to-markdown — CONVERT → VERIFY → ASSEMBLE Workflow template
//
// This is the expensive production pipeline. Run it AFTER the map phase has
// produced md/_maps/_all.json (see assets/map-workflow-template.js and the
// review gate in references/architecture.md). It loads that plan, fans out one
// convert agent per fragment (batched under the concurrency ceiling), verifies
// a stratified sample adversarially with inline reconvert, then assembles the
// README. Regenerate manifest.json deterministically with scripts/build_manifest.py.
//
// TO ADAPT:
//   1. Set ROOT to the single output-root absolute path (no trailing slash).
//   2. Confirm _all.json exists at ROOT/_maps/_all.json with {docMeta, linkIndex, fragments}.
//   3. Make sure FIDELITY matches references/fidelity-rules.md (edit to taste per document).
//   4. Tune SAMPLE_PER_KIND / the verify sample so every `kind` you have is covered.
//   5. Run through the Workflow tool. After it returns, run scripts/build_manifest.py
//      and scripts/validate_corpus.py, and re-dispatch any gaps they find.
// =============================================================================

export const meta = {
  name: 'pdf-convert',
  description: 'Convert planned PDF fragments to markdown (batched fan-out), adversarially verify a sample with inline reconvert, then assemble the README',
  phases: [
    { title: 'Load',     detail: 'read the merged _all.json plan' },
    { title: 'Convert',  detail: 'one agent per fragment, batched under the concurrency cap' },
    { title: 'Verify',   detail: 'adversarial sample vs source; reconvert real failures' },
    { title: 'Assemble', detail: 'write README.md (manifest is regenerated deterministically after)' },
  ],
}

// ---- PARAMETERS -------------------------------------------------------------
const ROOT = '/ABSOLUTE/PATH/TO/md'          // <-- the one output root; every agent writes only under here
const ALL_JSON = `${ROOT}/_maps/_all.json`
const BATCH = 14                              // convert wave size; keep < ~16 concurrency ceiling

// ---- SCHEMAS ----------------------------------------------------------------
const CONVERT_SCHEMA = {
  type: 'object', additionalProperties: true,
  required: ['target_file', 'files_written', 'status'],
  properties: {
    target_file: { type: 'string' },
    files_written: { type: 'array', items: { type: 'string' }, description: 'every file actually written (incl. a/b/c splits)' },
    doc: { type: 'string' }, clause: { type: 'string' }, title: { type: 'string' }, pdf_pages: { type: 'string' },
    type_ids: { type: 'array', items: { type: 'object', additionalProperties: true } },
    codes: { type: 'array', items: { type: 'object', additionalProperties: true } },
    unreadable: { type: 'array', items: { type: 'string' } },
    status: { type: 'string', enum: ['ok', 'partial'] },
    notes: { type: 'string' },
  },
}
const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: true,
  required: ['file', 'verdict', 'needs_reconvert'],
  properties: {
    file: { type: 'string' },
    verdict: { type: 'string', enum: ['ok', 'minor', 'fail'] },
    problems: { type: 'array', items: { type: 'string' } },
    needs_reconvert: { type: 'boolean' },
  },
}

// ---- EFFORT TIERING ---------------------------------------------------------
// Scanned pages (OCR from image) and dense structured fragments earn high effort;
// prose clauses get medium. Token frugality is a non-goal — fidelity is.
function effortFor(f) {
  if (f.scanned) return 'high'
  if (['asdu', 'coding-table', 'checklist', 'bitfield'].includes(f.kind)) return 'high'
  return 'medium'
}

// ---- FIDELITY RULES (keep in sync with references/fidelity-rules.md) --------
const FIDELITY = `FIDELITY RULES (this corpus exists to preserve exact detail; faithfulness over brevity):
- Open the file with YAML frontmatter: source, clause, title, pdf_pages (+ type_id, mnemonic for catalogue/ASDU entries; printed_pages when printed != pdf). First bytes of the file must be the --- line. \`source\` MUST be the short document id (the subdirectory name) — NOT the PDF filename.
- Preserve EXACTLY every identifier, type id, mnemonic, code, bit/field name, qualifier, enumerated value, and numeric range. These are the point of the document.
- Transcribe verbatim, including obvious source typos. If you correct an evident error, mark it with an HTML comment: <!-- source reads "X"; obvious typo for Y -->. Never silently "improve".
- Do NOT fabricate structure absent from the source. Render a figure that is a DIAGRAM (protocol stack, topology, flow chart) as a faithful labeled list or ordered step list — do NOT invent table column headers it never had. Do not synthesize summary/overview tables the source lacks, and do not add cross-references beyond the link index. Correct-but-absent structure is still a deviation; if added deliberately, mark it with an HTML comment.
- Tables -> GitHub-flavored markdown tables. Bit/octet wire-format and structural figures -> a field table (Octet | Field | Description), NOT prose, under a heading that keeps the original figure number and caption. Capture the type-id value, the structure qualifier, and every field; then the full causes-of-transmission / applicability list if present.
- Formal ":=" / BNF definitions -> plain fenced code blocks (no language tag), verbatim spacing.
- Sequence/state/timing diagrams -> ordered step lists or a GFM table with arrow glyphs, keeping the figure number; capture every state/event/condition/action so the exchange can be reconstructed.
- Selection / interoperability checklists -> GFM tables with the boxes intact: [ ] and [X]. Preserve every row.
- Cross-references: LINK to the target fragment (../<doc>/<file>.md via the link index), do NOT duplicate its content. References to documents NOT in this corpus -> plain text, not links.
- Scanned pages: transcribe ONLY the target-language pages; skip the facing twin. Watch exponents/indices (2^(1-i) vs 2^(-i)), look-alike chars, and keep repeated formulae internally consistent.
- Do NOT invent content for unreadable scans: write "> [unreadable: <what is approximate; what IS exact>]" at that spot and record the page in the unreadable[] return field.
- If your markdown would exceed ~600 lines, split into sibling files with a/b/c suffixes before ".md" and return ALL of them in files_written.`

// ---- CONVERT PROMPT BUILDER -------------------------------------------------
// For windowed large-PDF conversion (see references/scaling.md): the plan from
// plan_from_outline.py carries each fragment's `prev_end`; add a page-ownership note
// to this prompt ("page prev_end is context only; begin new transcription at prev_end+1,
// include any pre-heading tail under a (continued) marker; set continues=true if a section
// runs past your last page") so a section's tail isn't dropped at a window boundary.
function convertPrompt(f, dm, linkIndexStr, extra) {
  const scannedNote = f.scanned
    ? 'These pages are SCANNED (no text layer): read them as rendered images and OCR carefully; transcribe ONLY the target-language pages, skipping the facing twin.'
    : 'You may cross-check prose/tables with: pdftotext -f START -l END -layout "' + dm.pdf_path + '" -   (quote the path). But use the rendered page images for any figure/diagram.'
  return `Convert ONE section of a document into a single faithful markdown fragment.

DOCUMENT "${f.doc}". PDF file: \`${dm.pdf_path}\`. ${dm.clean}
Printed page = PDF page minus ${dm.offset}.

FRAGMENT TO PRODUCE:
${JSON.stringify({ clause: f.clause, title: f.title, kind: f.kind, scanned: !!f.scanned, pdf_pages: f.pdf_pages, printed_pages: f.printed_pages, figures: f.figures, type_ids: f.type_ids, cross_refs: f.cross_refs, est_lines: f.est_lines, notes: f.notes, target_file: f.target_file }, null, 1)}

STEPS:
1. Read PDF pages ${f.pdf_pages} with the Read tool (it renders pages as IMAGES — essential for figures and scans). For >15 pages, use multiple Read calls of <=15 pages each. ${scannedNote}
2. Confirm you are on the correct page: the running header should show printed page (PDF - ${dm.offset}); content must be the target language and the clean/final version (no redline change-bars, struck or colored text), and the heading must match this fragment's clause/title. If wrong, search +/-3 pages to locate the correct clean section.
3. Write the fragment to \`${ROOT}/${f.target_file}\` with the Write tool. Write ONLY under \`${ROOT}\` — never substitute the document id into the directory path. The frontmatter \`source:\` field MUST be exactly \`${f.doc}\` (the doc id), not the PDF filename.
4. After writing, verify the file exists (Read or ls it). Only then report success.

${FIDELITY}

LINK INDEX (mnemonic -> file, and "doc §clause" -> file; prefix targets with ../ to link from inside ${ROOT}/<doc>/):
${linkIndexStr}
${extra || ''}
Return the structured metadata: target_file, files_written (EVERY file you wrote), type_ids, codes, unreadable[], status, notes.`
}

// ---- PHASE: LOAD ------------------------------------------------------------
phase('Load')
const loaded = await agent(
  `Read the JSON file \`${ALL_JSON}\` and return its parsed contents verbatim (keys: docMeta, linkIndex, fragments). Use the Read tool.`,
  { label: 'load:maps', phase: 'Load', effort: 'low',
    schema: { type: 'object', additionalProperties: true, required: ['fragments', 'docMeta', 'linkIndex'],
      properties: { fragments: { type: 'array', items: { type: 'object', additionalProperties: true } }, docMeta: { type: 'object', additionalProperties: true }, linkIndex: { type: 'object', additionalProperties: true } } } }
)
if (!loaded || !loaded.fragments) throw new Error('load failed: no fragments in _all.json')
const fragments = loaded.fragments
const docMeta = loaded.docMeta
const linkIndexStr = JSON.stringify(loaded.linkIndex)
const byFile = {}
for (const f of fragments) byFile[f.target_file] = f
log(`Loaded ${fragments.length} fragments across ${Object.keys(docMeta).length} document(s)`)

// ---- PHASE: CONVERT (batched — never one giant parallel barrier) -----------
phase('Convert')
const convResults = []
for (let i = 0; i < fragments.length; i += BATCH) {
  const batch = fragments.slice(i, i + BATCH)
  const out = await parallel(batch.map((f) => () =>
    agent(convertPrompt(f, docMeta[f.doc], linkIndexStr), {
      label: `conv:${f.target_file}`, phase: 'Convert', schema: CONVERT_SCHEMA, effort: effortFor(f),
    })
  ))
  convResults.push(...out)
  log(`converted ${Math.min(i + BATCH, fragments.length)}/${fragments.length}`)
}
// For a SMALL corpus (<~60 fragments) you can replace the loop above with a single barrier:
//   const convResults = await parallel(fragments.map(f => () => agent(convertPrompt(...), {...})))
const meta2 = convResults.filter(Boolean)
const died = fragments.filter((f, i) => !convResults[i]).map((f) => f.target_file)
log(`Convert done: ${meta2.length}/${fragments.length} returned${died.length ? `; ${died.length} died -> re-dispatch: ${died.join(', ')}` : ''}`)

// ---- PHASE: VERIFY (adversarial sample + inline reconvert) ------------------
// Stratify: a few per kind, weighted to dense table/figure fragments + a tail.
phase('Verify')
const SAMPLE_PER_KIND = 3
const byKind = {}
for (const f of fragments) (byKind[f.kind] = byKind[f.kind] || []).push(f.target_file)
const SAMPLE = []
for (const k of Object.keys(byKind)) SAMPLE.push(...byKind[k].slice(0, SAMPLE_PER_KIND))
// add a deterministic tail sample (every Nth file) without Math.random:
for (let i = 0; i < fragments.length; i += Math.max(1, Math.floor(fragments.length / 10))) SAMPLE.push(fragments[i].target_file)
const SAMPLE_UNIQ = [...new Set(SAMPLE)].filter((tf) => byFile[tf])

const verifyResults = await pipeline(SAMPLE_UNIQ,
  (tf) => {
    const f = byFile[tf]; const dm = docMeta[f.doc]
    return agent(
      `Adversarially verify one produced fragment against its SOURCE pages — try to find a fidelity defect.
Produced file: \`${ROOT}/${tf}\` (Read it).
Source: PDF \`${dm.pdf_path}\`, pages ${f.pdf_pages} (printed = PDF - ${dm.offset}). Read those pages (images). ${f.scanned ? 'Scanned: compare against the target-language pages only.' : ''}
Check rigorously: (a) every identifier / code / field name / numeric range present and correct; (b) wire-format/bit-layout rendered as a field table with the right figure number; (c) tables and checklist boxes complete, none dropped; (d) no OCR garble, wrong-language, redline contamination, or hallucinated content; (e) frontmatter present and correct.
Verdict policy: a NAMED wrong number/code/exponent or a dropped/garbled table is "fail" + needs_reconvert=true. Purely cosmetic wording is "minor", needs_reconvert=false.
Return {file, verdict, problems[], needs_reconvert}.`,
      { label: `verify:${tf}`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'high' }
    )
  },
  (verdict, tf) => {
    if (!verdict || !verdict.needs_reconvert) return { file: tf, reconverted: false, verdict }
    const f = byFile[tf]; const dm = docMeta[f.doc]
    return agent(
      convertPrompt(f, dm, linkIndexStr, `\nRE-CONVERT: the prior version FAILED verification. Fix these problems specifically:\n- ${(verdict.problems || []).join('\n- ')}\nRead the source pages again carefully and overwrite the file(s).`),
      { label: `reconv:${tf}`, phase: 'Verify', schema: CONVERT_SCHEMA, effort: 'high' }
    ).then((r) => ({ file: tf, reconverted: true, verdict, reconvert: r }))
  }
)

// ---- PHASE: ASSEMBLE (after verify, so the README reflects repaired files) --
// NOTE: regenerate manifest.json deterministically with scripts/build_manifest.py
// AFTER this workflow returns — don't hand-write it here.
phase('Assemble')
const manifestRows = meta2.flatMap((m) => (m.files_written && m.files_written.length ? m.files_written : [m.target_file]).map((file) => ({ doc: m.doc, clause: m.clause, title: m.title, file, pdf_pages: m.pdf_pages })))
const typeIdRows = meta2.flatMap((m) => (m.type_ids || []).map((t) => ({ ...t, doc: m.doc, file: m.target_file })))

const assemble = await agent(
  `Write \`${ROOT}/README.md\` — the human entry point for this markdown corpus.

You are given the full fragment metadata (JSON). You may Read a couple of fragments that hold master tables (e.g. a code table or a type catalogue) to build authoritative quick-lookup tables.

FRAGMENT METADATA (doc, clause, title, file, pdf_pages):
${JSON.stringify(manifestRows)}

CATALOGUE ROWS collected during conversion (id/mnemonic/title/doc/file):
${JSON.stringify(typeIdRows)}

README.md must contain:
1. A short intro: what this corpus is and how it is organized; for a multi-document corpus, name the anchor document and how the documents relate.
2. A full TABLE OF CONTENTS linking every fragment, grouped by document and clause (relative links like \`104/5.3-startstop.md\`).
3. QUICK-LOOKUP TABLES appropriate to the document(s): a master id <-> mnemonic <-> defining-fragment table (sorted by id, fragment linked); any code tables; a per-document clause map; and cross-reference maps between documents. Surface the document's own master indexes as linked markdown.
Keep it clean and navigable — this is the entry point an agent loads first.

Return {files_written:[...], notes}.`,
  { label: 'assemble:readme', phase: 'Assemble', effort: 'medium', schema: { type: 'object', additionalProperties: true } }
)

return {
  converted: meta2.length,
  died,
  unreadable: meta2.filter((m) => (m.unreadable || []).length).map((m) => ({ file: m.target_file, marks: m.unreadable })),
  verify: verifyResults.filter(Boolean).map((v) => ({ file: v.file, verdict: v.verdict && v.verdict.verdict, reconverted: v.reconverted, problems: v.verdict && v.verdict.problems })),
  assemble,
  next_steps: 'Run scripts/build_manifest.py then scripts/validate_corpus.py; re-dispatch any gaps.',
}
