
import numpy as np, matplotlib.pyplot as plt
from figcommon import *
L = ledger()
fig = plt.figure(figsize=(W2, 128 * MM))
outer = fig.add_gridspec(2, 2, width_ratios=[1, 1.12], height_ratios=[1, 1], hspace=0.62, wspace=0.34,
                         left=0.12, right=0.985, top=0.94, bottom=0.10)
axA = fig.add_subplot(outer[:, 0]); axB = fig.add_subplot(outer[0, 1])
bot = outer[1, 1].subgridspec(1, 2, wspace=0.42); axC = fig.add_subplot(bot[0]); axD = fig.add_subplot(bot[1])

# a — C1 forest + the never-reported unprojected arm
arms = [("k96/sym", "12 B, symmetric"), ("k96/qscale", "12 B, query-scaled"), ("k192/sym", "24 B, symmetric"),
        ("k192/qscale", "24 B, query-scaled"), ("k384/sym", "48 B, symmetric"), ("k384/qscale", "48 B, query-scaled")]
y = np.arange(len(arms))[::-1] + 1.6
for off, comp, m, lab in ((0.14, "BM25_coarse", "o", "vs BM25, coarse analyser"), (-0.14, "BM25_frozen", "s", "vs BM25, production analyser")):
    for yi, (a, _) in zip(y, arms):
        k = f"c1.{a}.{comp}.fr3"; lo, hi = L[k + ".lo"], L[k + ".hi"]
        axA.hlines(yi + off, lo, hi, color=C_CODE, lw=1.0)
        s = lo > 0 or hi < 0
        axA.plot(L[k], yi + off, m, ms=3.8, color=C_CODE, mfc=C_CODE if s else "white", mec=C_CODE, mew=1.0, zorder=3)
    axA.plot([], [], m, ms=3.8, color=C_CODE, label=lab)
# unprojected arm, separated
for off, ref, m in ((0.14, "BM25_coarse/-", "o"), (-0.14, "BM25_frozen/-", "s")):
    k = f"ladder.diff.NOPROJ_FULL/qscale-vs-{ref}.fr3"
    axA.hlines(0.4 + off, L[k + ".lo"], L[k + ".hi"], color=C_REF, lw=1.0)
    axA.plot(L[k], 0.4 + off, m, ms=3.8, color=C_REF, zorder=3)
axA.axhline(1.0, color=META_GREY, lw=0.6, ls=(0, (2, 2)))
axA.set_yticks(list(y) + [0.4]); axA.set_yticklabels([a[1] for a in arms] + ["full vocabulary,\nno projection*"])
axA.vlines(0, -0.1, y[0] + 0.55, color=C_INK, lw=0.8); axA.set_xlabel("code − BM25, FR@3 on RealTalk (pp)")
axA.set_title("No compact budget reaches BM25", loc="left")
axA.plot([], [], "o", ms=3.8, color=C_CODE, mfc="white", label="open = CI includes 0")
axA.legend(frameon=False, loc="upper left", fontsize=6.5, handletextpad=0.3, borderaxespad=0.1)
axA.annotate("* not compact; never\n  reported; post hoc", (-17.6, 0.4), ha="left", va="center", fontsize=6.5, color=C_INK)
axA.set_xlim(-18, 13.5); axA.set_ylim(-0.1, y[0] + 1.6)

# b — E[T] against the floor
lab = ["no\nindex", "sign\ncode", "float\ncode", "BM25", "best\nof two", "96-bit\nfloor"]
val = [L["reach.no_index"], L["reach.sign96.E_T"], L["reach.float96.E_T"], L["reach.bm25.E_T"], L["reach.oracle_min"], L["reach.floor"]]
col = [C_REF, C_CODE, C_FLOAT, C_BM25, C_FLOOR, C_FLOOR]
x = np.arange(len(val))
for i, (v, c) in enumerate(zip(val, col)):
    hollow = i >= 4
    axB.vlines(x[i], 0.8, v, color=META_GREY, lw=0.8, zorder=1)
    axB.plot(x[i], v, "o", ms=5, color=c, mfc="white" if hollow else c, mec=c, mew=1.3, zorder=3)
    axB.annotate(f"{v:.2f}" if v < 10 else f"{v:.1f}", (x[i], v), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=6.5)
axB.set_yscale("log"); axB.set_ylim(0.75, 1000); axB.set_yticks([1, 10, 100]); axB.set_yticklabels(["1", "10", "100"])
axB.set_xticks(x); axB.set_xticklabels(lab, fontsize=6); axB.set_xlim(-0.5, 5.5)
axB.set_ylabel("E[T], docs opened"); axB.set_title("Far above the floor its bits allow", loc="left")
axB.annotate("LoCoMo; lower = better\nhollow = bound, not a system", (4.3, 420), ha="center", va="center", fontsize=6.5, color=C_INK)

# c — rerank (idea 1)
bs = ["LME", "PerLTQA", "LoCoMo"]
for i, b in enumerate(bs):
    for off, arm, c, m in ((-0.2, "BM25_full", C_BM25, "o"), (0.0, "qscale96", C_CODE, "o"), (0.2, "qscale96_bm25", C_FUSE, "D")):
        axC.plot(i + off, 100 * L[f"rerank.{b}.{arm}.fr3"], m, color=c, ms=4.2)
axC.set_xticks(range(3)); axC.set_xticklabels(bs, fontsize=6); axC.set_ylabel("FR@3 (%)")
axC.set_title("Rerank: ≈ BM25", loc="left"); axC.set_xlim(-0.5, 2.5)
for c, m, t in ((C_BM25, "o", "BM25"), (C_CODE, "o", "96-bit code"), (C_FUSE, "D", "code → BM25 rerank")): axC.plot([], [], m, color=c, label=t)
axC.legend(frameon=False, fontsize=6, loc="lower left", handletextpad=0.2, borderaxespad=0.1)
axC.set_ylim(25, 64)

# d — shared hashed encoder (idea 2)
for i, b in enumerate(bs):
    a0, a1 = L[f"hashed.{b}.base192.fr3"], L[f"hashed.{b}.shared_seed2026091601.fr3"]
    axD.annotate("", (i, a1), xytext=(i, a0), arrowprops=dict(arrowstyle="-|>", color=C_REF, lw=1.0, shrinkA=3, shrinkB=3))
    axD.plot(i, a0, "o", color=C_CODE, ms=4.2); axD.plot(i, a1, "o", color=C_CODE, mfc="white", ms=4.2)
axD.set_xticks(range(3)); axD.set_xticklabels(bs, fontsize=6); axD.set_ylabel("FR@3 (%)"); axD.set_xlim(-0.5, 2.5)
axD.set_title("Shared encoder: halves", loc="left"); axD.set_ylim(12, 66)
axD.plot([], [], "o", color=C_CODE, label="per-archive"); axD.plot([], [], "o", color=C_CODE, mfc="white", label="shared, hashed")
axD.legend(frameon=False, fontsize=6, loc="lower left", handletextpad=0.2, borderaxespad=0.1)

for ax, l in ((axA, "a"), (axB, "b"), (axC, "c"), (axD, "d")): panel_letter(ax, l)
RESULT = check_and_save(fig, "fig2_compact_vs_bm25")
