#!/usr/bin/env python3
"""Quality gate for a pdf-to-markdown corpus.

Validates a corpus rooted at <corpus_root> (documents live in
`<root>/<doc>/`, fragments are `<root>/<doc>/<clause>-<slug>.md`, planning
artifacts in `<root>/_maps/`). Runs five checks and prints a JSON report to
STDOUT; exits NONZERO when any HARD failure is found.

Checks:
  1. frontmatter (HARD) - every fragment starts with '---' and has
     source+clause+title; source must be in the allowed set.
  2. manifest_disk_reconcile (HARD) - manifest 'file's vs glob('<root>/*/*.md').
  3. links (HARD) - every internal '](X.md)' link resolves to a fragment.
  4. oversize (WARN) - fragments whose line count exceeds --max-lines.
  5. coverage (WARN, only with --all-json) - per doc, pages in the target
     region covered by no fragment (a planning-gap signal; genuinely dropped
     fragments are caught HARD by manifest_disk_reconcile).

Stdlib + nothing else. Human progress/warnings go to STDERR.
"""

import argparse
import glob
import json
import os
import re
import sys

# Shared format constants (identical across skill scripts).
LINK_RE = re.compile(r'\]\(([^)]+\.md)(#[^)]*)?\)')
DEFAULT_MAX_LINES = 600


