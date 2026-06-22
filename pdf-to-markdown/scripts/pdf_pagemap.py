#!/usr/bin/env python3
"""Classify pages of a TEXT-LAYER multi-version / multilingual PDF.

Reads the *text layer* (via pypdf) page by page and labels each page by
language (A vs B) and version (redline vs final), then groups consecutive
like-labeled pages into regions. Within the region matching the configured
target language + version it pairs printed-page numbers (pulled from the
running header) with their PDF page index to derive a stable printed->PDF
offset and the target page range.

Reading rendered page images to find the offset mis-attributes pages
(headers blur, OCR drifts); doing it on the text layer is reliable.

Allowed deps: stdlib + pypdf only. Output: JSON to STDOUT, notes to STDERR.

Usage:
    python3 pdf_pagemap.py <pdf> [--config CONFIG.json]
"""

import argparse
import json
import re
import sys
from collections import Counter

# --- shared format constants -------------------------------------------------
# Printed-page-from-running-header: a number flanked by en-dashes or hyphens.
HEADER_RE = re.compile(r"[–\-]\s*(\d{1,3})\s*[–\-]")
# Generic Latin-language tiebreak: accented characters lean toward "language B"
# (e.g. French) over plain-ASCII English.
ACCENTS = "éèêàçâîôûïë"
HEADER_SCAN_CHARS = 600

DEFAULT_CONFIG = {
    "lang_a_markers": [],
    "lang_b_markers": [],
    "lang_a_name": "A",
    "lang_b_name": "B",
    "redline_sentinels": [],
    "final_sentinels": [],
    "target_lang": "a",
    "target_version": "any",
}


def log(msg):
    print(msg, file=sys.stderr)


def fail(msg, code=1):
    log("error: " + msg)
    sys.exit(code)


def load_config(path):
    cfg = dict(DEFAULT_CONFIG)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                user = json.load(fh)
        except OSError as exc:
            fail("cannot read config %r: %s" % (path, exc))
        except json.JSONDecodeError as exc:
            fail("config %r is not valid JSON: %s" % (path, exc))
        if not isinstance(user, dict):
            fail("config must be a JSON object")
        cfg.update(user)
    return cfg


def merge_flag_overrides(cfg, args):
    """Apply repeatable comma-separated CLI flags on top of --config."""
    def split(val):
        return [s.strip() for s in val.split(",") if s.strip()]

    if args.lang_a_markers:
        cfg["lang_a_markers"] = [m for v in args.lang_a_markers for m in split(v)]
    if args.lang_b_markers:
        cfg["lang_b_markers"] = [m for v in args.lang_b_markers for m in split(v)]
    if args.redline_sentinels:
        cfg["redline_sentinels"] = [m for v in args.redline_sentinels for m in split(v)]
    if args.final_sentinels:
        cfg["final_sentinels"] = [m for v in args.final_sentinels for m in split(v)]
    if args.lang_a_name:
        cfg["lang_a_name"] = args.lang_a_name
    if args.lang_b_name:
        cfg["lang_b_name"] = args.lang_b_name
    if args.target_lang:
        cfg["target_lang"] = args.target_lang
    if args.target_version:
        cfg["target_version"] = args.target_version
    return cfg


def count_markers(text, markers):
    return sum(text.count(m) for m in markers)


def classify_page(text, cfg):
    """Return (lang_token, version_token, a_markers, b_markers, accents)."""
    a = count_markers(text, cfg["lang_a_markers"])
    b = count_markers(text, cfg["lang_b_markers"])
    accents = sum(text.count(ch) for ch in ACCENTS)

    # Language: marker counts dominate; accents break ties / fill the gap when
    # no markers are configured.
    if a > b:
        lang = "a"
    elif b > a:
        lang = "b"
    else:
        # tie (often 0/0): lean on accent density.
        lang = "b" if accents >= 3 else "a"

    # Version: sentinel hits are sticky within the run (resolved later); per
    # page we only record a hit when a sentinel literally appears.
    version = None
    if count_markers(text, cfg["final_sentinels"]) > 0:
        version = "final"
    elif count_markers(text, cfg["redline_sentinels"]) > 0:
        version = "redline"

    return lang, version, a, b, accents


def printed_candidates(text):
    head = text[:HEADER_SCAN_CHARS]
    return [int(x) for x in HEADER_RE.findall(head)]


def propagate_version(rows):
    """Sentinels appear once per version block; carry the last seen forward."""
    current = None
    for row in rows:
        if row["version_hit"] is not None:
            current = row["version_hit"]
        row["version"] = current if current is not None else "any"


def build_rows(reader, cfg):
    rows = []
    text_lengths = []
    distinct_texts = set()
    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - pypdf edge cases
            log("warn: page %d text extraction failed: %s" % (idx, exc))
            text = ""
        text_lengths.append(len(text.strip()))
        distinct_texts.add(text.strip())
        lang, version_hit, a, b, accents = classify_page(text, cfg)
        cands = printed_candidates(text)
        flags = []
        if version_hit:
            flags.append("sentinel:" + version_hit)
        rows.append({
            "page": idx,
            "lang": lang,
            "printed_candidates": cands,
            "flags": flags,
            "a_markers": a,
            "b_markers": b,
            "accents": accents,
            "version_hit": version_hit,
        })
    propagate_version(rows)
    return rows, text_lengths, len(distinct_texts)


