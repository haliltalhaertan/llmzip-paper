"""Regenerate every figure, table and number of the paper from paper/CLAIMS_LEDGER.csv.

Run from the repository root:  python build_all.py
Then compile:  cd paper && pdflatex llmzip_paper && bibtex llmzip_paper && pdflatex llmzip_paper && pdflatex llmzip_paper
Then check:    python paper/verify_paper.py
"""
import runpy, sys
from pathlib import Path

sys.path.insert(0, str(Path("paper").resolve()))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

for n in range(1, 7):
    ns = runpy.run_path(f"paper/fig{n}.py", run_name="__main__")
    overlaps = ns["RESULT"][0]
    print(f"fig{n}: {len(overlaps)} text-overlap pairs reported by the checker")
    plt.close("all")
runpy.run_path("paper/make_tables.py", run_name="__main__")
runpy.run_path("paper/render.py", run_name="__main__")
