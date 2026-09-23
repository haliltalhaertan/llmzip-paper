"""Automated checks of llmzip_paper against CLAIMS_LEDGER.csv. Writes paper/PAPER_VERIFICATION.json."""
import csv, json, re
from pathlib import Path

P = Path("paper")
L = {r["claim_id"]: r["value"] for r in csv.DictReader(open(P / "CLAIMS_LEDGER.csv", encoding="utf-8"))}
NUMS = []
for v in L.values():
    try:
        NUMS.append(float(v))
    except ValueError:
        pass
REPORT = {}
NUMRE = re.compile(r"(?<![\w.])(?:\\textminus\{\}|-)?\d[\d{},]*(?:\.\d+)?")


def parse(tok):
    neg = tok.startswith("\\textminus{}") or tok.startswith("-")
    t = tok.replace("\\textminus{}", "").lstrip("-").replace("{,}", "").replace(",", "")
    return (-1 if neg else 1) * float(t), (len(t.split(".")[1]) if "." in t else 0)


# 1. template: numbers outside placeholders must be structural constants
tmpl = (P / "llmzip_paper.tmpl.tex").read_text(encoding="utf-8")
body = tmpl[tmpl.index("\\begin{document}"):]
body = re.sub(r"«[^»]+»", " ", body)
body = re.sub(r"\\(label|ref|cite[pt]?|input|includegraphics|bibliography|bibliographystyle|texttt|url)(\[[^\]]*\])?\{[^}]*\}", " ", body)
body = re.sub(r"\\(begin|end)\{[^}]*\}(\[[^\]]*\])?", " ", body)
body = re.sub(r"%.*", " ", body)
STRUCT = {
    "1": "one / BM25 k1 unit", "1.2": "BM25 k1", "0.75": "BM25 b", "2": "BM25 bound constant / COUNT>=2 / N/(2K)",
    "3": "top-3 / trigram", "5": "top-5 / 5-gram", "10": "top-10", "12": "bytes per document / N=12", "24": "bytes",
    "48": "bytes", "50": "rerank depth", "61": "RRF constant", "96": "bits / dimensions", "192": "dimensions",
    "384": "dimensions", "0.1": "fusion weight", "4": "N", "8": "N", "3.14.7": "CPython", "2.5.3": "NumPy",
    "1.18.1": "SciPy", "1.9.1": "scikit-learn", "2026": "year", "23": "date", "17": "date", "0": "lambda=0 / gap 0",
    "256": "SHA-256", "-2": "word 1--2 grams", "-5": "character 3--5 grams", "96,192,384": "k grid", "5,": "all@5",
    "3.14": "CPython 3.14.7", "2.5": "NumPy 2.5.3", "1.18": "SciPy 1.18.1", "1.9": "scikit-learn 1.9.1",
    "90": "90th percentile", "4.0": "licence version (CC BY 4.0)", "95": "default interval level (ledger gate.c1.ci)",
}
lits = []
for m in NUMRE.finditer(body):
    tok = m.group().replace("{,}", ",")
    ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
    lits.append({"literal": tok, "structural": tok in STRUCT, "why": STRUCT.get(tok, ""), "context": ctx})
REPORT["template_literals"] = {"n": len(lits), "non_structural": [l for l in lits if not l["structural"]], "all": lits}

# 2. rendered prose values equal ledger values
used = json.loads((P / "prose_used_keys.json").read_text(encoding="utf-8"))
bad = []
for k, v in used.items():
    if k.startswith(("expr:", "meta:")):
        continue
    base = k
    if base in L:
        try:
            lv = float(L[base])
        except ValueError:
            continue
        cands = [lv]
        if k.endswith((".lo", ".hi")):
            other = k[:-3] + (".hi" if k.endswith(".lo") else ".lo")
            cands.append(float(L[other]))
        if not any(abs(abs(v) - abs(c) * s) < 1e-9 * max(1, abs(c * s)) for c in cands for s in (1, 1e-6, 1e-3, 100)):
            bad.append((k, v, L[base]))
REPORT["prose_values"] = {"placed": len(used), "mismatch": bad}

