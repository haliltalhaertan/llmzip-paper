"""Shared helpers for the paper figures: ledger access, palette, save-and-check."""
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path

PAPER = Path("paper")
FIG = PAPER / "figures"
MM = 1 / 25.4
W2 = 180 * MM          # double-column width, inches

C_BM25 = "#c98b2e"     # BM25, every figure
C_CODE = "#1f6f8b"     # 96-bit sign code / compact code
C_FLOAT = "#6fa8bf"    # same projection before sign quantisation
C_FUSE = "#7b4f9d"     # fusion arms
C_REF = "#8c959f"      # reference / no index / stock
C_FLOOR = "#4f7d2b"    # theoretical floor / oracle / ceiling
C_INK = "#333333"


def ledger():
    L = {}
    with open(PAPER / "CLAIMS_LEDGER.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["value"]
            try:
                v = float(v)
            except ValueError:
                pass
            L[r["claim_id"]] = v
    return L


def check_and_save(fig, name):
    """Save PDF+PNG and return the list of overlapping text pairs (should be empty)."""
    FIG.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    texts = [(t, t.get_window_extent(r)) for t in fig.findobj(mpl.text.Text)
             if t.get_text().strip() and t.get_visible()]
    ov = [(a.get_text()[:18], b.get_text()[:18]) for i, (a, ba) in enumerate(texts)
          for b, bb in texts[i + 1:] if ba.overlaps(bb)]
    fb = fig.bbox
    out = [t.get_text()[:18] for t, bt in texts
           if bt.x0 < fb.x0 - 1 or bt.y0 < fb.y0 - 1 or bt.x1 > fb.x1 + 1 or bt.y1 > fb.y1 + 1]
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=300)
    return ov, out


def ci_point(ax, x, y, lo, hi, color, sig=None, horizontal=True, ms=4.5, lw=1.2, z=3):
    """Point with interval; open marker when not significant."""
    face = color if (sig is None or sig) else "white"
    if horizontal:
        ax.errorbar(x, y, xerr=[[x - lo], [hi - x]], fmt="o", color=color, mfc=face, mec=color,
                    ms=ms, lw=lw, capsize=0, zorder=z)
    else:
        ax.errorbar(x, y, yerr=[[y - lo], [hi - y]], fmt="o", color=color, mfc=face, mec=color,
                    ms=ms, lw=lw, capsize=0, zorder=z)


# ---------------------------------------------------------------- house style (self-contained)
META_GREY = "#888888"
STYLE = {
    "font.size": 8.0, "axes.titlesize": 8.0, "axes.labelsize": 8.0, "legend.fontsize": 7.0,
    "xtick.labelsize": 6.0, "ytick.labelsize": 6.0, "axes.titlelocation": "left",
    "axes.linewidth": 0.6, "axes.spines.right": False, "axes.spines.top": False,
    "xtick.major.size": 3.0, "xtick.major.width": 0.6, "ytick.major.size": 3.0, "ytick.major.width": 0.6,
    "lines.linewidth": 1.2, "patch.linewidth": 0.6, "legend.frameon": False,
    "figure.dpi": 200.0, "savefig.dpi": 300.0, "savefig.bbox": "tight", "pdf.fonttype": 42, "ps.fonttype": 42,
}
mpl.rcParams.update(STYLE)


def panel_letter(ax, letter, dx=-0.18, dy=1.02, fontsize=9):
    """Bold lower-case panel letter above the top-left corner of an axes."""
    ax.text(dx, dy, letter.lower(), transform=ax.transAxes, fontsize=fontsize, fontweight="bold",
            ha="left", va="bottom")
