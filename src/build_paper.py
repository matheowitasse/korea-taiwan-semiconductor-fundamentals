"""Build the paper PDF from LaTeX (MiKTeX) and copy it to paper/Witasse_Korea_Taiwan_semiconductors.pdf.

Syncs paper/figures/ into paper/latex/figures/, runs pdflatex -> bibtex -> pdflatex -> pdflatex (which resolves
citations and cross-references), checks the bibliography survived, and rebuilds paper/overleaf.zip.
`latexmk` is not used because it needs Perl, which is not installed here.

Usage:  python src/build_paper.py
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEX = ROOT / "paper" / "latex"
TARGET = ROOT / "paper" / "Witasse_Korea_Taiwan_semiconductors.pdf"


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=LATEX, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout or ""


def sync_figures() -> None:
    """make_figures.py writes to paper/figures/, but LaTeX reads paper/latex/figures/. Copy before every build.

    Without this the PDF silently kept a stale Figure 1 (Taiwan at 44 months) after the figure itself was updated.
    """
    dst = LATEX / "figures"
    dst.mkdir(exist_ok=True)
    changed = []
    for src in sorted((ROOT / "paper" / "figures").glob("*.png")):
        out = dst / src.name
        if not out.exists() or out.read_bytes() != src.read_bytes():
            shutil.copy2(src, out)
            changed.append(src.name)
    print(f"figures synced: {', '.join(changed) if changed else 'already current'}")


def build_overleaf_zip() -> None:
    """Rebuild paper/overleaf.zip from the exact sources the PDF was just built from."""
    members = ["main.tex", "references.bib", "README.md"]
    members += [f"figures/{p.name}" for p in sorted((LATEX / "figures").glob("*.png"))]
    target = ROOT / "paper" / "overleaf.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for m in members:
            if (LATEX / m).exists():
                z.write(LATEX / m, m)
    print(f"overleaf bundle: {target} ({target.stat().st_size / 1024:.0f} KB)")


def main() -> None:
    sync_figures()
    for step in (["pdflatex", "-interaction=nonstopmode", "main.tex"],
                 ["bibtex", "main"],
                 ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                 ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
        out = run(step)
        # pdflatex marks errors with a leading "!"; bibtex does not, and a silent bibtex failure drops the whole
        # bibliography while the build still reports success. Both are checked.
        errors = [ln for ln in out.splitlines() if ln.startswith("!")]
        if step[0] == "bibtex":
            errors += [ln for ln in out.splitlines()
                       if "I found no" in ln or "error message" in ln or ln.startswith("Warning--I didn't find")]
        if errors:
            print(f"{step[0]}: {errors[0]}")
            sys.exit(f"build failed in {step[0]} — see {LATEX / 'main.log'} and {LATEX / 'main.blg'}")
    pdf = LATEX / "main.pdf"
    if not pdf.exists():
        sys.exit("no PDF produced")

    # A dropped bibliography is the failure this build has actually made before, so assert the references survived.
    aux = (LATEX / "main.aux").read_text(encoding="utf-8", errors="replace")
    bbl = LATEX / "main.bbl"
    n_cited = len(set(aux.split("\\citation{")[1:]))
    if not bbl.exists() or "bibitem" not in bbl.read_text(encoding="utf-8", errors="replace"):
        sys.exit("bibliography is empty — bibtex did not run correctly")
    n_items = bbl.read_text(encoding="utf-8", errors="replace").count("\\bibitem")
    print(f"bibliography: {n_items} entries rendered from {n_cited} citation commands")
    shutil.copy2(pdf, TARGET)
    pages = out.split("Output written on main.pdf (")[-1].split(" pages")[0] if "Output written" in out else "?"
    print(f"built {TARGET} ({pages} pages, {TARGET.stat().st_size / 1024:.0f} KB)")
    build_overleaf_zip()


if __name__ == "__main__":
    main()
