#!/usr/bin/env python3
"""Extract figure images from born-digital PDFs and map them to corpus fragments.

For each document in <root>/_maps/_all.json, scan its target page range, detect
'Figure N ...' captions, compute each figure's bounding box from the page's
vector drawings (+ raster image blocks) in the band above the caption, render a
high-DPI clip, trim whitespace, and save to <root>/<doc>/figures/figure-NN.png.

Emits <root>/_maps/figures.json: { "<doc>/<file>.md": [ {num, caption, page,
image, width, height} ] } keyed by owning fragment, for the injection step.

Caption-anchored + vector-bbox based, so it works on VECTOR diagrams (state
machines, wiring, sequence/stack figures) that pdfimages cannot extract.
A 'Figure N' line with no vector/image region above it (an in-text reference,
not a caption) is skipped.

deps: pymupdf, pillow
"""
import argparse, json, os, re, sys
import fitz
import numpy as np
from PIL import Image, ImageChops

CAP_RE = re.compile(r'^(?:figure|fig\.?)\s+(\d+)\b', re.I)
DPI = 200
ZOOM = DPI / 72.0
MARGIN_SIDE = 6      # pts left/right of the vector bbox
MARGIN_TOP = 2       # pts above (the vector bbox top IS the figure top; keep tiny)
HEADER = 55          # pts: ignore the running header/footer band
MIN_FIG_AREA = 1500  # pts^2: ignore tiny stray vector specks


def parse_pages(spec):
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
            pages.update(range(min(a, b), max(a, b) + 1))
            continue
        m = re.match(r'^(\d+)$', chunk)
        if m:
            pages.add(int(m.group(1)))
    return pages


def captions_on_page(page):
    """Detect 'Figure N ...' captions at the word level. Each 'Figure N' is an
    anchor; its title is the same-baseline words from the anchor up to the next
    anchor on that baseline. This handles a title split across blocks, two
    captions sharing a baseline (side-by-side figures), and left-margin line
    numbers (they sit left of the anchor and are excluded)."""
    ph = page.rect.height
    ws = sorted(page.get_text("words"), key=lambda w: (round(w[1]), w[0]))  # (x0,y0,x1,y1,word,...)
    anchors = []
    for i, w in enumerate(ws):
        if not re.match(r'^(?:figure|fig\.?)$', w[4], re.I):
            continue
        wcy = (w[1] + w[3]) / 2
        for j in range(i + 1, min(i + 3, len(ws))):
            nx = ws[j]
            if nx[0] < w[0] or abs((nx[1] + nx[3]) / 2 - wcy) > 3:
                continue
            m = re.match(r'^(\d+)', nx[4])
            if m and HEADER <= w[1] <= ph - HEADER:
                anchors.append((int(m.group(1)), w[0], w[1], w[3]))
            break
    out = []
    for (num, ax0, ay0, ay1) in anchors:
        acy = (ay0 + ay1) / 2
        nxt = min([a[1] for a in anchors if abs((a[2] + a[3]) / 2 - acy) <= 3 and a[1] > ax0],
                  default=1e9)
        sel = [w for w in ws if abs((w[1] + w[3]) / 2 - acy) <= 3 and ax0 - 1 <= w[0] < nxt]
        if not sel:
            continue
        sel.sort(key=lambda w: w[0])
        text = re.sub(r'\s+', ' ', " ".join(w[4] for w in sel)).strip()
        rect = fitz.Rect(min(w[0] for w in sel), min(w[1] for w in sel),
                         max(w[2] for w in sel), max(w[3] for w in sel))
        out.append((num, text, rect))
    out.sort(key=lambda t: t[2].y0)
    return out


SEG_DPI = 150            # render DPI for the whitespace-segmentation pass
INK = 205                # grayscale < INK counts as ink
WHITE_GAP_PT = 9         # a horizontal whitespace band >= this (pts) splits blocks
MERGE_GAP_PT = 26        # merge a higher block into the figure across a gap up to
                         # this, but ONLY if that block is diagram-like (see below)
MIN_BLOCK_PT = 12        # ignore inked blocks shorter than this (pts)


