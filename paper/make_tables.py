"""Emit every LaTeX table of the paper from CLAIMS_LEDGER.csv. No number is typed by hand."""
import csv, re
from pathlib import Path

HERE = Path("paper")
TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)
L = {r["claim_id"]: r["value"] for r in csv.DictReader(open(HERE / "CLAIMS_LEDGER.csv", encoding="utf-8"))}
USED = set()


def v(k):
    USED.add(k)
    return float(L[k])


def s(k):
    USED.add(k)
    return L[k]


def num(x, d=2, signed=False, thousands=False):
    t = f"{x:+,.{d}f}" if (signed and thousands) else f"{x:+.{d}f}" if signed else f"{x:,.{d}f}" if thousands else f"{x:.{d}f}"
    return t.replace("-", "\\textminus{}").replace(",", "{,}")


def f(k, d=2, signed=False, thousands=False, scale=1.0):
    return num(v(k) * scale, d, signed, thousands)


def ci(k, d=2, scale=1.0, lo=".lo", hi=".hi"):
    a, b = v(k + lo) * scale, v(k + hi) * scale
    a, b = min(a, b), max(a, b)
    return f"[{num(a, d)}, {num(b, d)}]"


def sig(lo, hi):
    return lo > 0 or hi < 0


RR = ">{\\raggedright\\arraybackslash}"


def rx(cols):
    out = re.sub(r"(?<![}])X", lambda m: RR + "X", cols)
    return out


APPENDIX = {"tab_c1", "tab_n2", "tab_channels", "tab_ladder", "tab_supersession"}


