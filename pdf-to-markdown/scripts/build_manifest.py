#!/usr/bin/env python3
"""Regenerate manifest.json deterministically from on-disk fragment frontmatter.

Walks a corpus root (<root>/<doc>/<clause>-<slug>.md), parses each fragment's
YAML-ish frontmatter with a tiny hand-rolled reader, and emits a FLAT JSON array
of {doc, clause, title, file, pdf_pages} sorted by (doc, natural-sort of clause).

Usage:
    python3 build_manifest.py <corpus_root> [--out PATH]

Machine output (the manifest) goes to the --out file (default <root>/manifest.json);
progress/warnings go to stderr. Exits nonzero on hard failures (missing root, etc.).
"""

import argparse
import json
import os
import re
import sys


def parse_frontmatter(path):
    """Read leading `---`-delimited frontmatter into a dict of str->str.

    The FIRST bytes of a fragment file must be `---`. Values are stripped of
    surrounding single or double quotes. Returns {} if there is no frontmatter.
    """
    fields = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
            if first.rstrip("\n\r") != "---":
                return fields
            for line in fh:
                stripped = line.rstrip("\n\r")
                if stripped.strip() == "---":
                    break
                if ":" not in line:
                    continue
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip()
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                    val = val[1:-1]
                fields[key] = val
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
    return fields


_NUM_RE = re.compile(r"(\d+)")


def natural_key(clause):
    """Natural sort key so '7.3.1' < '7.3.10' and numeric segments compare as ints."""
    parts = []
    for tok in _NUM_RE.split(clause):
        if tok.isdigit():
            parts.append((0, int(tok), ""))
        elif tok:
            parts.append((1, 0, tok))
    return parts


def collect_fragments(root):
    """Yield manifest entries for every fragment .md under <root>/<doc>/."""
    entries = []
    for doc in sorted(os.listdir(root)):
        doc_dir = os.path.join(root, doc)
        if not os.path.isdir(doc_dir):
            continue
        if doc == "_maps":
            continue
        for name in sorted(os.listdir(doc_dir)):
            if not name.endswith(".md") or name == "README.md":
                continue
            full = os.path.join(doc_dir, name)
            if not os.path.isfile(full):
                continue
            fm = parse_frontmatter(full)
            rel = os.path.relpath(full, root)
            rel_posix = rel.replace(os.sep, "/")
            doc_val = fm.get("source") or doc
            clause = fm.get("clause", "")
            entries.append({
                "doc": doc_val,
                "clause": clause,
                "title": fm.get("title", ""),
                "file": rel_posix,
                "pdf_pages": fm.get("pdf_pages") if fm.get("pdf_pages") else None,
            })
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Regenerate manifest.json from on-disk fragment frontmatter."
    )
    parser.add_argument("corpus_root", help="Corpus root dir containing <doc>/ subdirs")
    parser.add_argument("--out", default=None,
                        help="Output path (default <root>/manifest.json)")
    args = parser.parse_args(argv)

    root = args.corpus_root
    if not os.path.isdir(root):
        print(f"error: corpus root not found or not a directory: {root}", file=sys.stderr)
        return 1

    entries = collect_fragments(root)
    if not entries:
        print(f"error: no fragment .md files found under {root}", file=sys.stderr)
        return 1

    entries.sort(key=lambda e: (str(e["doc"]), natural_key(e["clause"])))

    out_path = args.out if args.out else os.path.join(root, "manifest.json")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except OSError as exc:
        print(f"error: cannot write {out_path}: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {len(entries)} entries to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