def figure_region(page, caption_rect, upper_bound, xlo, xhi):
    """Find the figure as the inked block immediately above the caption, using
    pixel whitespace segmentation of the band [xlo,xhi] x [upper,caption].
    A table/paragraph above the diagram is a separate block (whitespace gap);
    the diagram stays whole because its connector arrows keep each scanline
    inked. Returns a fitz.Rect (PDF points) or None."""
    band_top = max(upper_bound, HEADER)
    band = fitz.Rect(xlo, band_top, xhi, caption_rect.y0) & page.rect
    if band.height < MIN_BLOCK_PT or band.width < 8:
        return None
    z = SEG_DPI / 72.0
    pix = page.get_pixmap(clip=band, matrix=fitz.Matrix(z, z), colorspace=fitz.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)[:, :pix.width]
    row_ink = (img < INK).sum(axis=1)
    inked = row_ink > 2
    gap_px = max(1, int(WHITE_GAP_PT * z))
    # segment into blocks of inked rows, merging white gaps shorter than gap_px
    blocks, start, end, gap = [], None, None, 0
    for i, v in enumerate(inked):
        if v:
            if start is None:
                start = i
            end = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap > gap_px:
                blocks.append((start, end))
                start = None
    if start is not None:
        blocks.append((start, end))
    blocks = [b for b in blocks if (b[1] - b[0]) / z >= MIN_BLOCK_PT]
    if not blocks:
        return None

    def block_xspan(b):
        cols = np.where((img[b[0]:b[1] + 1] < INK).sum(axis=0) > 1)[0]
        if not len(cols):
            return band.x0, band.x1
        return band.x0 + cols[0] / z, band.x0 + (cols[-1] + 1) / z

    def has_vectors(b):  # any vector path within this block's y-range
        y0, y1 = band.y0 + b[0] / z, band.y0 + b[1] / z
        for dr in page.get_drawings():
            r = dr["rect"]
            if max(r.width, r.height) > 3 and y0 - 2 <= (r.y0 + r.y1) / 2 <= y1 + 2 and xlo <= (r.x0 + r.x1) / 2 <= xhi:
                return True
        return False

    # seed with the lowest inked block (just above the caption); merge higher
    # blocks ONLY if they are diagram-like (narrow + graphics-bearing) and close,
    # so a state diagram's detached top (ENTRY) is recovered but a full-width
    # table/paragraph above the figure is not.
    i = len(blocks) - 1
    s, e = blocks[i]
    while i > 0:
        above = blocks[i - 1]
        gap_pt = (s - above[1]) / z
        ax0, ax1 = block_xspan(above)
        narrow = (ax1 - ax0) < 0.80 * (xhi - xlo)
        if gap_pt <= MERGE_GAP_PT and narrow and has_vectors(above):
            s = above[0]
            i -= 1
        else:
            break
    cols = np.where((img[s:e + 1] < INK).sum(axis=0) > 1)[0]
    x0 = band.x0 + (cols[0] / z if len(cols) else 0)
    x1 = band.x0 + ((cols[-1] + 1) / z if len(cols) else band.width)
    region = fitz.Rect(x0, band.y0 + s / z, x1, band.y0 + (e + 1) / z)
    if region.width * region.height < MIN_FIG_AREA:
        return None
    # real-figure guards (reject in-text "Figure N" references):
    # 1) the region must contain actual graphics (vector paths or a raster image),
    #    not just a block of body text.
    ndraw = 0
    for dr in page.get_drawings():
        r = dr["rect"]
        if max(r.width, r.height) > 3:
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            if region.x0 <= cx <= region.x1 and region.y0 <= cy <= region.y1:
                ndraw += 1
    has_img = any(b.get("type") == 1 and fitz.Rect(b["bbox"]).intersects(region)
                  for b in page.get_text("dict")["blocks"])
    if ndraw < 1 and not has_img:
        return None
    # 2) a real caption is centered under its figure; an in-text reference is not.
    cap_c = (caption_rect.x0 + caption_rect.x1) / 2
    reg_c = (region.x0 + region.x1) / 2
    if abs(cap_c - reg_c) > 0.30 * region.width + 12:
        return None
    return region


def trim(path):
    im = Image.open(path).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        pad = 8
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad))
        im = im.crop(bbox)
        im.save(path)
    return im.size


def heading_y(page, clause):
    """y0 of the line that starts this fragment's section heading on the page,
    or None if the section doesn't start on this page."""
    if re.match(r'^[\d.]+$', clause):
        pat = re.compile(r'^' + re.escape(clause) + r'(?:\D|$)')
    else:  # 'Annex A', 'Appendix B', ...
        pat = re.compile(r'^' + re.escape(clause) + r'\b', re.I)
    best = None
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if pat.match(text):
                y = line["bbox"][1]
                if best is None or y < best:
                    best = y
    return best


def owning_fragment(page, page_no, frag_meta, y_fig):
    """Assign a figure at vertical position y_fig to the fragment whose section
    is active there: the nearest section heading ABOVE the figure on this page;
    if the figure is above every heading on the page, the section carried over
    from the previous page (largest start < page_no)."""
    cands = [(start, tf, clause) for (tf, (start, pgset, clause)) in frag_meta.items()
             if page_no in pgset]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0][1]
    headings = []
    for start, tf, clause in cands:
        hy = heading_y(page, clause)
        if hy is not None:
            headings.append((hy, tf))
    above = [(hy, tf) for (hy, tf) in headings if hy <= y_fig]
    if above:
        return max(above, key=lambda t: t[0])[1]
    carried = [(start, tf) for (start, tf, _) in cands if start < page_no]
    if carried:
        return max(carried)[1]
    return min(cands)[1]


