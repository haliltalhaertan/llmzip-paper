
import numpy as np, matplotlib.pyplot as plt
from figcommon import *
L = ledger()
fig = plt.figure(figsize=(W2, 62 * MM))
gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.1, 1], wspace=0.5, left=0.075, right=0.985, top=0.86, bottom=0.2)
axA = fig.add_subplot(gs[0]); axB = fig.add_subplot(gs[1]); axC = fig.add_subplot(gs[2])

# a — per-query T summaries
sy = [("sign96", "96-bit sign code", C_CODE), ("float96", "same code, float", C_FLOAT), ("bm25", "BM25", C_BM25)]
for i, (k, lab, c) in enumerate(sy):
    med, mean, p90, mx = (L[f"reach.{k}.{s}"] for s in ("median", "E_T", "p90", "max"))
    axA.hlines(i, med, p90, color=c, lw=2.2, alpha=0.45)
    axA.plot(med, i, "|", color=c, ms=9, mew=1.6); axA.plot(mean, i, "o", color=c, ms=4.5)
    axA.annotate(f"median {med:.0f}", (med, i), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=6.5)
    axA.annotate(f"mean {mean:.1f}", (mean, i), xytext=(0, -11), textcoords="offset points", ha="center", fontsize=6.5)
axA.set_xscale("log"); axA.set_xlim(2, 700); axA.set_xticks([3, 10, 30, 100, 300]); axA.set_xticklabels(["3", "10", "30", "100", "300"]); axA.minorticks_off(); axA.set_ylim(-0.6, 3.1)
axA.set_yticks(range(3)); axA.set_yticklabels([s[1] for s in sy])
axA.set_xlabel("docs opened to first evidence (log)")
axA.set_title("BM25 is usually right early", loc="left")
axA.annotate("tick = median; dot = mean;\nbar to 90th percentile", (0.98, 0.99), xycoords="axes fraction", ha="right", va="top", fontsize=6.5, color=C_INK)

# b — policy-shaped weight grid
lams = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
for k, lab, c in (("code", "96-bit sign code", C_CODE), ("bm25", "BM25", C_BM25)):
    v = [L[f"policy.grid.{k}.{l}"] for l in lams]
    axB.plot(range(len(lams)), v, "-o", color=c, ms=3.5, lw=1.2, label=lab)
axB.plot(3, L["policy.code.adaptive"], "o", ms=7, mfc="none", mec=C_INK, mew=1.0)
axB.annotate(("λ chosen out of fold:\n" + f"{L['policy.code.delta']:+.2f} [{L['policy.code.lo']:.2f}, {L['policy.code.hi']:.2f}]").replace("-", "−"), (3, L["policy.code.adaptive"]),
             xytext=(0, 12), textcoords="offset points", ha="center", va="bottom", fontsize=6.5)
axB.annotate("BM25: λ = 0 chosen (no gain)", (0.15, L["policy.bm25.static"]), xytext=(6, -4), textcoords="offset points", va="center", fontsize=6.5, color=C_BM25)
axB.set_xticks(range(len(lams))); axB.set_xticklabels(["0", ".25", ".5", "1", "2", "4", "8"])
axB.set_xlabel("policy weight λ"); axB.set_ylabel("E[T]"); axB.set_ylim(58, 100)
axB.set_title("Policy shaping helps only the code", loc="left")
axB.legend(frameon=False, fontsize=6.5, loc="upper left", handletextpad=0.3)

# c — combination headroom
cb, tie = L["reach.code_better_pct"], L["reach.tie_pct"]; bb = 100 - cb - tie
parts = [("code earlier", cb, C_CODE), ("tie", tie, C_REF), ("BM25 earlier", bb, C_BM25)]
left = 0
for j, (lab, v, c) in enumerate(parts):
    axC.barh(1.6, v, left=left, color=c, height=0.45)
    if j < 2:
        axC.annotate(f"{lab} {v:.1f}%", (left + v / 2, 1.85), xytext=(0, 3 + 9 * j), textcoords="offset points", ha="center", va="bottom", fontsize=6.5, color=c if c != C_REF else C_INK)
    else:
        axC.annotate(f"{lab}\n{v:.1f}%", (left + v / 2, 1.6), ha="center", va="center", fontsize=6.5, color="white")
    left += v
rows = [("best of two (oracle)", L["reach.oracle_min"], C_FLOOR), ("BM25 alone", L["reach.bm25.E_T"], C_BM25), ("alternate the two", L["reach.interleave"], C_FUSE)]
for yi, (lab, v, c) in zip((0.8, 0.3, -0.2), rows):
    axC.hlines(yi, 0, v, color=META_GREY, lw=0.8); axC.plot(v, yi, "o", color=c, ms=4.5, mfc="white" if yi == 0.8 else c, mec=c, mew=1.2)
    axC.annotate(f"{lab}: {v:.1f}", (v, yi), xytext=(4, 0), textcoords="offset points", va="center", fontsize=6.5)
axC.set_xlim(0, 100); axC.set_ylim(-0.55, 2.45); axC.set_yticks([])
axC.spines["left"].set_visible(False)
axC.set_xlabel("bar: % of queries; points: E[T]")
axC.set_title("Complementary, but hard to exploit", loc="left")
for ax, l in ((axA, "a"), (axB, "b"), (axC, "c")): panel_letter(ax, l)
fig.text(0.985, 0.015, "LoCoMo, n = 1,535; lower E[T] is better", ha="right", fontsize=6.5, color=C_INK)
RESULT = check_and_save(fig, "fig4_expected_cost")