# 3. table numbers traced to ledger at printed precision
def traced(x, d):
    tol = 0.5 * 10 ** (-d) + 1e-12
    for s in (1, 1e-6, 1e-3, 100):
        for n in NUMS:
            if abs(abs(x) - abs(n * s)) <= tol:
                return True
    return False

vocab_sum = sum(float(L[f"vocab.{b}.vectors"]) for b in ("locomo", "perltqa", "lme"))
TAB_STRUCT = {"2026": "date", "96": "k=96 configuration", "20{,}540": f"derived: sum of vocab.*.vectors = {vocab_sum:.0f}"}
assert vocab_sum == 20540
REPORT["table_structural_literals"] = TAB_STRUCT
tab = {}
for f in sorted((P / "tables").glob("*.tex")):
    t = f.read_text(encoding="utf-8")
    t = re.sub(r"\\(label|ref|begin|end|cmidrule|multicolumn|texttt)(\([^)]*\))?\{[^}]*\}(\{[^}]*\})?(\{[^}]*\})?", " ", t)
    t = re.sub(r"p\{[\d.]+cm\}|\{[\d.]+cm\}|@\{\}", " ", t)
    miss = []
    for m in NUMRE.finditer(t):
        x, d = parse(m.group())
        if m.group() in TAB_STRUCT:
            continue
        if not traced(x, d):
            miss.append({"literal": m.group(), "context": t[max(0, m.start() - 50):m.end() + 30].replace("\n", " ")})
    tab[f.name] = miss
REPORT["table_untraced"] = tab

# 4. citations
tex = (P / "llmzip_paper.tex").read_text(encoding="utf-8")
cites = set(k.strip() for grp in re.findall(r"\\cite[pt]?\{([^}]*)\}", tex) for k in grp.split(","))
bibkeys = set(re.findall(r"@\w+\{([^,]+),", (P / "references.bib").read_text(encoding="utf-8")))
chk = list(csv.DictReader(open(P / "REFERENCES_CHECK.csv", encoding="utf-8")))
REPORT["citations"] = {"cited": sorted(cites), "missing_from_bib": sorted(cites - bibkeys), "bib_entries": len(bibkeys),
                       "check_rows": len(chk), "cited_not_resolved": sorted(r["key"] for r in chk if r["key"] in cites and str(r["resolved"]).lower() not in ("true", "1", "yes")),
                       "cited_without_check_row": sorted(cites - {r["key"] for r in chk})}

# 5. every label referenced
alltex = tex + "".join(f.read_text(encoding="utf-8") for f in (P / "tables").glob("*.tex"))
labels = set(re.findall(r"\\label\{([^}]+)\}", alltex))
refs = set(re.findall(r"\\ref\{([^}]+)\}", alltex))
REPORT["labels"] = {"n": len(labels), "unreferenced": sorted(l for l in labels if l not in refs and not l.startswith("sec:"))}