def main():
    ap = argparse.ArgumentParser(description="Extract + map PDF figures for a markdown corpus.")
    ap.add_argument("corpus_root")
    ap.add_argument("--all-json", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.corpus_root)
    all_json = args.all_json or os.path.join(root, "_maps", "_all.json")
    plan = json.load(open(all_json))
    doc_meta = plan["docMeta"]
    frags = plan["fragments"]
    # optional denylist of bad extractions (verified by the figure-verify pass),
    # as "<doc>/figures/figure-NN.png" relative paths — skipped on re-run.
    deny_path = os.path.join(root, "_maps", "figures_deny.json")
    deny = set(json.load(open(deny_path))) if os.path.exists(deny_path) else set()

    by_doc = {}
    for f in frags:
        by_doc.setdefault(f["doc"], []).append(f)

    result = {}
    total = 0
    multi = []
    for doc, dm in doc_meta.items():
        pdf_path = dm.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"warn: missing pdf for {doc}: {pdf_path}", file=sys.stderr)
            continue
        figdir = os.path.join(root, doc, "figures")
        os.makedirs(figdir, exist_ok=True)
        # page -> fragment index (start, pageset, clause)
        frag_meta = {}
        for f in by_doc.get(doc, []):
            pg = parse_pages(f["pdf_pages"])
            if pg:
                frag_meta[f["target_file"]] = (min(pg), pg, str(f.get("clause", "")))
        target = parse_pages(dm.get("target_pages")) or set(
            p for (_, pgset, _) in frag_meta.values() for p in pgset)
        doc_obj = fitz.open(pdf_path)
        seen_nums = {}
        for page_no in sorted(target):
            page = doc_obj[page_no - 1]
            caps = captions_on_page(page)
            for i, (num, text, crect) in enumerate(caps):
                # upper bound = nearest caption strictly above this one (side-by-side
                # captions share the same band; they don't bound each other)
                above = [c[2].y1 for c in caps if c[2].y1 <= crect.y0 - 5]
                upper = max(above) if above else HEADER
                # x-bounds: split the gutter to any sibling caption on a nearby baseline
                sib_l = [c[2].x1 for c in caps if abs(c[2].y0 - crect.y0) < 15 and c[2].x1 <= crect.x0]
                sib_r = [c[2].x0 for c in caps if abs(c[2].y0 - crect.y0) < 15 and c[2].x0 >= crect.x1]
                xlo = (max(sib_l) + crect.x0) / 2 if sib_l else page.rect.x0
                xhi = (min(sib_r) + crect.x1) / 2 if sib_r else page.rect.x1
                bbox = figure_region(page, crect, upper, xlo, xhi)
                if bbox is None:
                    continue  # in-text reference, not a real caption
                suffix = ""
                if num in seen_nums:
                    seen_nums[num] += 1
                    suffix = chr(ord('a') + seen_nums[num] - 1)
                else:
                    seen_nums[num] = 1
                name = f"figure-{num:02d}{suffix}.png"
                if f"{doc}/figures/{name}" in deny:
                    continue  # verified bad extraction — skip
                outp = os.path.join(figdir, name)
                # include the caption's full x-extent so a wide/left-hanging
                # caption isn't clipped (caption sits below the figure bbox).
                x0 = max(min(bbox.x0, crect.x0) - MARGIN_SIDE, xlo - MARGIN_SIDE)
                x1 = min(max(bbox.x1, crect.x1) + MARGIN_SIDE, xhi + MARGIN_SIDE)
                clip = fitz.Rect(x0, bbox.y0 - MARGIN_TOP, x1, crect.y1 + 2) & page.rect
                pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(ZOOM, ZOOM))
                pix.save(outp)
                w, h = trim(outp)
                tf = owning_fragment(page, page_no, frag_meta, bbox.y0)
                if tf is None:
                    print(f"warn: no fragment owns {doc} p{page_no} Figure {num}", file=sys.stderr)
                    continue
                cand_count = sum(1 for (_, (_, pg, _)) in frag_meta.items() if page_no in pg)
                if cand_count > 1:
                    multi.append(f"{doc} p{page_no} Fig {num} -> {tf} ({cand_count} candidates)")
                result.setdefault(tf, []).append({
                    "num": num, "caption": text, "page": page_no,
                    "image": f"figures/{name}", "width": w, "height": h,
                })
                total += 1
        doc_obj.close()

    out = os.path.join(root, "_maps", "figures.json")
    json.dump(result, open(out, "w"), indent=2)
    print(f"extracted {total} figures across {len(result)} fragments -> {out}", file=sys.stderr)
    by_d = {}
    for tf in result:
        by_d[tf.split('/')[0]] = by_d.get(tf.split('/')[0], 0) + len(result[tf])
    for d in sorted(by_d):
        print(f"  {d}: {by_d[d]} figures", file=sys.stderr)
    if multi:
        print("multi-candidate page assignments (verify):", file=sys.stderr)
        for m in multi:
            print("  " + m, file=sys.stderr)


if __name__ == "__main__":
    main()