def write(name, body, caption, label, cols, wide=True, note=None, size="\\small"):
    env = "table"
    out = [f"\\begin{{{env}}}[{'H' if name in APPENDIX else 'tbp'}]", "\\centering", size, f"\\caption{{{caption}}}", f"\\label{{{label}}}",
           (f"\\begin{{tabularx}}{{\\linewidth}}{{{rx(cols)}}}" if "X" in cols else f"\\begin{{adjustbox}}{{max width=\\linewidth}}\\begin{{tabular}}{{{cols}}}"),
           "\\toprule", body.strip(), "\\bottomrule", ("\\end{tabularx}" if "X" in cols else "\\end{tabular}\\end{adjustbox}")]
    if note:
        out.append(f"\\par\\smallskip\\parbox{{\\linewidth}}{{\\footnotesize {note}}}")
    out.append(f"\\end{{{env}}}")
    (TAB / f"{name}.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- T1 benchmarks
rows = []
for name, key, unit, lic, use in (
        ("LongMemEval-S (cleaned)", "LongMemEval", "turn", "MIT", "470 answerable questions; 30 abstention items excluded"),
        ("LoCoMo", "LoCoMo", "turn (dialogue line)", "CC BY-NC 4.0", "category 5 excluded; five unscorable items dropped"),
        ("PerLTQA", "PerLTQA", "memory record", "CC BY-NC 4.0", "all questions"),
        ("RealTalk", "RealTalk", "message", "none published", "local use only; redistribution blocked")):
    rows.append(f"{name} & {f(f'cbm25.{key}.n_archives', 0, thousands=True)} & {f(f'cbm25.{key}.queries_compared', 0, thousands=True)} & {unit} & {lic} & {use} \\\\")
write("tab_benchmarks", "Benchmark & Archives & Queries & Document unit & Licence & Scope \\\\\n\\midrule\n" + "\n".join(rows),
      "Benchmarks. Query counts are those scored by the bit-exactness checks and the fusion runs.",
      "tab:benchmarks", "@{}l r r l l X@{}")

# ---------------------------------------------------------------- T2 gate registry
c1best = "c1.k384/qscale.BM25_coarse.fr3"
fw = "fusion.LoCoMo.W"
cut = -100 * v(fw + ".dE_T") / v("fusion.LoCoMo.bm25.E_T")
gcut = -100 * v("fusion.LoCoMo.G.dE_T") / v("fusion.LoCoMo.bm25.E_T")
g = [
    ("C3: code first stage, BM25 rerank (2026-09-16)",
     f"$\\Delta$FR@3 $\\geq {f('gate.c3.min_pp', 1)}$ pp over BM25, CI excluding 0", "yes", "not met",
     f"LME {f('gate.c3.LME.delta', 2, True)}, PerLTQA {f('gate.c3.PerLTQA.delta', 2, True)}, LoCoMo {f('gate.c3.LoCoMo.delta', 2, True)} pp (point estimates)"),
    ("C1: compact code vs BM25, RealTalk (2026-09-20)",
     f"some arm $\\leq$ 48 B/doc with $\\Delta$FR@3 $\\geq {f('gate.c1.min_pp', 1)}$ pp and {f('gate.c1.ci', 0)}\\% CI excluding 0", "yes", "fail",
     f"0 of 12 cells positive; best {f(c1best, 2, True)} {ci(c1best)} pp"),
    ("Channel ablation (2026-09-21)",
     "drop the character channel only if no benchmark shows a significant FR@3 regression", "no", "fail",
     f"LME {f('chan.LME.WORD.d', 2, True)}, RealTalk {f('chan.RealTalk.WORD.d', 2, True)} pp, both significant"),
    ("Vocabulary compaction (2026-09-21)",
     f"0 differing bits, fewer bytes, latency $\\leq {f('gate.vocab.latency_max', 2)}\\times$", "exactness", "pass",
     f"0 of {num(v('vocab.locomo.vectors') + v('vocab.perltqa.vectors') + v('vocab.lme.vectors'), 0, thousands=True)} vectors differ; bytes {f('vocab.locomo.saving_pct', 1, scale=-1)}\\% (LoCoMo)"),
    ("Policy-shaped routing (2026-09-22)", "E[T] significantly lower than static code ranking", "no", "pass (defective)",
     f"{f('policy.code.delta', 2, True)} {ci('policy.code')} docs; closes {f('policy.closed_bm25_pct', 1)}\\% of the gap to BM25"),
    ("Fusion W, weighted RRF (2026-09-23)",
     f"LoCoMo E[T] cut $\\geq {f('gate.fusion.min_cut_pct', 0)}$\\% with {f('gate.fusion.ci', 1)}\\% CI below 0; FR@3 lower bound $>$ {f('gate.fusion.margin_pp', 1)} pp on all four", "yes", "fail",
     f"E[T] {num(-cut, 1)}\\%; LoCoMo FR@3 {f(fw + '.dFR3', 2, True)} {ci(fw + '.dFR3')} pp"),
    ("Fusion G, gated switch (2026-09-23)", "same as W", "yes", "fail",
     f"E[T] {f('fusion.LoCoMo.G.dE_T', 2, True)} {ci('fusion.LoCoMo.G.dE_T')} docs: no significant difference was demonstrated"),
]
body = "Gate & Criterion (declared before the run) & Min.\\ effect & Outcome & Decisive numbers \\\\\n\\midrule\n" + \
       "\n".join(f"{a} & {b} & {c} & {d} & {e} \\\\" for a, b, c, d, e in g)
write("tab_gates", body,
      "Registry of pre-specified gates. \"Min.\\ effect\" records whether the gate named a minimum useful effect size, not only significance.",
      "tab:gates", "@{}>{\\raggedright\\arraybackslash}p{3.3cm} >{\\raggedright\\arraybackslash}X l l >{\\raggedright\\arraybackslash}p{4.4cm}@{}",
      note="Gates were written into run records before results, but none was hash-committed in advance; see Section~\\ref{sec:limits}.")

# ---------------------------------------------------------------- T3 reversal table
ph = "ladder.diff.NOPROJ_WORD/float-vs-NOPROJ_FULL/float.fr3"
def cell(k):
    lo, hi = v(k + ".lo"), v(k + ".hi")
    kv = k if k in L else k + ".d"
    return f"{f(kv, 2, True)} {ci(k)}" + ("" if sig(lo, hi) else "$^{\\circ}$")
rev = [
    ("Document unit", "full raw float $-$ BM25, all queries", "project unit", cell("n2.project.all.raw_full-bm25"),
     "external unit", cell("n2.external.all.raw_full-bm25")),
    ("Cohort", "full sign code $-$ BM25, project unit", "rare bucket", cell("n2.project.rare.sym_full-bm25"),
     "all queries", cell("n2.project.all.sym_full-bm25")),
    ("Projection family", "word-only $-$ all channels, RealTalk", "no projection, float", cell(ph),
     "$k=96$ sign code", cell("chan.RealTalk.WORD")),
    ("Benchmark", "drop character channel", "PerLTQA", cell("chan.PerLTQA.WORD"), "LongMemEval", cell("chan.LME.WORD")),
    ("Metric", "fusion W $-$ BM25, LoCoMo", "E[T], docs (lower is better)", cell(fw + ".dE_T"), "FR@3", cell(fw + ".dFR3")),
    ("Tie convention$^{\\dagger}$", "external BM25 FR@3, LoCoMo (\\%)", "deterministic (fr3)", f("locomo_gap.external_reported", 2),
     "expected over ties (efr3)", f"{f('locomo_gap.mean.E_external_end_to_end', 2)} ({f('locomo_gap.arm_E_minus_reported', 2, True)})"),
]
body = "Choice & Quantity & Setting A & Value A & Setting B & Value B \\\\\n\\midrule\n" + "\n".join(" & ".join(r) + " \\\\" for r in rev)
write("tab_reversals", body, "One configuration choice at a time, everything else held fixed. FR@3 differences in pp unless stated. Intervals are 95\\% paired, archive-clustered bootstraps except the metric row (97.5\\%). $^{\\circ}$ interval includes 0: no significant difference was demonstrated.",
      "tab:reversals", "@{}l >{\\raggedright\\arraybackslash}p{3.4cm} >{\\raggedright\\arraybackslash}p{2.2cm} l >{\\raggedright\\arraybackslash}p{2.2cm} l@{}", size="\\footnotesize",
      note="$^{\\dagger}$ Included for completeness: the tie convention moves the number but reverses no verdict in this programme.")

# ---------------------------------------------------------------- T4 compaction and cost
MB = 1e6
rows = []
for lab, vk, bk, rk in (("LoCoMo", "locomo", "LoCoMo", "LoCoMo"), ("PerLTQA", "perltqa", "PerLTQA", "PerLTQA"),
                        ("LongMemEval", "lme", "LongMemEval", "LongMemEval"), ("RealTalk", None, "RealTalk", None)):
    enc = (f"{f(f'vocab.{vk}.stock', 1, scale=1 / MB, thousands=True)} $\\to$ {f(f'vocab.{vk}.compact', 1, scale=1 / MB, thousands=True)} & "
           f"{f(f'vocab.{vk}.saving_pct', 1)} & {f(f'vocab.{vk}.mismatch', 0)}/{f(f'vocab.{vk}.vectors', 0, thousands=True)} & {f(f'vocab.{vk}.latency', 2)}") if vk else "\\multicolumn{4}{c}{not measured}"
    bm = (f"{f(f'cbm25.{bk}.stock_bm25_bytes', 2, scale=1 / MB, thousands=True)} $\\to$ {f(f'cbm25.{bk}.compact_bm25_bytes', 2, scale=1 / MB, thousands=True)} & "
          f"{f(f'cbm25.{bk}.saving_pct', 1)} & {f(f'cbm25.{bk}.score_bit_mismatches', 0)}/{f(f'cbm25.{bk}.queries_compared', 0, thousands=True)} & {f(f'cbm25.{bk}.latency', 2)}")
    rat = (f"{f(f'ratio.{rk}.stock', 2)} & {f(f'ratio.{rk}.compact', 2)} & {f(f'ratio.{rk}.fused', 2)}") if rk else "-- & -- & --"
    rows.append(f"{lab} & {enc} & {bm} & {rat} \\\\")
body = ("& \\multicolumn{4}{c}{Encoder vocabulary} & \\multicolumn{4}{c}{BM25 index} & \\multicolumn{3}{c}{Encoder $\\div$ BM25} \\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}\\cmidrule(l){10-12}\n"
        "Benchmark & MB & $-$\\% & bits & time & MB & $-$\\% & bits & time & stock & compact & fusion \\\\\n\\midrule\n" + "\n".join(rows))
write("tab_compaction", body,
      "Bit-identical compaction. MB are summed over archives; \"bits\" counts differing outputs over all compared query vectors or query score lists; \"time\" is compact/stock latency. The last three columns compare resident bytes; \"fusion\" is BM25 + encoder + codes over compact BM25.",
      "tab:compaction", "@{}l r r r r r r r r r r r@{}", size="\\footnotesize",
      note=f"Owner chain F1--F4 on the encoder object graph: {f('f1.before', 0, thousands=True)} $\\to$ {f('f4.after', 0, thousands=True)} B ({f('f1f4.total_saving_pct', 2)}\\% less); warm single-query median {f('f4.ms_before', 2)} $\\to$ {f('f4.ms_after', 2)} ms. Byte counts are reachable-object accounting, not process RSS, and the stock BM25 is a plain Python dictionary implementation.")

# ---------------------------------------------------------------- T5 fusion
rows = []
for lab, b in (("LoCoMo", "LoCoMo"), ("PerLTQA", "PerLTQA"), ("LongMemEval", "LongMemEval"), ("RealTalk", "RealTalk")):
    W = f"fusion.{b}.W"; P = f"posthoc.{b}"
    rows.append(f"{lab} & {f(f'fusion.{b}.bm25.E_T', 2)} & {f(W + '.dE_T', 2, True)} {ci(W + '.dE_T')} & {f(W + '.dFR3', 2, True)} {ci(W + '.dFR3')} & "
                f"{f(P + '.dE_T', 2, True)} {ci(P + '.dE_T')} & {f(P + '.dFR3', 2, True)} {ci(P + '.dFR3')} & "
                f"{f(f'allev.{b}.W_loo.dall@5', 2, True)} & {f(f'allev.{b}.w0.1.dall@5', 2, True)} {ci(f'allev.{b}.w0.1.dall@5')} \\\\")
body = ("& & \\multicolumn{2}{c}{Gated arm W (weight out of fold)} & \\multicolumn{2}{c}{Post hoc, $w=0.1$} & \\multicolumn{2}{c}{$\\Delta$ all evidence in top 5 (pp)} \\\\\n"
        "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\\cmidrule(l){7-8}\n"
        "Benchmark & BM25 E[T] & $\\Delta$E[T] & $\\Delta$FR@3 & $\\Delta$E[T] & $\\Delta$FR@3 & W & $w=0.1$ \\\\\n\\midrule\n" + "\n".join(rows))
write("tab_fusion", body,
      "Fusion of BM25 with the 96-bit code by weighted reciprocal rank. E[T] in documents opened (lower is better), FR@3 in pp. E[T] and FR@3 intervals are 97.5\\% (Bonferroni over two arms); all-evidence intervals are 95\\%.",
      "tab:fusion", "@{}l r l l l l r l@{}", size="\\footnotesize",
      note=f"The $w=0.1$ column was chosen after seeing the weight grid and was never gated. On LoCoMo it reaches E[T] {f('posthoc.LoCoMo.E_T', 2)}, a cut of {num(-100 * v('posthoc.LoCoMo.dE_T') / v('fusion.LoCoMo.bm25.E_T'), 1)}\\%, short of the {f('gate.fusion.min_cut_pct', 0)}\\% primary threshold.")

# ---------------------------------------------------------------- T6 closed routes
cr = [
    ("Fewer bits: 12 B instead of 48 B per document", f"48 B minus 12 B, LoCoMo FR@3 (four cells, all significant)",
     f"{f('n2.project.rare.sym_384-sym_96', 2, True)} to {f('n2.external.all.sym_384-sym_96', 2, True)} pp"),
    ("Drop the character channel", "channel ablation, four benchmarks", f"two significant regressions (LME {f('chan.LME.WORD.d', 2, True)} pp)"),
    ("Shared hashed encoder, no vocabulary", "FR@3 per-archive $\\to$ shared", f"LME {f('hashed.LME.base192.fr3', 2)} $\\to$ {f('hashed.LME.shared_seed2026091601.fr3', 2)}\\%"),
    ("Code first stage, BM25 rerank", "C3 gate", f"LoCoMo {f('gate.c3.LoCoMo.delta', 2, True)}, LME {f('gate.c3.LME.delta', 2, True)} pp"),
    ("Unweighted RRF of BM25 and code", "LoCoMo, 2026-09-16 configuration", f"FR@3 {f('rrf16.locomo.fr3', 2, True)} {ci('rrf16.locomo.fr3')} pp"),
    ("Code-based adaptive penalty", "policy-shaped routing", f"E[T] {f('policy.code.delta', 2, True)} docs; BM25 control rejects it ($\\lambda=0$)"),
    ("Weighted RRF, weight out of fold", "fusion gate", f"LoCoMo FR@3 {f('fusion.LoCoMo.W.dFR3', 2, True)} pp"),
]
body = "Route & Test & Result \\\\\n\\midrule\n" + "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in cr)
write("tab_closed", body, "Routes closed by measurement.", "tab:closed", "@{}>{\\raggedright\\arraybackslash}p{5.0cm} >{\\raggedright\\arraybackslash}X >{\\raggedright\\arraybackslash}p{5.2cm}@{}")

# ---------------------------------------------------------------- T7 correction log (own errors)
corr = [
    ("2026-09-17 $\\to$ 09-20", "Accumulation-order hypothesis recorded as REFUTED; withdrawn",
     f"{f('corr.t1.permutations', 0)} forced permutations against a {f('corr.t1.event_rate_pct', 1)}\\% event miss it with probability {f('corr.t1.p_miss', 2)}; the null was uninformative"),
    ("2026-09-20", "Bigram-analyser explanation of the LoCoMo gap proposed and falsified", "the project's frozen arm already used that analyser"),
    ("2026-09-20", "Rare-bucket subgroup quoted as a LoCoMo-wide result",
     f"48 B $-$ 12 B is {f('n2.project.rare.sym_384-sym_96', 2, True)} pp in the rare bucket (n = {f('n2.project.n_rare', 0)}) but {f('n2.project.all.sym_384-sym_96', 2, True)} on all {f('n2.project.n', 0, thousands=True)} queries"),
    ("2026-09-20", "Claim-screen denominator", f"{f('p4.retrieval_units', 0)} retrieval claims, not one more: a heading line had merged into a paragraph"),
    ("2026-09-20", "Sign bug in the claim trace index", "negative-valued claims looked untraceable; matching by absolute value fixed it"),
    ("2026-09-21", "Resident memory described as dense float arrays",
     f"measured: character vocabulary {f('resident.cv_char_vectorizer', 2, scale=1 / MB)} MB and word vocabulary {f('resident.wv_word_vectorizer', 2, scale=1 / MB)} MB"),
    ("2026-09-21", "LoCoMo channel result described as \"neutral\"",
     f"reworded: no significant difference was demonstrated, {ci('chan.LoCoMo.WORD')} pp"),
    ("2026-09-21", "RealTalk word-only lead from unprojected arms", f"reversed at $k=96$: {f('chan.RealTalk.WORD.d', 2, True)} pp"),
    ("2026-09-22", "Codex role summary read as a count of distinct roles", "it is the bitwise OR of role masks; the package was right"),
    ("2026-09-22", "Policy-shaped gate written without a minimum effect", f"passed while closing {f('policy.closed_bm25_pct', 1)}\\% of the gap to BM25 and {f('policy.closed_floor_pct', 2)}\\% of the gap to the floor"),
    ("2026-09-23", "Compact BM25 size estimated, not measured",
     f"estimate {f('corr.bm25est.estimate_kB', 0)} kB ({f('corr.bm25est.ratio_est', 1)}$\\times$); measured {f('corr.bm25est.measured_bytes', 0, thousands=True)} B ({f('corr.bm25est.ratio_meas', 2)}$\\times$)"),
]
body = "Date & What was wrong & Correction \\\\\n\\midrule\n" + "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in corr)
write("tab_corrections", body, "The head researcher's own errors in this programme, all corrected in the record where they appeared.",
      "tab:corrections", "@{}l >{\\raggedright\\arraybackslash}p{5.2cm} >{\\raggedright\\arraybackslash}X@{}", size="\\footnotesize")

# ---------------------------------------------------------------- T8 supersession ledger
ids = sorted(k[len("sup.id."):] for k in L if k.startswith("sup.id."))
def esc(x): return x.replace("_", "\\_")
rows = [f"\\texttt{{{esc(i)}}} & {s('sup.id.' + i).replace('_', ' ').lower()} \\\\" for i in ids]
half = (len(rows) + 1) // 2
pairs = [rows[j][:-3] + " & " + (rows[j + half] if j + half < len(rows) else " & \\\\") for j in range(half)]
write("tab_supersession", "Entry & Status & Entry & Status \\\\\n\\midrule\n" + "\n".join(pairs),
      f"The programme's supersession ledger of 2026-09-17: {f('sup.entries', 0)} entries, of which {num(v('sup.status.RETRACTED') + v('sup.status.FULLY_RETRACTED'), 0)} are retractions.",
      "tab:supersession", "@{}l X l X@{}", size="\\footnotesize")

# ---------------------------------------------------------------- A1 C1 grid
rows = []
for arm, lab in (("k96/sym", "12"), ("k96/qscale", "12"), ("k192/sym", "24"), ("k192/qscale", "24"), ("k384/sym", "48"), ("k384/qscale", "48")):
    cells = []
    for comp in ("BM25_coarse", "BM25_frozen"):
        k = f"c1.{arm}.{comp}"
        cells += [f"{f(k + '.fr3', 2, True)} {ci(k + '.fr3')}", f"{f(k + '.hit10', 2, True)} {ci(k + '.hit10')}"]
    rows.append(f"\\texttt{{{arm}}} & {lab} & " + " & ".join(cells) + " \\\\")
body = ("& & \\multicolumn{2}{c}{vs BM25, coarse analyser} & \\multicolumn{2}{c}{vs BM25, production analyser} \\\\\n\\cmidrule(lr){3-4}\\cmidrule(l){5-6}\n"
        "Arm & B/doc & $\\Delta$FR@3 & $\\Delta$Hit@10 & $\\Delta$FR@3 & $\\Delta$Hit@10 \\\\\n\\midrule\n" + "\n".join(rows))
write("tab_c1", body, "C1 gate, all twelve cells (RealTalk, pp, 95\\% intervals).", "tab:c1", "@{}l r l l l l@{}", size="\\footnotesize")

# ---------------------------------------------------------------- A2 N2 four cells
rows = []
for cname, lab in (("sym_384-sym_96", "48 B $-$ 12 B sign"), ("sym_384-bm25", "48 B sign $-$ BM25"), ("sym_full-bm25", "full sign $-$ BM25"),
                   ("std_384-bm25", "48 B standardized $-$ BM25"), ("raw_full-bm25", "full raw float $-$ BM25")):
    cells = []
    for u, c in (("project", "rare"), ("project", "all"), ("external", "rare"), ("external", "all")):
        k = f"n2.{u}.{c}.{cname}"
        cells.append(f"{f(k, 2, True)} {ci(k)}" if (k + ".lo") in L else f(k, 2, True))
    rows.append(f"{lab} & " + " & ".join(cells) + " \\\\")
body = ("& \\multicolumn{2}{c}{Project unit} & \\multicolumn{2}{c}{External unit} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(l){4-5}\n"
        "Contrast (FR@3, pp) & rare bucket & all queries & rare bucket & all queries \\\\\n\\midrule\n" + "\n".join(rows))
write("tab_n2", body, "LoCoMo contrasts under both document units and both cohorts (95\\% intervals).", "tab:n2", "@{}l l l l l@{}", size="\\footnotesize")

# ---------------------------------------------------------------- A3 channel ablation
rows = []
for lab, b in (("LongMemEval", "LME"), ("RealTalk", "RealTalk"), ("LoCoMo", "LoCoMo"), ("PerLTQA", "PerLTQA")):
    full = f"chan.{b}.LSA_WORD_CHAR"
    cells = [f"{f(full + '.fr3', 2)}"]
    for m in ("WORD", "LSA_WORD"):
        k = f"chan.{b}.{m}"
        cells.append(f"{f(k + '.d', 2, True)} {ci(k)}")
    cells.append(f"{num(100 * (1 - v(f'chan.{b}.WORD.mb') / v(full + '.mb')), 0)}")
    rows.append(f"{lab} & " + " & ".join(cells) + " \\\\")
body = "Benchmark & all channels FR@3 & word only $-$ all & word+LSA $-$ all & memory saved by word only (\\%) \\\\\n\\midrule\n" + "\n".join(rows)
write("tab_channels", body, "Channel ablation at $k=96$ with sign codes (pp, 95\\% intervals).", "tab:channels", "@{}l r l l r@{}", wide=False, size="\\footnotesize")

# ---------------------------------------------------------------- A4 RealTalk ladder
arms = sorted({k.split(".")[1] for k in L if k.startswith("ladder.") and not k.startswith("ladder.diff")})
order = ["BM25_frozen/-", "BM25_coarse/-"] + [a for a in arms if a.startswith("NOPROJ")] + [a for a in arms if a.startswith("k")]
rows = [f"\\texttt{{{esc(a)}}} & {f(f'ladder.{a}.hit10', 2)} & {f(f'ladder.{a}.fr3', 2)} \\\\" for a in order]
write("tab_ladder", "Arm & Hit@10 & FR@3 \\\\\n\\midrule\n" + "\n".join(rows), "RealTalk ladder, all seventeen arms (\\%). NOPROJ arms are unprojected and not compact.",
      "tab:ladder", "@{}l r r@{}", wide=False, size="\\footnotesize")

(HERE / "tables_used_keys.txt").write_text("\n".join(sorted(USED)), encoding="utf-8")
print(len(list(TAB.glob("*.tex"))), "tables;", len(USED), "ledger keys used")