# 6. claim titles hold for every plotted row
def fl(k): return float(L[k])
claims = {
    "fig2a no compact cell reaches BM25": all(fl(f"c1.{a}.{c}.fr3") < 0 for a in ("k96/sym", "k96/qscale", "k192/sym", "k192/qscale", "k384/sym", "k384/qscale") for c in ("BM25_coarse", "BM25_frozen")),
    "fig2d shared encoder roughly halves FR@3 (ratio 0.40-0.55)": all(0.40 <= fl(f"hashed.{b}.shared_seed2026091601.fr3") / fl(f"hashed.{b}.base192.fr3") <= 0.55 for b in ("LME", "PerLTQA", "LoCoMo")),
    "fig3a codes are 0.3% of resident": round(100 * fl("resident.packed_doc_codes") / fl("resident.union"), 1) == 0.3,
    "fig3c compacting both widens the gap": all(fl(f"ratio.{b}.compact") > fl(f"ratio.{b}.stock") for b in ("LoCoMo", "PerLTQA", "LongMemEval")),
    "fig4b BM25 control chooses lambda=0": fl("policy.bm25.delta") == 0.0,
    "fig5 post-hoc w=0.1 lowers E[T] on all four (CI below 0)": all(fl(f"posthoc.{b}.dE_T.hi") < 0 for b in ("LoCoMo", "PerLTQA", "LongMemEval", "RealTalk")),
    "fig5 post-hoc FR@3 lower bounds above -1": all(fl(f"posthoc.{b}.dFR3.lo") > -1 for b in ("LoCoMo", "PerLTQA", "LongMemEval", "RealTalk")),
    "fig6a martingale is 0 at every N and no other family is 0 at every N": all(fl(f"codex.gap.martingale_penalty.N{n}") == 0 for n in (4, 8, 12)) and all(any(fl(f"codex.gap.{k}.N{n}") > 0 for n in (4, 8, 12)) for k in ("bundled", "fully_split_with_cost_sharing", "hard_nonanticipativity_60s")),
    "reversal: projection family flips sign, both significant": fl("ladder.diff.NOPROJ_WORD/float-vs-NOPROJ_FULL/float.fr3.lo") > 0 and fl("chan.RealTalk.WORD.hi") < 0,
    "reversal: benchmark flips sign, both significant": fl("chan.PerLTQA.WORD.lo") > 0 and fl("chan.LME.WORD.hi") < 0,
    "reversal: document unit flips significance": fl("n2.project.all.raw_full-bm25.hi") < 0 and fl("n2.external.all.raw_full-bm25.lo") < 0 < fl("n2.external.all.raw_full-bm25.hi"),
    "reversal: cohort flips significance": fl("n2.project.rare.sym_full-bm25.hi") < 0 and fl("n2.project.all.sym_full-bm25.lo") < 0 < fl("n2.project.all.sym_full-bm25.hi"),
    "reversal: metric, E[T] better and FR@3 worse, both significant": fl("fusion.LoCoMo.W.dE_T.hi") < 0 and fl("fusion.LoCoMo.W.dFR3.hi") < 0,
    "tie convention reverses nothing (magnitude only, < 0.1 pp)": abs(fl("locomo_gap.arm_E_minus_reported")) < 0.1,
    "48B sign vs BM25 non-significant in all four cells": all(L[f"n2.{u}.{c}.sym_384-bm25.sig"] == "False" for u in ("project", "external") for c in ("rare", "all")),
    "eleven own corrections in Table corrections": (P / "tables" / "tab_corrections.tex").read_text(encoding="utf-8").count("\\\\\n") - 1 == 11,
    "supersession: 8 retractions of 20": fl("sup.status.RETRACTED") + fl("sup.status.FULLY_RETRACTED") == 8 and fl("sup.entries") == 20,
}
REPORT["claims"] = claims

# 7. labels on the title page; log clean
REPORT["four_labels_present"] = all(x in tex for x in ("LOCAL EXPLORATORY PILOT", "NOT PREREGISTERED", "NOT FOR CITATION", "DISCLOSE-BEFORE-USE"))
log = (P / "llmzip_paper.log").read_text(encoding="latin-1")
REPORT["log"] = {"errors": [l for l in log.splitlines() if l.startswith("!")],
                 "warnings": [l for l in log.splitlines() if re.search(r"LaTeX Warning|Overfull|undefined", l)],
                 "pages": int(re.search(r"\((\d+) pages", log).group(1))}
REPORT["summary"] = {
    "template_non_structural_literals": len(REPORT["template_literals"]["non_structural"]),
    "prose_mismatches": len(bad),
    "table_untraced": sum(len(v) for v in tab.values()),
    "missing_citations": len(REPORT["citations"]["missing_from_bib"]) + len(REPORT["citations"]["cited_not_resolved"]) + len(REPORT["citations"]["cited_without_check_row"]),
    "unreferenced_labels": len(REPORT["labels"]["unreferenced"]),
    "claims_failed": [k for k, ok in claims.items() if not ok],
    "log_errors": len(REPORT["log"]["errors"]), "log_warnings": len(REPORT["log"]["warnings"]),
}
(P / "PAPER_VERIFICATION.json").write_text(json.dumps(REPORT, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(REPORT["summary"], indent=1))
