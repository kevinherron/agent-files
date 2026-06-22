#!/usr/bin/env python3
"""Merge per-document map plans into a single _all.json.

Reads every ``<doc>.json`` in a maps directory (skipping ``_all.json``) and
builds the combined corpus index used by downstream conversion/validation:

    {
      "docMeta":   {<doc>: {pdf_file, offset:int, clean:str}},
      "linkIndex": {
        "byMnemonic": {<mnemonic>: target_file},
        "byClause":   {"<doc> §<clause>": target_file}
      },
      "fragments": [<each fragment with injected doc + pdf_file>]
    }

byMnemonic is built from each fragment's ``type_ids[].mnemonic``. The script is
tolerant of missing optional fields: the per-doc offset may be an int field
(``offset``) or has to be regex-extracted from a directive string such as
``printed_to_pdf_offset`` ("PDF page = printed + 144"); the clean directive may
live under ``clean`` or ``structure_notes``.

Usage:
    python3 build_all_map.py <maps_dir> [--out PATH]

Machine output (the merged map) is written to ``--out`` (default
``<maps_dir>/_all.json``); a per-doc / per-kind distribution is printed to
stderr. Exits nonzero on missing dir, no inputs, or unreadable maps.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

# Pull the first integer out of an offset directive string, e.g.
# "PDF page = printed page + 144" -> 144 (signed if a leading - is present).
_OFFSET_RE = re.compile(r"([+-]?\d+)")


def log(msg):
    print(msg, file=sys.stderr)


def die(msg, code=1):
    log(f"error: {msg}")
    sys.exit(code)


def extract_offset(header):
    """Return an int offset from the header, tolerating several shapes."""
    if isinstance(header.get("offset"), int):
        return header["offset"]
    # offset may be a numeric string
    if isinstance(header.get("offset"), str):
        m = _OFFSET_RE.search(header["offset"])
        if m:
            return int(m.group(1))
    raw = header.get("printed_to_pdf_offset")
    if isinstance(raw, (int,)):
        return raw
    if isinstance(raw, str):
        m = _OFFSET_RE.search(raw)
        if m:
            return int(m.group(1))
    return 0


def extract_clean(header):
    """Return the clean/structure directive string, tolerating naming."""
    for key in ("clean", "structure_notes", "clean_notes"):
        val = header.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def load_map(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        die(f"could not read map {path!r}: {exc}")


def build(maps_dir):
    try:
        entries = sorted(os.listdir(maps_dir))
    except OSError as exc:
        die(f"cannot list maps dir {maps_dir!r}: {exc}")

    map_files = [
        os.path.join(maps_dir, name)
        for name in entries
        if name.endswith(".json") and name != "_all.json"
    ]
    if not map_files:
        die(f"no per-document map files (*.json) found in {maps_dir!r}")

    doc_meta = {}
    by_mnemonic = {}
    by_clause = {}
    fragments = []
    per_doc = Counter()
    per_kind = Counter()

    for path in map_files:
        data = load_map(path)
        if not isinstance(data, dict):
            die(f"map {path!r} is not a JSON object")

        doc = data.get("doc") or os.path.splitext(os.path.basename(path))[0]
        pdf_file = data.get("pdf_file", "")
        offset = extract_offset(data)
        clean = extract_clean(data)

        doc_meta[str(doc)] = {
            "pdf_file": pdf_file,
            "offset": offset,
            "clean": clean,
        }

        frags = data.get("fragments") or []
        if not isinstance(frags, list):
            die(f"map {path!r} 'fragments' is not a list")

        for frag in frags:
            if not isinstance(frag, dict):
                log(f"warning: skipping non-object fragment in {path!r}")
                continue
            merged = dict(frag)
            merged["doc"] = str(doc)
            merged["pdf_file"] = pdf_file
            fragments.append(merged)

            per_doc[str(doc)] += 1
            per_kind[merged.get("kind", "?")] += 1

            target = merged.get("target_file")
            clause = merged.get("clause")
            if target and clause is not None:
                by_clause[f"{doc} §{clause}"] = target

            if target:
                for tid in merged.get("type_ids") or []:
                    if isinstance(tid, dict):
                        mnemonic = tid.get("mnemonic")
                        if isinstance(mnemonic, str) and mnemonic.strip():
                            by_mnemonic[mnemonic.strip()] = target

    result = {
        "docMeta": doc_meta,
        "linkIndex": {
            "byMnemonic": by_mnemonic,
            "byClause": by_clause,
        },
        "fragments": fragments,
    }
    return result, per_doc, per_kind, len(map_files)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge per-document map plans into _all.json."
    )
    parser.add_argument("maps_dir", help="directory holding <doc>.json map files")
    parser.add_argument(
        "--out",
        help="output path (default: <maps_dir>/_all.json)",
    )
    args = parser.parse_args(argv)

    maps_dir = args.maps_dir
    if not os.path.isdir(maps_dir):
        die(f"maps_dir is not a directory: {maps_dir!r}")

    out_path = args.out or os.path.join(maps_dir, "_all.json")

    result, per_doc, per_kind, n_maps = build(maps_dir)

    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except OSError as exc:
        die(f"could not write output {out_path!r}: {exc}")

    log(f"merged {n_maps} map file(s) -> {out_path}")
    log(f"fragments: {len(result['fragments'])}")
    log(f"byMnemonic: {len(result['linkIndex']['byMnemonic'])}")
    log(f"byClause: {len(result['linkIndex']['byClause'])}")
    log("per-doc distribution:")
    for doc in sorted(per_doc):
        log(f"  {doc}: {per_doc[doc]}")
    log("per-kind distribution:")
    for kind in sorted(per_kind):
        log(f"  {kind}: {per_kind[kind]}")

    print(json.dumps({"out": out_path, "fragments": len(result["fragments"])}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
