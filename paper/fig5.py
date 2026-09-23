
import numpy as np, matplotlib.pyplot as plt
from figcommon import *
L = ledger()
C_PH = "#b39bc8"
fig = plt.figure(figsize=(W2, 66 * MM))
gs = fig.add_gridspec(1, 3, wspace=0.16, left=0.1, right=0.985, top=0.80, bottom=0.2)
axA = fig.add_subplot(gs[0]); axB = fig.add_subplot(gs[1], sharey=axA); axC = fig.add_subplot(gs[2], sharey=axA)
bs = [("LoCoMo", "LoCoMo"), ("PerLTQA", "PerLTQA"), ("LME", "LongMemEval"), ("RealTalk", "RealTalk")]
y = np.arange(4)[::-1]
def pt(ax, v, yy, lo, hi, c, m):
    s = lo > 0 or hi < 0
    ax.hlines(yy, lo, hi, color=c, lw=1.1)
    ax.plot(v, yy, m, ms=4.3, color=c, mfc=c if s else "white", mec=c, mew=1.1, zorder=3)
for yi, (lab, b) in zip(y, bs):
    base = L[f"fusion.{b}.bm25.E_T"]
    # a  E[T] reduction, %
    v, lo, hi = (-100 * L[f"fusion.{b}.W.dE_T{s}"] / base for s in ("", ".hi", ".lo")); pt(axA, v, yi + 0.15, lo, hi, C_FUSE, "o")
    v, lo, hi = (-100 * L[f"posthoc.{b}.dE_T{s}"] / base for s in ("", ".hi", ".lo")); pt(axA, v, yi - 0.15, lo, hi, C_PH, "D")
    # b  FR@3
    pt(axB, L[f"fusion.{b}.W.dFR3"], yi + 0.15, L[f"fusion.{b}.W.dFR3.lo"], L[f"fusion.{b}.W.dFR3.hi"], C_FUSE, "o")
    pt(axB, L[f"posthoc.{b}.dFR3"], yi - 0.15, L[f"posthoc.{b}.dFR3.lo"], L[f"posthoc.{b}.dFR3.hi"], C_PH, "D")
    # c  all evidence in top 5
    pt(axC, L[f"allev.{b}.W_loo.dall@5"], yi + 0.15, L[f"allev.{b}.W_loo.dall@5.lo"], L[f"allev.{b}.W_loo.dall@5.hi"], C_FUSE, "o")
    pt(axC, L[f"allev.{b}.w0.1.dall@5"], yi - 0.15, L[f"allev.{b}.w0.1.dall@5.lo"], L[f"allev.{b}.w0.1.dall@5.hi"], C_PH, "D")
for ax in (axA, axB, axC): ax.axvline(0, color=C_INK, lw=0.8)
axA.vlines(5, y[0] - 0.45, y[0] + 0.55, color=C_FLOOR, lw=1.0, ls=(0, (3, 2)))
axA.annotate("primary: ≥ 5% (LoCoMo)", (5, y[0] + 0.5), xytext=(2, 0), textcoords="offset points", fontsize=6.5, color=C_FLOOR, va="bottom")
axB.axvline(-1, color=C_FLOOR, lw=1.0, ls=(0, (3, 2)))
axB.annotate("margin −1 pp", (-1, y[0] + 0.5), xytext=(-2, 0), textcoords="offset points", ha="right", va="bottom", fontsize=6.5, color=C_FLOOR)
axA.set_yticks(y); axA.set_yticklabels([b[0] for b in bs]); axA.set_ylim(-0.6, 3.95)
for ax in (axB, axC): plt.setp(ax.get_yticklabels(), visible=False)
axA.set_xlabel("E[T] reduction vs BM25 (%)"); axB.set_xlabel("FR@3 change (pp)"); axC.set_xlabel("all evidence in top 5, change (pp)")
axA.set_title("Fewer documents opened", loc="left"); axB.set_title("First evidence in top 3", loc="left"); axC.set_title("All evidence in top 5", loc="left")
axA.plot([], [], "o", color=C_FUSE, label="gated arm: weight chosen out of fold (failed gate)")
axA.plot([], [], "D", color=C_PH, label="post-hoc lead: fixed weight w = 0.1 (never gated)")
axA.plot([], [], "o", color=C_INK, mfc="white", label="open = CI includes 0")
fig.legend(*axA.get_legend_handles_labels(), frameon=False, loc="upper center", ncol=3, fontsize=6.5, bbox_to_anchor=(0.54, 0.995), handletextpad=0.3, columnspacing=1.2)
for ax, l in ((axA, "a"), (axB, "b"), (axC, "c")): panel_letter(ax, l)
fig.text(0.985, 0.015, "right = the fusion helps; E[T] and FR@3 intervals 97.5% (Bonferroni), all-evidence 95%", ha="right", fontsize=6.5, color=C_INK)
RESULT = check_and_save(fig, "fig5_fusion")
