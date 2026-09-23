
import numpy as np, matplotlib.pyplot as plt
from figcommon import *
L = ledger()
def ab(s): a, b = s.split("->"); return float(a), float(b)
def fr(s): a, b = s.split("/"); return float(a), float(b)
fig = plt.figure(figsize=(W2, 112 * MM))
gs = fig.add_gridspec(2, 2, hspace=0.72, wspace=0.5, left=0.12, right=0.985, top=0.93, bottom=0.11)
axA = fig.add_subplot(gs[0, 0]); axB = fig.add_subplot(gs[0, 1]); axC = fig.add_subplot(gs[1, 0]); axD = fig.add_subplot(gs[1, 1])

# a — certificate gap by relaxation family (Codex strand)
fam = [("bundled", "bundled relaxation", C_REF, "o"), ("fully_split_with_cost_sharing", "split + cost sharing", C_FLOAT, "s"),
       ("hard_nonanticipativity_60s", "hard non-anticipativity (60 s)", C_BM25, "^"), ("martingale_penalty", "martingale penalty", C_FLOOR, "D")]
Ns = [4, 8, 12]
for k, lab, c, m in fam:
    v = [L[f"codex.gap.{k}.N{n}"] for n in Ns]
    axA.plot(Ns, v, "-" + m, color=c, ms=4, lw=1.2, label=lab)
axA.set_xticks(Ns); axA.set_xlabel("number of items N"); axA.set_ylabel("certificate gap")
axA.set_title("Only the martingale penalty closes it at every N", loc="left"); axA.set_ylim(-1.5, 31); axA.set_yticks([0, 5, 10, 15, 20])
axA.legend(frameon=False, fontsize=6.5, loc="upper left", ncol=2, handletextpad=0.3, columnspacing=1.0, borderaxespad=0.1)

# b — representation size (N = 12)
items = [("value\ntable", "codex.dd.table.value"), ("value\nquotient", "codex.dd.quotient.value"),
         ("policy\ntable", "codex.dd.table.policy"), ("policy\nquotient", "codex.dd.quotient.policy")]
x = np.arange(len(items) + 1)
for i, (lab, k) in enumerate(items):
    s, r = L[k + ".strict.nodes"], L[k + ".reachable_only.nodes"]
    c = C_CODE if "value" in k else C_FUSE
    axB.vlines(i, r, s, color=c, lw=1.0); axB.plot(i, s, "o", color=c, mfc="white", ms=4.2); axB.plot(i, r, "o", color=c, ms=4.2)
    axB.annotate(f"{r:,.0f}", (i, r), xytext=(0, -9), textcoords="offset points", ha="center", fontsize=6.5)
n20 = L["ctrl.N12.total_nodes"]
axB.plot(4, n20, "D", color=C_FLOOR, ms=4.5)
axB.annotate(f"{n20:.0f} nodes\n{L['ctrl.N12.program_bytes']:,.0f} B", (4, n20), xytext=(0, 6), textcoords="offset points", ha="center", va="bottom", fontsize=6.5)
axB.set_yscale("log"); axB.set_ylim(8, 20000); axB.set_yticks([10, 100, 1000, 10000]); axB.set_yticklabels(["10", "100", "1,000", "10,000"]); axB.minorticks_off()
axB.set_xticks(x); axB.set_xticklabels([i[0] for i in items] + ["compiled\nprogram"], fontsize=6); axB.set_xlim(-0.5, 4.5)
axB.set_ylabel("diagram nodes (log)")
axB.set_title("A 20-node program replaces thousands of nodes", loc="left")
axB.plot([], [], "o", color=C_INK, mfc="white", label="strict"); axB.plot([], [], "o", color=C_INK, label="reachable only")
axB.legend(frameon=False, fontsize=6.5, loc="upper right", handletextpad=0.3)

# c — reader accuracy depends on retrieval (parallel LongMemEval line)
n = L["par.qa2.n"]
bars = [("stemmed\nBM25 (B1c)", 100 * L["par.qa2.B1c"] / n, C_BM25), ("gold\nevidence", 100 * L["par.qa2.ORACLE"] / n, C_FLOOR)]
cg, ng = fr(L["par.qa2.allgold_correct"]); cm, nm = fr(L["par.qa2.missing_correct"])
bars += [(f"all gold in\ntop 5 (n={ng:.0f})", 100 * cg / ng, C_CODE), (f"gold missing\n(n={nm:.0f})", 100 * cm / nm, C_REF)]
for i, (lab, v, c) in enumerate(bars):
    axC.bar(i + (0.4 if i == 2 else 0.6 if i == 3 else 0), v, color=c, width=0.62)
    axC.annotate(f"{v:.1f}" if i < 2 else f"{v:.0f}", (i + (0.4 if i == 2 else 0.6 if i == 3 else 0), v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=6.5)
axC.set_xticks([0, 1, 2.4, 3.6]); axC.set_xticklabels([b[0] for b in bars], fontsize=6); axC.set_ylim(0, 112); axC.set_yticks([0, 25, 50, 75, 100])
axC.set_ylabel("reader correct (%)")
axC.annotate(f"McNemar p = {L['par.qa2.p']:.3f}", (0.5, 99), ha="center", fontsize=6.5, color=C_INK)
axC.annotate("B1c run, split by retrieval", (3.0, 104), ha="center", fontsize=6.5, color=C_INK)
axC.set_title("Answers follow retrieval", loc="left")

# d — query expansion: dev lead, held-out non-confirmation
rowsd = [("dev: QA", ab(L["par.qexp_dev.qa"]), 250, L["par.qexp_dev.p"]),
         ("held-out: QA", ab(L["par.qexp_ho.qa"]), 250, L["par.qexp_ho.p"]),
         ("held-out: all gold@5", ab(L["par.qexp_ho.all5"]), 240, L["par.qexp_ho.all5_p"])]
yd = np.arange(len(rowsd))[::-1]
for yi, (lab, (a, b), den, p) in zip(yd, rowsd):
    va, vb = 100 * a / den, 100 * b / den
    axD.annotate("", (vb, yi), xytext=(va, yi), arrowprops=dict(arrowstyle="-|>", color=C_FUSE, lw=1.0, shrinkA=2, shrinkB=2))
    axD.plot(va, yi, "o", color=C_BM25, ms=4.2); axD.plot(vb, yi, "o", color=C_FUSE, ms=4.2)
    axD.annotate(f"p = {p:.2f}", (max(va, vb), yi), xytext=(8, 0), textcoords="offset points", va="center", fontsize=6.5)
axD.set_yticks(yd); axD.set_yticklabels([r[0] for r in rowsd]); axD.set_xlim(78, 94); axD.set_ylim(-0.6, 2.8)
axD.set_xlabel("correct (%)"); axD.set_title("Query expansion does not confirm", loc="left")
axD.plot([], [], "o", color=C_BM25, label="without expansion"); axD.plot([], [], "o", color=C_FUSE, label="with expansion")
axD.legend(frameon=False, fontsize=6.5, loc="upper right", ncol=2, handletextpad=0.2, columnspacing=0.8, borderaxespad=0.0)
for ax, l in ((axA, "a"), (axB, "b"), (axC, "c"), (axD, "d")): panel_letter(ax, l)
fig.text(0.11, 0.505, "a–b: external Codex strand (re-run independently)", fontsize=6.5, color=C_INK, ha="left")
fig.text(0.11, 0.015, "c–d: parallel LongMemEval line (recomputed from its per-question files)", fontsize=6.5, color=C_INK, ha="left")
RESULT = check_and_save(fig, "fig6_external")