def group_regions(rows):
    regions = []
    for row in rows:
        key = (row["lang"], row["version"])
        if regions and (regions[-1]["lang"], regions[-1]["version"]) == key:
            regions[-1]["end"] = row["page"]
        else:
            regions.append({
                "lang": row["lang"],
                "version": row["version"],
                "start": row["page"],
                "end": row["page"],
            })
    return regions


def coalesce_target_region(regions, rows, target_lang, target_version):
    """Pick the region matching target lang+version. Tolerate stray 1-page
    flips by merging same-key regions that are separated only by tiny gaps."""
    def matches(r):
        lang_ok = (r["lang"] == target_lang)
        ver_ok = (target_version == "any" or r["version"] == target_version
                  or r["version"] == "any")
        return lang_ok and ver_ok

    candidates = [r for r in regions if matches(r)]
    if not candidates:
        return None
    # Choose the longest matching region as the spine, then extend it to absorb
    # immediately-adjacent matching regions (heals 1-page misclassifications).
    spine = max(candidates, key=lambda r: r["end"] - r["start"])
    start, end = spine["start"], spine["end"]
    changed = True
    while changed:
        changed = False
        for r in candidates:
            if r["start"] <= end + 3 and r["end"] >= start - 3:
                ns, ne = min(start, r["start"]), max(end, r["end"])
                if (ns, ne) != (start, end):
                    start, end = ns, ne
                    changed = True
    return {"lang": target_lang, "version": target_version,
            "start": start, "end": end}


def derive_offset(rows, region):
    """Pair each printed candidate in the region with its PDF page; the most
    consistent (modal) printed->PDF offset wins. offset = pdf_page - printed."""
    anchors = []
    offset_votes = Counter()
    for row in rows:
        if not (region["start"] <= row["page"] <= region["end"]):
            continue
        for printed in row["printed_candidates"]:
            offset = row["page"] - printed
            if offset < 0:
                continue  # printed page can't exceed pdf page
            offset_votes[offset] += 1
            anchors.append({"page": row["page"], "printed": printed,
                            "offset": offset})
    if not offset_votes:
        return None, anchors
    # Modal offset; tie-break toward the larger offset (front matter inflates
    # small spurious offsets from numbers like the "5" in a part number).
    best = max(offset_votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
    return best, anchors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", help="path to the text-layer PDF")
    ap.add_argument("--config", help="path to CONFIG.json")
    ap.add_argument("--lang-a-markers", action="append", dest="lang_a_markers",
                    help="comma-separated language-A marker phrases (repeatable)")
    ap.add_argument("--lang-b-markers", action="append", dest="lang_b_markers")
    ap.add_argument("--redline-sentinels", action="append", dest="redline_sentinels")
    ap.add_argument("--final-sentinels", action="append", dest="final_sentinels")
    ap.add_argument("--lang-a-name", dest="lang_a_name")
    ap.add_argument("--lang-b-name", dest="lang_b_name")
    ap.add_argument("--target-lang", dest="target_lang", choices=["a", "b"])
    ap.add_argument("--target-version", dest="target_version",
                    choices=["final", "redline", "any"])
    args = ap.parse_args(argv)

    cfg = merge_flag_overrides(load_config(args.config), args)

    try:
        import pypdf
    except ImportError:
        fail("pypdf is required but not importable")

    try:
        reader = pypdf.PdfReader(args.pdf)
        if reader.is_encrypted:
            try:
                if reader.decrypt("") == 0:
                    fail("PDF is encrypted and cannot be opened without a password")
            except Exception:
                fail("PDF is encrypted and cannot be opened without a password")
        npages = len(reader.pages)
    except FileNotFoundError:
        fail("file not found: %s" % args.pdf)
    except Exception as exc:
        fail("cannot open PDF %r: %s" % (args.pdf, exc))

    if npages == 0:
        fail("PDF has no pages")

    log("scanning %d pages of %s" % (npages, args.pdf))
    rows, text_lengths, unique_texts = build_rows(reader, cfg)

    # Scanned PDFs often carry a tiny repeated watermark/copyright text layer
    # but no real content. Detect "no usable text layer" via the median amount
    # of text per page plus how many pages share identical text: if most pages
    # are an identical short string (the watermark), there is nothing to map.
    sorted_lengths = sorted(text_lengths)
    median_len = sorted_lengths[len(sorted_lengths) // 2] if sorted_lengths else 0
    if median_len < 200 or (npages >= 5 and unique_texts <= 2):
        fail("no usable text layer found (scanned/image PDF?); use OCR instead")

    regions = group_regions(rows)
    target = coalesce_target_region(regions, rows,
                                    cfg["target_lang"], cfg["target_version"])

    suggested_offset = None
    suggested_target_range = None
    anchors = []
    if target:
        suggested_offset, anchors = derive_offset(rows, target)
        suggested_target_range = [target["start"], target["end"]]
        log("target region %s/%s -> pdf %d-%d, offset %s" % (
            target["lang"], target["version"], target["start"], target["end"],
            suggested_offset))
    else:
        log("warn: no region matched target_lang=%s target_version=%s" % (
            cfg["target_lang"], cfg["target_version"]))

    # strip internal helper field from emitted rows
    out_rows = [{k: v for k, v in r.items() if k != "version_hit"} for r in rows]
    # re-attach version to each row's flags for visibility
    for orow, row in zip(out_rows, rows):
        orow["version"] = row["version"]

    result = {
        "pdf": args.pdf,
        "pages": npages,
        "config_used": cfg,
        "rows": out_rows,
        "derived": {
            "regions": regions,
            "anchors": anchors,
            "suggested_offset": suggested_offset,
            "suggested_target_range": suggested_target_range,
        },
    }
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
