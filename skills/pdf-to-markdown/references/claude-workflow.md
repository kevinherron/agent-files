# Claude Workflow adapter

Use this reference only when a compatible Claude Workflow tool is available and the
requested task authorizes its use. The portable conversion contract is in SKILL.md and
references/architecture.md. Missing Workflow support does not block direct conversion
or native-host delegation.

## Adapt the templates

- `assets/map-workflow-template.js` plans source fragments.
- `assets/workflow-template.js` converts, verifies, and assembles a mapped corpus.

Resolve script and reference paths from the loaded skill directory. Set the output ROOT
and source profiles to the actual inputs. Build `_maps/_all.json` before conversion and
confirm the prompt includes the current fidelity rules. Validate the page map in the
coordinating thread before conversion; this is an evidence check, not a user approval gate.

The templates use Claude's Workflow `agent`, `parallel`, `pipeline`, and PDF `Read`
interfaces. Verify their current schemas and page limits in the host. They are not native
Codex APIs. In another host, use its PDF rendering and image tools and preserve the same
page ownership and fidelity contracts.

Set conversion batch size from the available worker slots, reserving coordinator capacity
where needed. The template defaults to one worker; raise it only within verified host
limits. Also bound map and verification fan-out when adapting the templates. There is no
portable 16-agent ceiling. Preserve the session's model and effort unless the user or
host configuration authorizes overrides; the template's effortFor function is an optional
Claude-specific tuning example, not a fidelity requirement.

After conversion, regenerate the manifest with `scripts/build_manifest.py` and run
`scripts/validate_corpus.py`. Verify disk contents instead of trusting agent return values.

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
