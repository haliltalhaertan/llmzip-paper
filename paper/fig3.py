
import numpy as np, matplotlib.pyplot as plt
from figcommon import *
L = ledger()
MB = 1e6
fig = plt.figure(figsize=(W2, 112 * MM))
gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], hspace=0.75, wspace=0.55, left=0.19, right=0.975, top=0.93, bottom=0.12)
axA = fig.add_subplot(gs[0, 0]); axB = fig.add_subplot(gs[0, 1]); axC = fig.add_subplot(gs[1, 0]); axD = fig.add_subplot(gs[1, 1])

# a — what occupies memory (10 LoCoMo archives)
rows = [("encoder: character vocabulary", L["resident.cv_char_vectorizer"], C_CODE),
        ("encoder: word vocabulary", L["resident.wv_word_vectorizer"], C_CODE),
        ("BM25 index (stock)", L["cbm25.LoCoMo.stock_bm25_bytes"], C_BM25),
        ("raw conversation text", L["resident.raw_text"], C_REF),
        ("packed 96-bit document codes", L["resident.packed_doc_codes"], C_CODE),
        ("SVD projector", L["resident.base_lsa_projector"], C_CODE)]
y = np.arange(len(rows))[::-1]
for yi, (lab, v, c) in zip(y, rows):
    axA.hlines(yi, 0.01, v / MB, color=META_GREY, lw=0.8); axA.plot(v / MB, yi, "o", color=c, ms=4.5)
    txt = f"{v/MB:.2f} MB" if v >= 1e5 else f"{v/1e3:.1f} kB"
    axA.annotate(txt, (v / MB, yi), xytext=(4, 0), textcoords="offset points", va="center", fontsize=6.5)
axA.set_xscale("log"); axA.set_xlim(0.01, 200); axA.set_yticks(y); axA.set_yticklabels([r[0] for r in rows])
axA.set_xlabel("resident bytes, 10 LoCoMo archives (MB, log)")
axA.set_title("The codes are 0.3%; the vocabulary is the memory", loc="left")

# b — bit-identical compactions
items = [("encoder vocabulary", [("LoCoMo", "vocab.locomo"), ("PerLTQA", "vocab.perltqa"), ("LME", "vocab.lme")]),
         ("BM25 index", [("LoCoMo", "cbm25.LoCoMo"), ("PerLTQA", "cbm25.PerLTQA"), ("LME", "cbm25.LongMemEval"), ("RealTalk", "cbm25.RealTalk")])]
labs, vals, cols = [], [], []
for grp, lst in items:
    for b, k in lst:
        labs.append(b); vals.append(L[k + ".saving_pct"]); cols.append(C_CODE if grp.startswith("enc") else C_BM25)
    labs.append(""); vals.append(np.nan); cols.append("none")
labs, vals, cols = labs[:-1], vals[:-1], cols[:-1]
x = np.arange(len(vals))
axB.bar(x, vals, color=cols, width=0.7)
for xi, v in zip(x, vals):
    if not np.isnan(v): axB.annotate(f"{v:.0f}", (xi, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=6.5)
axB.set_xticks(x); axB.set_xticklabels(labs, rotation=35, ha="right", fontsize=6); axB.set_ylim(0, 118); axB.set_yticks([0, 20, 40, 60, 80])
axB.set_ylabel("bytes removed (%)"); axB.set_title("Compaction without changing a bit", loc="left")
axB.annotate("encoder", (1, 88), ha="center", fontsize=6.5, color=C_CODE)
axB.annotate("BM25 index", (5.5, 88), ha="center", fontsize=6.5, color=C_BM25)
nv = sum(L[f"vocab.{b}.vectors"] for b in ("locomo", "perltqa", "lme")); nq = sum(L[f"cbm25.{b}.queries_compared"] for b in ("LoCoMo", "PerLTQA", "LongMemEval", "RealTalk"))
mm = sum(L[f"vocab.{b}.mismatch"] for b in ("locomo", "perltqa", "lme")) + sum(L[f"cbm25.{b}.score_bit_mismatches"] for b in ("LoCoMo", "PerLTQA", "LongMemEval", "RealTalk"))
axB.annotate(f"differing bits: {mm:.0f} over {nv:,.0f} vectors\nand {nq:,.0f} queries", (3, 100), ha="center", va="bottom", fontsize=6.5, color=C_INK)

# c — fair encoder/BM25 ratio
bs = [("LoCoMo", "LoCoMo"), ("PerLTQA", "PerLTQA"), ("LME", "LongMemEval")]
for i, (lab, b) in enumerate(bs):
    s, c_, f = L[f"ratio.{b}.stock"], L[f"ratio.{b}.compact"], L[f"ratio.{b}.fused"]
    axC.hlines(i, s, c_, color=META_GREY, lw=0.8)
    axC.plot(s, i, "o", mfc="white", mec=C_INK, ms=4.5); axC.plot(c_, i, "o", color=C_CODE, ms=4.5); axC.plot(f, i, "D", color=C_FUSE, ms=4)
    for v, dy in ((s, 7), (c_, 7), (f, 7)): axC.annotate(f"{v:.2f}×", (v, i), xytext=(0, dy), textcoords="offset points", ha="center", fontsize=6.5)
axC.vlines(1, -0.5, 2.7, color=C_INK, lw=0.8); axC.annotate("parity", (1.08, 2.45), fontsize=6.5, color=C_INK)
axC.set_yticks(range(3)); axC.set_yticklabels([b[0] for b in bs]); axC.set_ylim(-1.2, 2.7); axC.set_xlim(0.5, 6.7)
axC.set_xlabel("encoder memory ÷ BM25 memory (×)")
axC.set_title("Compacting both sides widens the gap", loc="left")
axC.plot([], [], "o", mfc="white", mec=C_INK, label="stock÷stock"); axC.plot([], [], "o", color=C_CODE, label="compact÷compact"); axC.plot([], [], "D", color=C_FUSE, label="fusion÷compact")
axC.legend(frameon=False, fontsize=6, loc="lower left", ncol=3, handletextpad=0.2, columnspacing=0.8, borderaxespad=0.1)

# d — owner F1–F4 chain
steps = [("start", L["f1.before"]), ("F1", L["f1.after"]), ("F2", L["f2.after"]), ("F4", L["f4.after"])]
x = np.arange(len(steps))
axD.bar(x, [v / MB for _, v in steps], color=[C_REF, C_CODE, C_CODE, C_CODE], width=0.62)
for xi, (_, v) in zip(x, steps): axD.annotate(f"{v/MB:.1f}", (xi, v / MB), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=6.5)
axD.set_xticks(x); axD.set_xticklabels([s[0] for s in steps]); axD.set_ylim(0, 150); axD.set_yticks([0, 25, 50, 75, 100])
axD.set_ylabel("resident bytes (MB)"); axD.set_title(f"Owner chain: −{L['f1f4.total_saving_pct']:.1f}%", loc="left")
axD.annotate(f"query {L['f4.ms_before']:.2f} → {L['f4.ms_after']:.2f} ms", (3.4, 138), ha="right", fontsize=6.5, color=C_INK)
axD.annotate(f"F3 cuts query payload\n(−{L['f3.payload_saving_pct']:.1f}%), not residency", (3.4, 114), ha="right", fontsize=6.5, color=C_INK)

for ax, l in ((axA, "a"), (axB, "b"), (axC, "c"), (axD, "d")): panel_letter(ax, l)
RESULT = check_and_save(fig, "fig3_memory")
