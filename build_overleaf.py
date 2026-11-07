#!/usr/bin/env python3
# ==========================================================
# build_overleaf.py
#
# Assembles a self-contained ./latex/ folder ready to upload to
# Overleaf. It copies the manuscript + SI + bibliography and every
# figure they reference (preserving the outputs/figures/ subpath the
# .tex uses), so the project compiles as-is.
#
# Run whenever the paper or figures change, then upload ./latex/ to
# Overleaf (or drag its contents in):
#     python build_overleaf.py
#
# Location-independent: resolves paths to the project root, so it works
# from any working directory / either computer.
# ==========================================================

import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "latex")

# files that always go in the bundle (source .tex + bibliography)
DOCS = ["manuscript_nature_energy.tex",
        "supplementary_information.tex",
        "sn-bibliography.bib"]

INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")


def figures_referenced(tex_paths):
    figs = set()
    for tp in tex_paths:
        if not os.path.exists(tp):
            continue
        with open(tp, encoding="utf-8") as fh:
            for m in INCLUDE_RE.finditer(fh.read()):
                figs.add(m.group(1).strip())
    return sorted(figs)


def _safe_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        shutil.copy2(src, dst)          # copy contents + metadata
    except (PermissionError, OSError):
        # OneDrive-synced targets can reject metadata copy; fall back to
        # a plain content overwrite.
        with open(src, "rb") as a, open(dst, "wb") as b:
            b.write(a.read())


def main():
    # Overwrite in place (do NOT rmtree: OneDrive-synced files can't be
    # deleted from every environment). Stale figures no longer referenced
    # may linger -- harmless for Overleaf; delete by hand if you want a
    # perfectly clean folder.
    os.makedirs(OUT, exist_ok=True)

    # 1) copy the documents
    copied_docs = []
    for d in DOCS:
        src = os.path.join(ROOT, d)
        if os.path.exists(src):
            _safe_copy(src, os.path.join(OUT, d))
            copied_docs.append(d)
        else:
            print(f"  ! missing document: {d}")

    # 2) copy every referenced figure, preserving its relative subpath
    tex_paths = [os.path.join(ROOT, d) for d in DOCS if d.endswith(".tex")]
    figs = figures_referenced(tex_paths)
    ok, missing = [], []
    for rel in figs:
        # figure paths in the .tex may or may not carry an extension
        candidates = [rel] if os.path.splitext(rel)[1] else [rel + e for e in (".png", ".pdf", ".jpg")]
        found = None
        for c in candidates:
            src = os.path.join(ROOT, c)
            if os.path.exists(src):
                found = (c, src); break
        if found is None:
            missing.append(rel); continue
        relpath, src = found
        dst = os.path.join(OUT, relpath)
        _safe_copy(src, dst)
        ok.append(relpath)

    # 3) report
    print(f"\nOverleaf bundle written to: {OUT}")
    print(f"  documents copied : {', '.join(copied_docs)}")
    print(f"  figures copied   : {len(ok)}")
    for f in ok:
        print(f"      + {f}")
    if missing:
        print(f"  figures MISSING  : {len(missing)} (generate these before compiling)")
        for f in missing:
            print(f"      - {f}")
    print("\nAlso needed in Overleaf (once): sn-jnl.cls and the sn-*.bst template")
    print("files -- get them from Overleaf's 'Springer Nature LaTeX Template'.")
    print("Then upload the CONTENTS of ./latex/ to your Overleaf project.")


if __name__ == "__main__":
    main()
