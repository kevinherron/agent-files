// =============================================================================
// pdf-to-markdown — MAP Workflow template (the cheap planning phase)
//
// One planner agent per PDF. Each reads only enough pages to emit a JSON plan
// of fragments with EXACT page ranges; it writes NO fragment content. Output:
// one ROOT/_maps/<doc>.json per document.
//
// AFTER this returns (the REVIEW GATE — see references/architecture.md):
//   1. For text-layer PDFs that bundle redline+clean or multiple languages, run
//      scripts/pdf_pagemap.py and confirm the offset is CONSTANT at >=3 anchors.
//   2. Run scripts/build_all_map.py to merge the per-doc plans into _all.json.
//   3. Only then run assets/workflow-template.js (convert/verify/assemble).
//
// For a LARGE single PDF with an embedded outline, prefer building the plan from
// scripts/pdf_probe.py's outline dump (see references/scaling.md) instead of
// having one agent skim 1500 pages — then you may skip this workflow entirely
// and write _maps/<doc>.json from the outline + windowing directly.
//
// TO ADAPT: set ROOT and fill DOCS (one entry per PDF) with a pre-scouted
// profile string (page count, language/version layout, the target region and
// offset if you already know them, and a fragment-enumeration hint).
// =============================================================================

export const meta = {
  name: 'pdf-map',
  description: 'Plan each PDF into per-clause fragment records with exact page ranges (planner agents, no content written)',
  phases: [{ title: 'Map', detail: 'one agent per PDF: resolve structure, enumerate fragments' }],
}

const ROOT = '/ABSOLUTE/PATH/TO/md'

const MAP_SCHEMA = {
  type: 'object', additionalProperties: true,
  required: ['doc', 'total_pdf_pages', 'target_pdf_range', 'printed_to_pdf_offset', 'fragments'],
  properties: {
    doc: { type: 'string' },
    pdf_file: { type: 'string' },
    total_pdf_pages: { type: 'number' },
    language_layout: { type: 'string', description: 'how languages are arranged, if multilingual' },
    version_split: { type: 'string', description: 'how redline vs clean/consolidated are arranged, if bundled' },
    printed_to_pdf_offset: { type: 'string', description: 'formula: printed = pdf - N, within the target region' },
    target_pdf_range: { type: 'array', items: { type: 'number' }, description: '[start, end] PDF pages of the body to convert' },
    structure_notes: { type: 'string' },
    fragments: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: true,
        required: ['clause', 'title', 'pdf_pages', 'target_file', 'kind'],
        properties: {
          clause: { type: 'string' },
          title: { type: 'string' },
          printed_pages: { type: 'string' },
          pdf_pages: { type: 'string', description: 'EXACT pdf page range to read, e.g. "232-235"' },
          target_file: { type: 'string', description: 'path relative to ROOT, e.g. "104/5.3-startstop.md"' },
          kind: { type: 'string', enum: ['clause', 'asdu', 'checklist', 'coding-table', 'bitfield', 'procedure', 'overview'] },
          scanned: { type: 'boolean' },
          type_ids: { type: 'array', items: { type: 'object', additionalProperties: true } },
          figures: { type: 'array', items: { type: 'string' } },
          est_lines: { type: 'number' },
          cross_refs: { type: 'array', items: { type: 'string' } },
          notes: { type: 'string' },
        },
      },
    },
  },
}

// Shared planning rules prepended to every per-doc prompt.
const SHARED = `You are mapping ONE PDF into a plan of markdown fragments for downstream conversion.
RULES:
- Use the Read tool with the \`pages\` parameter; read <= 15 pages per call. (Quote the path if you ever shell out; some filenames contain { } or spaces.)
- PLANNING ONLY: do NOT write fragment content. Produce a JSON plan giving, for every fragment, the EXACT pdf_pages a downstream agent must read.
- Plan ONLY the target content (the clean/consolidated version, target language). Exclude redline pages (margin change-bars, struck/colored text) and other-language pages.
- Granularity: one fragment per second-level section by default. EXCEPTIONS: every atomic catalogue entry (e.g. one ASDU / object type / opcode) is its OWN fragment; if a section would clearly exceed ~600 lines, plan to split it (note in est_lines/notes).
- For each fragment set: clause, title, printed_pages, pdf_pages (EXACT), target_file (relative to ROOT, lowercase-kebab; catalogue files like "<doc>/<clause>-t<NN>-<mnemonic>.md"), kind, scanned (true if no text layer), figures (numbers it contains), est_lines (rough), cross_refs (sections in OTHER docs it references), and for catalogue fragments type_ids:[{id,mnemonic,title}].
- Determine printed_to_pdf_offset for the target region and set target_pdf_range.
- VALIDATE by actually reading a few pages: confirm the target-language clean heading appears on the pdf_pages you assign (not the wrong language, not redline).
- Before returning, ALSO write your full JSON plan to \`${ROOT}/_maps/<doc>.json\` with the Write tool.`

// One entry per PDF. The `profile` is what you pre-scouted with pdf_probe.py /
// pdf_pagemap.py: page count, layout, the target region + offset, and any
// known fragment enumeration. The better the profile, the better the plan.
const DOCS = [
  // {
  //   doc: '104',
  //   profile: `DOCUMENT: <name>. File: \`/path/to/file.pdf\` (NNN pdf pages). doc id = "104".
  // CONFIRMED LAYOUT: <redline/clean + language arrangement>. Target = <region>, printed = PDF - <offset>.
  // TOC (printed pages): <paste the contents listing>.
  // Plan fragments: <enumerate the target files + kinds>. Give exact pdf_pages for each.`,
  // },
]

phase('Map')
if (!DOCS.length) throw new Error('Fill DOCS with one entry per PDF before running.')
const maps = await parallel(DOCS.map((d) => () =>
  agent(`${SHARED}\n\n${d.profile}`, { label: `map:${d.doc}`, phase: 'Map', schema: MAP_SCHEMA, effort: 'high' })
))

const summary = maps.filter(Boolean).map((m) => ({
  doc: m.doc,
  target_pdf_range: m.target_pdf_range,
  offset: m.printed_to_pdf_offset,
  fragment_count: (m.fragments || []).length,
  structure_notes: m.structure_notes,
}))
log(`Mapped ${summary.length}/${DOCS.length} document(s): ${summary.map((s) => `${s.doc}=${s.fragment_count}`).join(', ')}`)
return {
  summary,
  review_gate: 'Validate offsets with scripts/pdf_pagemap.py (constant at >=3 anchors), then merge with scripts/build_all_map.py before converting.',
  maps,
}
