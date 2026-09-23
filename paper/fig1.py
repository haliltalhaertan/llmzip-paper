
import numpy as np, matplotlib.pyplot as plt
from figcommon import *
L = ledger()
fig = plt.figure(figsize=(W2, 140 * MM))
outer = fig.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.5, left=0.075, right=0.985, top=0.94, bottom=0.12)
top = outer[0].subgridspec(1, 2, wspace=0.42); bot = outer[1].subgridspec(1, 3, width_ratios=[2.6, 3.6, 4.4], wspace=0.62)
axA = fig.add_subplot(top[0]); axB = fig.add_subplot(top[1]); axC = fig.add_subplot(bot[0]); axD = fig.add_subplot(bot[1])
gsE = bot[2].subgridspec(1, 2, wspace=0.12); axE1 = fig.add_subplot(gsE[0]); axE2 = fig.add_subplot(gsE[1], sharey=axE1)
rows = [("Project unit (captions appended)", L["locomo_gap.mean.A_project"], C_REF),
        ("  − image captions", L["locomo_gap.mean.B_no_captions"], C_REF),
        ("  + session timestamps", L["locomo_gap.mean.C_plus_timestamps"], C_REF),
        ("External unit, project harness", L["locomo_gap.mean.D_external_text"], C_BM25),
        ("External, expected ties (efr3)", L["locomo_gap.mean.E_external_end_to_end"], C_BM25),
        ("External, as reported (fr3)", L["locomo_gap.external_reported"], C_BM25)]
y = np.arange(len(rows))[::-1]
for yi, (lab, v, c) in zip(y, rows):
    axA.hlines(yi, 39.6, v, color=META_GREY, lw=0.8, zorder=1); axA.plot(v, yi, "o", color=c, ms=4.5, zorder=3)
    axA.annotate(f"{v:.2f}", (v, yi), xytext=(4, 0), textcoords="offset points", va="center", fontsize=6.5)
axA.set_yticks(y); axA.set_yticklabels([r[0] for r in rows]); axA.set_xlim(39.6, 44.6)
axA.set_xlabel("BM25 FR@3 on LoCoMo (%)"); axA.set_title("Document unit: the 1.9 pp gap is how text is cut", loc="left")
cells = [("project", "rare", "project unit,\nrare bucket"), ("project", "all", "project unit,\nall queries"),
         ("external", "rare", "external unit,\nrare bucket"), ("external", "all", "external unit,\nall queries")]
xs = np.arange(4)
for off, cname, col, lab in ((-0.12, "sym_384-bm25", C_CODE, "384-bit sign code − BM25"), (0.12, "raw_full-bm25", C_FLOAT, "full raw float − BM25")):
    for xi, (u, c, _) in zip(xs, cells):
        k = f"n2.{u}.{c}.{cname}"; ci_point(axB, xi + off, L[k], L[k + ".lo"], L[k + ".hi"], col, sig=(L[k + ".sig"] == "True"), horizontal=False)
    axB.plot([], [], "o", color=col, label=lab)
axB.axhline(0, color=C_INK, lw=0.8); axB.set_xticks(xs); axB.set_xticklabels([c[2] for c in cells]); axB.set_xlim(-0.5, 3.5)
axB.set_ylabel("FR@3 difference (pp)"); axB.set_title("Cohort and unit change what is significant", loc="left")
axB.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.02), fontsize=6.5, handletextpad=0.3)
axB.annotate("open marker = CI includes 0", (3.45, -15.2), ha="right", fontsize=6.5, color=C_INK)
pc = [(L["ladder.diff.NOPROJ_WORD/float-vs-NOPROJ_FULL/float.fr3"], L["ladder.diff.NOPROJ_WORD/float-vs-NOPROJ_FULL/float.fr3.lo"], L["ladder.diff.NOPROJ_WORD/float-vs-NOPROJ_FULL/float.fr3.hi"], C_FLOAT),
      (L["chan.RealTalk.WORD.d"], L["chan.RealTalk.WORD.lo"], L["chan.RealTalk.WORD.hi"], C_CODE)]
for i, (v, lo, hi, c) in enumerate(pc): ci_point(axC, i, v, lo, hi, c, horizontal=False)
axC.axhline(0, color=C_INK, lw=0.8); axC.set_xticks([0, 1]); axC.set_xticklabels(["no projection,\nfloat", "k = 96,\nsign code"]); axC.set_xlim(-0.6, 1.6)
axC.set_ylabel("word-only − all channels,\nFR@3 (pp)"); axC.set_title("Projection flips it", loc="left")
bn = ["LME", "RealTalk", "LoCoMo", "PerLTQA"]
for i, k in enumerate(bn):
    ci_point(axD, i, L[f"chan.{k}.WORD.d"], L[f"chan.{k}.WORD.lo"], L[f"chan.{k}.WORD.hi"], C_CODE, sig=L[f"chan.{k}.WORD.sig"] == 1.0, horizontal=False)
axD.axhline(0, color=C_INK, lw=0.8); axD.set_xticks(range(4)); axD.set_xticklabels(bn); axD.set_xlim(-0.6, 3.6)
axD.set_ylabel("drop character channel,\nFR@3 (pp)"); axD.set_title("Benchmark flips it", loc="left")
bE = ["LoCoMo", "PerLTQA", "LongMemEval", "RealTalk"]; yE = np.arange(4)[::-1]
for yi, b in zip(yE, bE):
    base = L[f"fusion.{b}.bm25.E_T"]
    v, lo, hi = (-100 * L[f"fusion.{b}.W.dE_T{s}"] / base for s in ("", ".hi", ".lo")); ci_point(axE1, v, yi, lo, hi, C_FUSE, sig=(lo > 0 or hi < 0))
    v, lo, hi = (L[f"fusion.{b}.W.dFR3{s}"] for s in ("", ".lo", ".hi")); ci_point(axE2, v, yi, lo, hi, C_FUSE, sig=(lo > 0 or hi < 0))
for ax in (axE1, axE2): ax.axvline(0, color=C_INK, lw=0.8); ax.margins(x=0.12)
axE1.set_xticks([0, 25, 50]); axE2.set_xticks([-5, 0, 5])
axE1.set_yticks(yE); axE1.set_yticklabels(["LoCoMo", "PerLTQA", "LME", "RealTalk"]); plt.setp(axE2.get_yticklabels(), visible=False)
axE1.set_xlabel("docs saved (%)"); axE2.set_xlabel("FR@3 (pp)"); axE1.set_title("Metric flips it", loc="left")
for ax, l in ((axA, "a"), (axB, "b"), (axC, "c"), (axD, "d"), (axE1, "e")): panel_letter(ax, l)
fig.text(0.985, 0.012, "c–e: up / right = the tested change helps", ha="right", fontsize=6.5, color=C_INK)
RESULT = check_and_save(fig, "fig1_reversals")