def warn(msg):
    print(msg, file=sys.stderr)


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def parse_frontmatter(path):
    """Hand-rolled tiny frontmatter reader.

    Returns (fields_dict, error_str_or_None). The first bytes of a fragment
    file must be '---'. Fields are split on the first ':' and surrounding
    quotes are stripped.
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            text = fh.read()
    except OSError as exc:
        return {}, "unreadable: %s" % exc
    if not text.startswith('---'):
        return {}, "does not start with '---'"
    lines = text.splitlines()
    # First line is the opening '---'; find the closing '---'.
    fields = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == '---':
            closed = True
            break
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        fields[key] = val
    if not closed:
        return fields, "frontmatter not closed with '---'"
    return fields, None


def list_fragments(root):
    """Root-relative fragment paths matching <root>/*/*.md, excluding _maps
    and README files."""
    out = []
    for p in glob.glob(os.path.join(root, '*', '*.md')):
        rel = os.path.relpath(p, root)
        parts = rel.split(os.sep)
        if parts[0] == '_maps':
            continue
        if os.path.basename(p).upper().startswith('README'):
            continue
        out.append(rel.replace(os.sep, '/'))
    return sorted(out)


def infer_sources(root):
    """Allowed sources inferred from <root> subdir names (those containing
    at least one .md fragment)."""
    srcs = set()
    for rel in list_fragments(root):
        srcs.add(rel.split('/')[0])
    return srcs


def parse_pages(spec):
    """Parse a pdf_pages spec like 'a-b' or 'n' into a set of ints. Handles
    comma-separated multi-ranges defensively. Returns set()."""
    pages = set()
    if not spec:
        return pages
    for chunk in str(spec).replace(';', ',').split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r'^(\d+)\s*[-–]\s*(\d+)$', chunk)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > b:
                a, b = b, a
            pages.update(range(a, b + 1))
            continue
        m = re.match(r'^(\d+)$', chunk)
        if m:
            pages.add(int(m.group(1)))
    return pages


def check_frontmatter(root, fragments, allowed_sources):
    """Check 1 (HARD)."""
    failures = []
    for rel in fragments:
        path = os.path.join(root, rel)
        fields, err = parse_frontmatter(path)
        if err:
            failures.append({"file": rel, "problem": err})
            continue
        missing = [k for k in ('source', 'clause', 'title')
                   if not fields.get(k)]
        if missing:
            failures.append({"file": rel,
                             "problem": "missing fields: %s" % ",".join(missing)})
            continue
        src = fields['source']
        if allowed_sources and src not in allowed_sources:
            failures.append({"file": rel,
                             "problem": "source not in allowed set: %r" % src,
                             "allowed": sorted(allowed_sources)})
    return {"checked": len(fragments), "failures": failures}, failures


def check_manifest_disk(root, manifest, disk_set):
    """Check 2 (HARD)."""
    manifest_files = [row.get('file') for row in manifest if row.get('file')]
    manifest_set = set(manifest_files)
    seen = {}
    dups = []
    for f in manifest_files:
        seen[f] = seen.get(f, 0) + 1
    for f, n in seen.items():
        if n > 1:
            dups.append({"file": f, "count": n})
    in_manifest_not_on_disk = sorted(manifest_set - disk_set)
    on_disk_not_in_manifest = sorted(disk_set - manifest_set)
    result = {
        "manifest_rows": len(manifest),
        "disk_fragments": len(disk_set),
        "in_manifest_not_on_disk": in_manifest_not_on_disk,
        "on_disk_not_in_manifest": on_disk_not_in_manifest,
        "duplicate_manifest_rows": sorted(dups, key=lambda d: d["file"]),
    }
    hard = bool(in_manifest_not_on_disk) or bool(on_disk_not_in_manifest)
    return result, hard


def check_links(root, fragments, disk_set):
    """Check 3 (HARD)."""
    unresolved = []
    total = 0
    for rel in fragments:
        path = os.path.join(root, rel)
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                text = fh.read()
        except OSError as exc:
            unresolved.append({"file": rel, "link": None,
                               "problem": "unreadable: %s" % exc})
            continue
        for m in LINK_RE.finditer(text):
            target = m.group(1)
            total += 1
            # Skip absolute URLs (defensive); links are relative paths.
            if '://' in target:
                continue
            resolved = os.path.normpath(
                os.path.join(os.path.dirname(rel), target))
            resolved = resolved.replace(os.sep, '/')
            if resolved not in disk_set:
                unresolved.append({"file": rel, "link": target,
                                   "resolved": resolved})
    return {"links_checked": total, "unresolved": unresolved}, unresolved


def check_oversize(root, fragments, max_lines):
    """Check 4 (WARN)."""
    over = []
    for rel in fragments:
        path = os.path.join(root, rel)
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                n = sum(1 for _ in fh)
        except OSError:
            continue
        if n > max_lines:
            over.append({"file": rel, "lines": n})
    return {"max_lines": max_lines, "oversize": sorted(over, key=lambda d: -d["lines"])}, over


def check_coverage(all_json):
    """Check 5 (WARN). Per doc, union of fragment pdf_pages vs the doc's
    target region (docMeta target range if present, else min..max of the
    doc's own pages). Report pages in range covered by no fragment."""
    doc_meta = all_json.get('docMeta', {}) or {}
    fragments = all_json.get('fragments', []) or []
    by_doc = {}
    for f in fragments:
        doc = f.get('doc')
        if doc is None:
            continue
        by_doc.setdefault(doc, set()).update(parse_pages(f.get('pdf_pages')))

    gaps = {}
    per_doc = {}
    for doc, covered in by_doc.items():
        meta = doc_meta.get(doc, {}) or {}
        region = None
        # Accept an explicit target range if docMeta provides one.
        for key in ('target_pages', 'target', 'pdf_pages', 'range'):
            if key in meta:
                region = parse_pages(meta[key])
                break
        if not region:
            if covered:
                region = set(range(min(covered), max(covered) + 1))
            else:
                region = set()
        missing = sorted(region - covered)
        per_doc[doc] = {
            "region_min": min(region) if region else None,
            "region_max": max(region) if region else None,
            "covered_pages": len(covered),
            "uncovered_pages": missing,
        }
        if missing:
            gaps[doc] = missing
    return {"per_doc": per_doc, "docs_with_gaps": sorted(gaps.keys())}, gaps


def main():
    ap = argparse.ArgumentParser(
        description="Validate a pdf-to-markdown corpus (quality gate).")
    ap.add_argument("corpus_root", help="corpus root directory")
    ap.add_argument("--manifest", default=None,
                    help="path to manifest.json (default <root>/manifest.json)")
    ap.add_argument("--all-json", default=None,
                    help="path to _all.json (default <root>/_maps/_all.json if present)")
    ap.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES,
                    help="oversize warning threshold (default 600)")
    ap.add_argument("--sources", default=None,
                    help="comma-separated allowed source set (else inferred)")
    args = ap.parse_args()

    root = os.path.abspath(args.corpus_root)
    if not os.path.isdir(root):
        die("error: corpus root is not a directory: %s" % root)

    manifest_path = args.manifest or os.path.join(root, "manifest.json")
    all_json_path = args.all_json
    if all_json_path is None:
        cand = os.path.join(root, "_maps", "_all.json")
        if os.path.exists(cand):
            all_json_path = cand

    if not os.path.exists(manifest_path):
        die("error: manifest not found: %s" % manifest_path)
    try:
        with open(manifest_path, 'r', encoding='utf-8') as fh:
            manifest = json.load(fh)
    except (OSError, ValueError) as exc:
        die("error: cannot parse manifest %s: %s" % (manifest_path, exc))
    if not isinstance(manifest, list):
        die("error: manifest must be a flat JSON array")

    fragments = list_fragments(root)
    if not fragments:
        die("error: no fragments found under %s/*/*.md" % root)
    disk_set = set(fragments)

    if args.sources:
        allowed_sources = set(s.strip() for s in args.sources.split(',') if s.strip())
    else:
        allowed_sources = infer_sources(root)
    warn("info: allowed sources = %s" % sorted(allowed_sources))

    all_json = None
    if all_json_path:
        if not os.path.exists(all_json_path):
            die("error: --all-json not found: %s" % all_json_path)
        try:
            with open(all_json_path, 'r', encoding='utf-8') as fh:
                all_json = json.load(fh)
        except (OSError, ValueError) as exc:
            die("error: cannot parse all-json %s: %s" % (all_json_path, exc))

    hard_failures = []
    warnings = []
    checks = {}

    fm_result, fm_failures = check_frontmatter(root, fragments, allowed_sources)
    checks["frontmatter"] = fm_result
    if fm_failures:
        hard_failures.append("frontmatter: %d fragment(s) failed" % len(fm_failures))
    warn("check frontmatter: %d checked, %d failed" %
         (fm_result["checked"], len(fm_failures)))

    md_result, md_hard = check_manifest_disk(root, manifest, disk_set)
    checks["manifest_disk_reconcile"] = md_result
    if md_hard:
        hard_failures.append(
            "manifest_disk_reconcile: %d in_manifest_not_on_disk, %d on_disk_not_in_manifest"
            % (len(md_result["in_manifest_not_on_disk"]),
               len(md_result["on_disk_not_in_manifest"])))
    if md_result["duplicate_manifest_rows"]:
        warnings.append("manifest_disk_reconcile: %d duplicate manifest row(s)"
                        % len(md_result["duplicate_manifest_rows"]))
    warn("check manifest_disk_reconcile: %d manifest rows, %d disk fragments, "
         "%d missing, %d extra" %
         (md_result["manifest_rows"], md_result["disk_fragments"],
          len(md_result["in_manifest_not_on_disk"]),
          len(md_result["on_disk_not_in_manifest"])))

    link_result, link_unresolved = check_links(root, fragments, disk_set)
    checks["links"] = link_result
    if link_unresolved:
        hard_failures.append("links: %d unresolved internal link(s)"
                             % len(link_unresolved))
    warn("check links: %d links checked, %d unresolved" %
         (link_result["links_checked"], len(link_unresolved)))

    over_result, over = check_oversize(root, fragments, args.max_lines)
    checks["oversize"] = over_result
    if over:
        warnings.append("oversize: %d fragment(s) over %d lines"
                        % (len(over), args.max_lines))
    warn("check oversize: %d fragment(s) over %d lines" % (len(over), args.max_lines))

    if all_json is not None:
        cov_result, cov_gaps = check_coverage(all_json)
        checks["coverage"] = cov_result
        if cov_gaps:
            warnings.append("coverage: %d doc(s) with uncovered pages "
                            "(planning gaps or intentionally-skipped pages such as "
                            "blank/other-language pages; genuinely dropped fragments "
                            "are caught by manifest_disk_reconcile)" % len(cov_gaps))
        warn("check coverage: %d doc(s) with gaps (warning)" % len(cov_gaps))
    else:
        checks["coverage"] = {"skipped": "no --all-json available"}
        warn("check coverage: skipped (no _all.json)")

    ok = not hard_failures
    report = {
        "corpus_root": root,
        "manifest": manifest_path,
        "all_json": all_json_path,
        "checks": checks,
        "ok": ok,
        "hard_failures": hard_failures,
        "warnings": warnings,
    }
    print(json.dumps(report, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
