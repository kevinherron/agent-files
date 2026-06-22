#!/usr/bin/env python3
"""Build an outline-driven fragment plan (page-range windows) for a large PDF.

Reads a pdf_probe.py JSON (which carries the PDF's embedded outline) and emits a
map plan at <root>/_maps/<doc>.json: a list of fragments, each a page-range
WINDOW small enough for one convert agent to read in <=2 Read calls. Sections
come from the outline's top- and second-level nodes (section numbers parsed from
the bookmark titles, e.g. "12.5.2" or "A.1"); a section larger than --window
pages is sub-tiled into a/b/c windows with a 1-page overlap so a heading or table
straddling a window boundary is seen whole by at least one agent.

It then reports page-COVERAGE over the body range: every body page should be
covered by some window (overlaps expected). A gap means the plan would drop
pages -- fix it before converting.

This is the scale path from references/scaling.md: outline -> windows. For a PDF
with no usable outline, fall back to a TOC-reader agent or fixed page-window
tiling (see scaling.md). Stdlib only.

Usage:
  python3 plan_from_outline.py <probe.json> --doc <id> --root <dir> [options]
Options:
  --window N        max pages per window (default 12; a Read caps at 20)
  --overlap N       page overlap between adjacent windows of one section (default 1)
  --body-start N    first body PDF page (default: first top-level numeric clause)
  --body-end N      last body PDF page (default: total pages)
  --clause-filter S comma-separated top-level clause heads to keep (e.g. "13,14")
  --out PATH        output path (default <root>/_maps/<doc>.json)
"""

import argparse
import json
import os
import re
import sys


def warn(msg):
    print(msg, file=sys.stderr)


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def slugify(title, maxlen=56):
    # Drop a leading section number ("12.5.2 ", "A.1 ", "Annex A - ").
    t = re.sub(r'^\s*Annex\s+[A-Z]+\s*[-–:]?\s*', '', title, flags=re.I)
    t = re.sub(r'^\s*[0-9A-Z]+(?:\.[0-9]+)*\s*[-–:.]?\s*', '', t)
    t = t.lower()
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return (t[:maxlen].rstrip('-')) or 'section'


def parse_secnum(title):
    """Parse a leading section number into a tuple of components.

    "12.5.2 Foo" -> ('12','5','2'); "A.1 Bar" -> ('A','1');
    "Annex A - X" -> ('A',); "1 PURPOSE" -> ('1',). None if unparseable.
    """
    t = re.sub(r'^\s*Annex\s+', '', title.strip(), flags=re.I)
    m = re.match(r'^([0-9]+|[A-Z])((?:\.[0-9]+)*)', t)
    if not m:
        return None
    parts = [m.group(1)] + [p for p in m.group(2).split('.') if p]
    return tuple(parts)


def is_numeric_top(secnum):
    return secnum is not None and len(secnum) == 1 and secnum[0].isdigit()


def windows_for(s, e, window, overlap):
    """Tile [s, e] (inclusive pages) into windows of <= `window` pages with
    `overlap` shared pages between neighbours. Returns list of (ws, we)."""
    if e <= s:
        return [(s, max(s, e))]
    out = []
    step = max(1, window - overlap)
    start = s
    while start <= e:
        end = min(e, start + window - 1)
        out.append((start, end))
        if end >= e:
            break
        start = end - overlap + 1
    return out


def section_windows(s, e, child_starts, window, overlap):
    """Tile [s, e] into windows that END on child-section boundaries, so a
    subsection is never split across two windows. A single child larger than
    `window` is page-tiled as a fallback. A 1-page overlap is applied to
    interior windows to catch a table straddling a boundary."""
    bounds = sorted(p for p in set(child_starts) if s < p <= e)
    if (e - s + 1) <= window or not bounds:
        return windows_for(s, e, window, overlap)
    sentinels = bounds + [e + 1]
    wins = []
    seg = s
    while seg <= e:
        best = None
        for b in sentinels:
            if b <= seg:
                continue
            if (b - 1) - seg + 1 <= window:
                best = b  # window [seg, b-1] still fits; keep extending
            else:
                break
        if best is None:
            # The first child after seg is itself larger than `window`; take it
            # whole as one (oversized) window -- page-tiled below.
            nb = next(b for b in sentinels if b > seg)
            wins.append((seg, min(e, nb - 1)))
            seg = nb
        else:
            wins.append((seg, min(e, best - 1)))
            seg = best
    # 1-page overlap on interior windows.
    overlapped = []
    for idx, (ws, we) in enumerate(wins):
        nws = ws if idx == 0 else max(s, ws - overlap)
        overlapped.append((nws, we))
    # Page-tile any window still larger than `window` (an oversized single child).
    final = []
    for (ws, we) in overlapped:
        if we - ws + 1 > window:
            final.extend(windows_for(ws, we, window, overlap))
        else:
            final.append((ws, we))
    return final


