#!/usr/bin/env python3
"""Inject extracted figure images into corpus fragments (keep text + add image).

Reads <root>/_maps/figures.json ({ "<doc>/<file>.md": [ {num, caption, page,
image, ...} ] }) and, for each figure, inserts a markdown image link into the
owning fragment:
  - after the fragment's own '#### Figure N ...' heading if present, else
  - under a trailing '## Figures' section.
Idempotent: a figure already linked (by image path) is skipped, so re-running
after a re-extract is safe.

Usage: python3 inject_figures.py <corpus_root>
"""
import argparse, json, os, re, sys


def heading_pat(num):
    # a markdown heading line that references this figure number
    return re.compile(r'(?im)^(#{1,6})[ \t]+.*\bfig(?:ure|\.)?[ \t]*0*%d(?!\d).*$' % num)


def already_linked(text, image):
    return ('(%s)' % image) in text


def inject_one(text, fig):
    img = fig["image"]
    if already_linked(text, img):
        return text, "skip(exists)"
    alt = "%s (source p.%s)" % (fig["caption"].strip(), fig["page"])
    block = "\n![%s](%s)\n" % (alt, img)
    m = heading_pat(fig["num"]).search(text)
    if m:
        end = m.end()
        nl = text.find("\n", end)
        nl = len(text) if nl == -1 else nl
        return text[:nl] + "\n" + block + text[nl:], "heading"
    return None, "no-heading"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_root")
    args = ap.parse_args()
    root = os.path.abspath(args.corpus_root)
    figs = json.load(open(os.path.join(root, "_maps", "figures.json")))
    stats = {"heading": 0, "appended": 0, "skip(exists)": 0}
    for tf, items in sorted(figs.items()):
        path = os.path.join(root, tf)
        if not os.path.exists(path):
            print("warn: missing fragment %s" % tf, file=sys.stderr)
            continue
        text = open(path).read()
        appended = []
        for fig in sorted(items, key=lambda f: (f["num"], f["image"])):
            new, how = inject_one(text, fig)
            if how == "skip(exists)":
                stats["skip(exists)"] += 1
                continue
            if new is None:  # no heading -> collect for a Figures section
                if not already_linked(text, fig["image"]):
                    appended.append(fig)
                continue
            text = new
            stats["heading"] += 1
        if appended:
            sec = ["\n\n## Figures\n"]
            for fig in appended:
                # strip a leading "Figure N" from the caption so the label isn't doubled
                cap = re.sub(r'^\s*fig(?:ure|\.)?\s*\d+[:.\s-]*', '', fig["caption"].strip(), flags=re.I)
                sec.append("\n**Figure %s — %s** (source p.%s)\n\n![Figure %s](%s)\n"
                           % (fig["num"], cap, fig["page"], fig["num"], fig["image"]))
                stats["appended"] += 1
            text = text.rstrip() + "".join(sec)
        open(path, "w").write(text)
    print("injected: %d after headings, %d in Figures sections, %d already present"
          % (stats["heading"], stats["appended"], stats["skip(exists)"]), file=sys.stderr)


if __name__ == "__main__":
    main()
