#!/usr/bin/env python3
"""Triage a single PDF for the pdf-to-markdown pipeline.

Reports page count, file size, a text-layer verdict (born-digital / scanned /
mixed), a flattened outline, and which helper tools are available. All machine
output is JSON on stdout; human-readable progress and warnings go to stderr.

Usage:
    python3 pdf_probe.py <pdf>

Dependencies: Python standard library + pypdf. Optionally cross-checks the page
count against the poppler `pdfinfo` CLI when present.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


def log(msg):
    """Print a human-readable progress/warning line to stderr."""
    print(msg, file=sys.stderr)


def detect_tools():
    """Return a bool map of available CLIs and the pypdf import."""
    tools = {
        "pdftotext": shutil.which("pdftotext") is not None,
        "pdfinfo": shutil.which("pdfinfo") is not None,
        "pdftoppm": shutil.which("pdftoppm") is not None,
        "pdfimages": shutil.which("pdfimages") is not None,
        "pypdf": False,
    }
    try:
        import pypdf  # noqa: F401

        tools["pypdf"] = True
    except Exception:
        tools["pypdf"] = False
    return tools


def pdfinfo_pages(pdf_path):
    """Return the page count reported by pdfinfo, or None if unavailable."""
    if shutil.which("pdfinfo") is None:
        return None
    try:
        out = subprocess.run(
            ["pdfinfo", pdf_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    for line in out.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def sample_indices(num_pages):
    """Pick page indices to sample: all if <=60, else a uniform stride of ~50."""
    if num_pages <= 0:
        return []
    if num_pages <= 60:
        return list(range(num_pages))
    stride = max(1, num_pages // 50)
    return list(range(0, num_pages, stride))


def _norm(text):
    """Collapse whitespace for comparison/counting."""
    return re.sub(r"\s+", "", text or "")


def detect_watermark(page_texts):
    """Detect a per-page boilerplate watermark shared across (nearly) all pages.

    Scanned PDFs are frequently distributed with a licensing/copyright stamp
    pressed onto every page as a thin text layer over image content. Such a
    stamp would otherwise be mistaken for a real text layer. Return the set of
    repeated normalized lines that appear on a strong majority of pages.
    """
    if len(page_texts) < 3:
        return set()
    from collections import Counter

    counts = Counter()
    for txt in page_texts:
        seen = set()
        for line in (txt or "").splitlines():
            norm = _norm(line)
            if len(norm) >= 8:
                seen.add(norm)
        for norm in seen:
            counts[norm] += 1
    threshold = max(3, int(0.8 * len(page_texts)))
    return {line for line, c in counts.items() if c >= threshold}


def assess_text_layer(reader, num_pages):
    """Sample pages and classify the PDF's text layer.

    A page "has text" if it yields > 20 non-whitespace chars AFTER removing any
    repeated per-page watermark/boilerplate lines, so a license stamp on every
    page of a scan does not masquerade as a real text layer.
    """
    indices = sample_indices(num_pages)
    pages_sampled = len(indices)
    page_texts = []
    for i in indices:
        try:
            page_texts.append(reader.pages[i].extract_text() or "")
        except Exception:
            page_texts.append("")

    watermark = detect_watermark(page_texts)
    if watermark:
        log(f"detected per-page boilerplate watermark ({len(watermark)} line(s))")

    pages_with_text = 0
    chars_total = 0
    for txt in page_texts:
        kept_lines = [
            ln for ln in txt.splitlines() if _norm(ln) not in watermark
        ]
        nonws = _norm("\n".join(kept_lines))
        chars_total += len(nonws)
        if len(nonws) > 20:
            pages_with_text += 1
    fraction = (pages_with_text / pages_sampled) if pages_sampled else 0.0
    if fraction >= 0.85:
        verdict = "born-digital"
    elif fraction <= 0.15:
        verdict = "scanned"
    else:
        verdict = "mixed"
    return {
        "pages_sampled": pages_sampled,
        "pages_with_text": pages_with_text,
        "fraction_with_text": round(fraction, 4),
        "chars_total": chars_total,
        "verdict": verdict,
    }


def flatten_outline(reader):
    """Flatten reader.outline recursively into {level, title, page} entries.

    Tolerates broken/partial outlines: any destination that cannot be resolved
    to a page is skipped rather than raising.
    """
    entries = []

    def walk(node, level):
        # pypdf yields nested lists for sub-outlines and Destination objects
        # for leaves.
        if isinstance(node, list):
            for child in node:
                walk(child, level + 1 if not isinstance(child, list) else level)
            return
        title = None
        try:
            title = node.title
        except Exception:
            title = None
        if title is None:
            try:
                title = node.get("/Title")
            except Exception:
                title = None
        page = None
        try:
            page_index = reader.get_destination_page_number(node)
            if page_index is not None and page_index >= 0:
                page = page_index + 1  # 1-based
        except Exception:
            page = None
        if title is not None:
            entries.append(
                {"level": level, "title": str(title), "page": page}
            )

    try:
        outline = reader.outline
    except Exception as exc:
        log(f"warning: could not read outline: {exc}")
        return []

    if not outline:
        return []

    # Top-level outline is a list; its direct leaf children are level 1.
    try:
        for item in outline:
            walk(item, 1 if not isinstance(item, list) else 0)
    except Exception as exc:
        log(f"warning: partial outline traversal failed: {exc}")
    return entries


def probe(pdf_path):
    """Build the full probe result dict for one PDF."""
    tools = detect_tools()
    result = {
        "pdf": pdf_path,
        "exists": os.path.isfile(pdf_path),
        "pages": None,
        "size_bytes": None,
        "text_layer": {
            "pages_sampled": 0,
            "pages_with_text": 0,
            "fraction_with_text": 0.0,
            "chars_total": 0,
            "verdict": "unknown",
        },
        "outline": [],
        "tools": tools,
    }

    if not result["exists"]:
        return result, "missing"

    try:
        result["size_bytes"] = os.path.getsize(pdf_path)
    except OSError:
        result["size_bytes"] = None

    if not tools["pypdf"]:
        return result, "no-pypdf"

    import pypdf
    from pypdf.errors import PdfReadError

    try:
        reader = pypdf.PdfReader(pdf_path)
        if reader.is_encrypted:
            # Attempt empty-password decrypt; many specs are lightly encrypted.
            try:
                reader.decrypt("")
            except Exception:
                pass
        num_pages = len(reader.pages)
    except (PdfReadError, OSError, ValueError) as exc:
        log(f"error: cannot read PDF with pypdf: {exc}")
        return result, "unreadable"
    except Exception as exc:
        log(f"error: unexpected failure reading PDF: {exc}")
        return result, "unreadable"

    result["pages"] = num_pages

    info_pages = pdfinfo_pages(pdf_path)
    if info_pages is not None and info_pages != num_pages:
        log(
            f"warning: page-count mismatch pypdf={num_pages} "
            f"pdfinfo={info_pages}"
        )

    log(f"sampling text layer over {num_pages} pages...")
    result["text_layer"] = assess_text_layer(reader, num_pages)
    result["outline"] = flatten_outline(reader)
    log(
        f"verdict={result['text_layer']['verdict']} "
        f"outline_entries={len(result['outline'])}"
    )
    return result, "ok"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Triage a PDF: pages, text-layer verdict, outline, tools."
    )
    parser.add_argument("pdf", help="path to the PDF file")
    args = parser.parse_args(argv)

    result, status = probe(args.pdf)
    print(json.dumps(result, indent=2))

    if status == "missing":
        log(f"error: file not found: {args.pdf}")
        return 2
    if status == "no-pypdf":
        log("error: pypdf is not importable; cannot analyze PDF")
        return 3
    if status == "unreadable":
        log("error: PDF is encrypted or corrupt and could not be parsed")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