def main():
    ap = argparse.ArgumentParser(description="Outline-driven fragment plan for a large PDF.")
    ap.add_argument("probe_json", help="pdf_probe.py JSON output (has the outline)")
    ap.add_argument("--doc", required=True, help="short document id (subdir name)")
    ap.add_argument("--root", required=True, help="corpus output root")
    ap.add_argument("--window", type=int, default=12, help="max pages per window")
    ap.add_argument("--overlap", type=int, default=1, help="page overlap between windows")
    ap.add_argument("--body-start", type=int, default=None)
    ap.add_argument("--body-end", type=int, default=None)
    ap.add_argument("--clause-filter", default=None,
                    help="comma-separated top-level clause heads to keep, e.g. '13,14'")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    try:
        with open(args.probe_json, 'r', encoding='utf-8') as fh:
            probe = json.load(fh)
    except (OSError, ValueError) as exc:
        die("error: cannot read probe json: %s" % exc)

    total_pages = probe.get('pages') or 0
    outline = probe.get('outline') or []
    pdf_file = os.path.basename(probe.get('pdf', '')) or None

    # Outline entries with a real page and a parseable section number, in
    # document (reading) order.
    entries = []
    for o in outline:
        pg = o.get('page')
        if not pg:
            continue
        sec = parse_secnum(o.get('title') or '')
        if sec is None:
            continue
        entries.append({'sec': sec, 'page': int(pg), 'title': (o.get('title') or '').strip()})
    if not entries:
        die("error: no parseable numbered outline entries found")

    # Body range.
    numeric_tops = [e['page'] for e in entries if is_numeric_top(e['sec'])]
    body_start = args.body_start or (min(numeric_tops) if numeric_tops else min(e['page'] for e in entries))
    body_end = args.body_end or total_pages or max(e['page'] for e in entries)

    # Units = top/second-level sections within the body, in reading order.
    keep_heads = None
    if args.clause_filter:
        keep_heads = set(s.strip() for s in args.clause_filter.split(',') if s.strip())
    units = []
    for e in entries:
        if len(e['sec']) > 2:
            continue
        if e['page'] < body_start or e['page'] > body_end:
            continue
        if keep_heads is not None and e['sec'][0] not in keep_heads:
            continue
        units.append(e)
    # Stable sort by page (outline is already reading-ordered; this guards
    # against minor non-monotonicity).
    units.sort(key=lambda u: u['page'])
    if not units:
        die("error: no section units in body range (check --body-start/--clause-filter)")

    # To bound each unit's end we need the NEXT unit-or-deeper boundary in the
    # whole body, not just within a clause filter -- otherwise a filtered unit
    # would stretch to body_end. Use all depth<=2 entries (unfiltered) sorted by
    # page as the boundary set.
    boundaries = sorted(
        (e['page'] for e in entries if len(e['sec']) <= 2 and body_start <= e['page'] <= body_end),
        )

    def next_boundary(after_page):
        nb = None
        for p in boundaries:
            if p > after_page:
                nb = p
                break
        return nb

    # Child-section start pages per parent section, for boundary-aligned windows.
    children = {}
    for en in entries:
        if len(en['sec']) >= 2:
            children.setdefault(en['sec'][:-1], []).append(en['page'])
    for k in children:
        children[k] = sorted(children[k])

    fragments = []
    for u in units:
        s = u['page']
        nb = next_boundary(s)
        e = (nb - 1) if nb else body_end
        e = min(max(s, e), body_end)
        secstr = '.'.join(u['sec'])
        child_starts = [p for p in children.get(tuple(u['sec']), []) if s < p <= e]
        wins = section_windows(s, e, child_starts, args.window, args.overlap)
        multi = len(wins) > 1
        for i, (ws, we) in enumerate(wins):
            suffix = chr(ord('a') + i) if multi else ''
            pdf_pages = ("%d-%d" % (ws, we)) if we > ws else ("%d" % ws)
            fragments.append({
                "clause": secstr,
                "title": u['title'],
                "pdf_pages": pdf_pages,
                "target_file": "%s/%s%s-%s.md" % (args.doc, secstr, suffix, slugify(u['title'])),
                "kind": "clause",
                "parent_section": secstr,
                "est_pages": we - ws + 1,
                "prev_end": (wins[i - 1][1] if i > 0 else None),
            })

    # Coverage over the body range.
    covered = set()
    overlaps = 0
    for f in fragments:
        m = re.match(r'^(\d+)(?:-(\d+))?$', f['pdf_pages'])
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
        for p in range(a, b + 1):
            if p in covered:
                overlaps += 1
            covered.add(p)
    body = set(range(body_start, body_end + 1))
    uncovered = sorted(body - covered)

    plan = {
        "doc": args.doc,
        "pdf_file": pdf_file,
        "total_pdf_pages": total_pages,
        "target_pdf_range": [body_start, body_end],
        "printed_to_pdf_offset": "n/a (outline pages are PDF pages; born-digital)",
        "structure_notes": "Outline-driven windows (top/second-level sections; window=%d overlap=%d)." % (args.window, args.overlap),
        "fragments": fragments,
    }
    out_path = args.out or os.path.join(args.root, "_maps", "%s.json" % args.doc)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(plan, fh, indent=1, ensure_ascii=False)

    # Per-clause fragment counts.
    from collections import Counter
    per_clause = Counter(f['clause'].split('.')[0] for f in fragments)
    warn("wrote %s" % out_path)
    warn("body range: PDF %d-%d (%d pages)" % (body_start, body_end, len(body)))
    warn("units: %d | fragments(windows): %d | overlap-pages: %d" % (len(units), len(fragments), overlaps))
    warn("coverage: %d/%d body pages covered (%.1f%%); %d uncovered" %
         (len(covered & body), len(body), 100.0 * len(covered & body) / max(1, len(body)), len(uncovered)))
    if uncovered:
        warn("  first uncovered pages: %s%s" % (uncovered[:20], " ..." if len(uncovered) > 20 else ""))
    warn("fragments per top-level clause: %s" % dict(sorted(per_clause.items(), key=lambda kv: (len(kv[0]), kv[0]))))

    print(json.dumps({
        "out": out_path,
        "body_range": [body_start, body_end],
        "units": len(units),
        "fragments": len(fragments),
        "coverage_pct": round(100.0 * len(covered & body) / max(1, len(body)), 2),
        "uncovered_count": len(uncovered),
        "uncovered_sample": uncovered[:20],
    }, indent=2))


if __name__ == "__main__":
    main()
