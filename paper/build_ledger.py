"""Provenance script: builds CLAIMS_LEDGER.csv from the programme's private run records.

It cannot run from this repository alone. It needs the private development archive, located by the
environment variables LLMZIP_WORK, LLMZIP_REPO, CODEX_PACKAGE and LLMZIP_ARTEFACTS. It is published so that
every ledger entry's extraction rule (file, field, recomputation, seed) can be read. Everything
downstream of the ledger (figures, tables, paper, verification) runs from this repository: see build_all.py.
"""
"""Build CLAIMS_LEDGER.csv: every number the paper quotes, read from its source.

[LOCAL EXPLORATORY PILOT] [NOT PREREGISTERED] [NOT FOR CITATION] [DISCLOSE-BEFORE-USE]

Runs inside the analysis kernel (needs `host` for artifact paths). No value is
typed by hand: each row is read from a saved artifact (identified by version id)
or from a file on disk (identified by path and sha256). Bootstrap intervals that
were computed in-session are recomputed here with the same seed and loop order.
"""
import collections, csv, hashlib, io, json, os, re, zipfile
from pathlib import Path
import numpy as np

ROWS = []
SRC_SHA = {}


def add(cid, value, unit, src, field, meaning):
    ROWS.append({"claim_id": cid, "value": value, "unit": unit, "source": src,
                 "field": field, "meaning": meaning})


def artifact_path(vid):
    """Saved run records are addressed by artefact id; LLMZIP_ARTEFACTS holds them as <id>/<file>."""
    hits = list(Path(os.environ.get("LLMZIP_ARTEFACTS", "artefacts")).glob(f"*{vid}*/*")) + \
           list(Path(os.environ.get("LLMZIP_ARTEFACTS", "artefacts")).glob(f"*{vid}*"))
    files = [h for h in hits if h.is_file()]
    assert files, f"artefact {vid} not found under LLMZIP_ARTEFACTS"
    return str(files[0])


def art(vid):
    p = Path(artifact_path(vid))
    SRC_SHA[f"artifact:{vid}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text(encoding="utf-8")) if p.suffix == ".json" else p.read_text(encoding="utf-8")


def disk(path):
    p = Path(path)
    b = p.read_bytes()
    SRC_SHA[f"file:{p}"] = hashlib.sha256(b).hexdigest()
    return json.loads(b.decode("utf-8")) if p.suffix == ".json" else b.decode("utf-8", "replace")


W = Path(os.environ.get("LLMZIP_WORK", "llmzip-work"))
RE = Path(os.environ.get("LLMZIP_REPO", "llmzip")) / "repro"
RT = W / "review_transfer" / "certificate_memory_longmemeval_retry_v2"
CX = Path(os.environ.get("CODEX_PACKAGE", "codex-package"))

# ------------------------------------------------------------------ T1 + seal
a = "e0553704-d20f-4201-8ab0-78585038dba4"; d = art(a); s = f"artifact:{a}"
t = d["totals"]
add("t1.evaluations", t["evaluations"], "count", s, "totals.evaluations", "T1 cell evaluations across sessions")
add("t1.exact", t["exact_match"], "count", s, "totals.exact_match", "evaluations bit-identical to published")
add("t1.deviating", t["deviating"], "count", s, "totals.deviating", "evaluations deviating (all one cell)")
add("t1.bistable_published", t["published_value"], "pp", s, "totals.published_value", "BM25/coarse_idfonly/FR@3 as published")
add("t1.bistable_alt", t["deviating_value"], "pp", s, "totals.deviating_value", "same cell under PYTHONHASHSEED 99/777")
add("t1.bistable_diff", round(t["deviating_value"] - t["published_value"], 10), "pp", s, "derived", "difference = 1/25 of one of 141 queries")
a = "d4e8dd7a-e8b6-431d-b62d-9143dfce76cd"; txt = art(a)
rows = list(csv.DictReader(io.StringIO(txt)))
add("t1.cells", len(rows), "count", f"artifact:{a}", "rows", "published T1 cells re-run")
add("t1.cells_match", sum(r["verdict"] == "MATCH" for r in rows), "count", f"artifact:{a}", "verdict==MATCH", "cells matching at the published hash seed")
a = "bc23c25c-884f-4879-88cb-1c85366172db"; d = art(a); s = f"artifact:{a}"
add("seal.entries", d["base_seal"]["entries"], "count", s, "base_seal.entries", "files in the authoritative seal")
add("seal.changed", d["verdict"]["files_changed"], "count", s, "verdict.files_changed", "sealed files edited in place on 2026-09-18")
add("seal.numeric_changed", str(d["verdict"]["numeric_logic_changed"]), "bool", s, "verdict.numeric_logic_changed", "whether any numeric logic changed")

# ------------------------------------------------------------------ C1 gate
a = "f05ba158-4c30-4cd7-b204-86524d3513e5"; d = art(a); s = f"artifact:{a}"
add("c1.n_queries", d["n_queries"], "count", s, "n_queries", "RealTalk queries in the C1 evaluation")
for comp, v in d["verdict_fr3"].items():
    add(f"c1.passed.{comp.split('/')[0]}", str(v["passed"]), "bool", s, f"verdict_fr3.{comp}.passed", "C1 gate outcome on FR@3")
for r in d["table"]:
    k = f"c1.{r['arm']}.{r['comparator'].split('/')[0]}"
    for m in ("fr3", "hit10"):
        add(f"{k}.{m}", r[f"{m}_pp"], "pp", s, f"table[{r['arm']},{r['comparator']}].{m}_pp", f"{r['bytes']} B/doc arm minus BM25, {m}")
        add(f"{k}.{m}.lo", r[f"{m}_lo"], "pp", s, f"...{m}_lo", "95% lower bound")
        add(f"{k}.{m}.hi", r[f"{m}_hi"], "pp", s, f"...{m}_hi", "95% upper bound")
fid = d["fidelity_gate"]
add("c1.fidelity", json.dumps(fid)[:120], "json", s, "fidelity_gate", "producer fidelity gate")

# ------------------------------------------------------------------ LoCoMo gap
a = "b9f3fc00-cbc3-47db-b6eb-d10374b596d7"; d = art(a); s = f"artifact:{a}"
for k, v in d["means_pp"].items():
    add(f"locomo_gap.mean.{k}", v, "pp", s, f"means_pp.{k}", "BM25 FR@3 under document-unit arm")
for k, v in d["decomposition_pp"].items():
    add(f"locomo_gap.{k}", v, "pp", s, f"decomposition_pp.{k}", "gap decomposition")
add("locomo_gap.captions_docs", d["document_differences_found"]["project_appends_image_captions"], "count", s,
    "document_differences_found.project_appends_image_captions", "documents with appended image captions")
add("locomo_gap.external_reported", d["external_reported"]["value"], "pp", s, "external_reported.value", "external package fr3")
add("locomo_gap.external_n", d["external_reported"]["n"], "count", s, "external_reported.n", "external package cohort")
a = "f8fb5142-b8fc-4def-b684-d1defa6348f4"; d = art(a); s = f"artifact:{a}"
add("locomo_gap.analyser_loose", d["means_pp"]["loose"], "pp", s, "means_pp.loose", "BM25 FR@3, loose analyser")
add("locomo_gap.analyser_frozen", d["means_pp"]["frozen"], "pp", s, "means_pp.frozen", "BM25 FR@3, frozen analyser")
add("locomo_gap.analyser_external", d["means_pp"]["external_1_2gram"], "pp", s, "means_pp.external_1_2gram", "BM25 FR@3, external analyser")

# ------------------------------------------------------------------ estimand registry
a = "fb2bf452-8989-4c11-ad14-cbaf31d66285"; d = art(a); s = f"artifact:{a}"
add("p4.units", d["units_total"], "count", s, "units_total", "claim units in the reading layer")
add("p4.retrieval_units", d["units_retrieval_estimand"], "count", s, "units_retrieval_estimand", "retrieval claims")
for k, v in d["coverage_over_retrieval_units"].items():
    add(f"p4.names.{k}", v, "count", s, f"coverage_over_retrieval_units.{k}", "retrieval claims naming this field")
add("p4.all_five", d["name_all_five"], "count", s, "name_all_five", "retrieval claims naming all five fields")
for k, v in d["provenance_tracing"].items():
    if isinstance(v, int):
        add(f"p4.trace.{k}", v, "count", s, f"provenance_tracing.{k}", "claim provenance tracing")

# ------------------------------------------------------------------ N2 two units
a = "c7547751-16b4-479a-94a4-ba611e5b9def"; d = art(a); s = f"artifact:{a}"
for unit in ("project", "external"):
    u = d[unit]
    add(f"n2.{unit}.n", u["n_queries"], "count", s, f"{unit}.n_queries", "queries")
    add(f"n2.{unit}.n_rare", u["n_rare"], "count", s, f"{unit}.n_rare", "rare-bucket queries")
    for coh in ("rare_bucket_fr3", "all_queries_fr3"):
        for arm, v in u[coh].items():
            add(f"n2.{unit}.{coh}.{arm}", v, "pp", s, f"{unit}.{coh}.{arm}", "FR@3")
    for key, coh in (("contrasts", "rare"), ("contrasts_all_queries", "all")):
        for cname, cv in u[key].items():
            base = f"n2.{unit}.{coh}.{cname}"
            add(base, cv["delta_pp"], "pp", s, f"{unit}.{key}.{cname}.delta_pp", "FR@3 contrast")
            add(base + ".lo", cv["ci95"][0], "pp", s, f"{unit}.{key}.{cname}.ci95[0]", "95% lower")
            add(base + ".hi", cv["ci95"][1], "pp", s, f"{unit}.{key}.{cname}.ci95[1]", "95% upper")
            add(base + ".sig", str(cv.get("significant")), "bool", s, f"{unit}.{key}.{cname}.significant", "")

# ------------------------------------------------------------------ footprint + resident
a = "ea20964a-4480-44d7-bc0e-4fae9a9acdd6"; txt = art(a)
for r in csv.DictReader(io.StringIO(txt)):
    b = r["benchmark"]
    for k in ("archives", "median_raw_text_bytes", "median_documents", "bytes_per_document"):
        add(f"text.{b}.{k}", float(r[k]) if "." in r[k] else int(r[k]), "bytes" if "bytes" in k else "count",
            f"artifact:{a}", k, "raw text per archive")
a = "56fd415d-c317-46f6-bc9c-ad1770c40af8"; d = art(a); s = f"artifact:{a}"
for k, v in d["totals_bytes"].items():
    add(f"resident.{k}", v, "bytes", s, f"totals_bytes.{k}", "LoCoMo serving bytes, 10 archives")
add("resident.union", d["union_serving_bytes"], "bytes", s, "union_serving_bytes", "union serving bytes")
add("resident.raw_text", d["raw_text_bytes"], "bytes", s, "raw_text_bytes", "raw text bytes")
add("resident.construction", sum(r["construction_matrices_bytes"] for r in d["per_archive"]), "bytes", s,
    "sum(per_archive.construction_matrices_bytes)", "construction matrices, not serving")

# ------------------------------------------------------------------ owner F1-F5
z = zipfile.ZipFile(W / "publication_all_findings_v1" / "LLMZIP_ALL_FINDINGS_PUBLICATION_V1.zip")
inner_b = z.read("research_all_findings_v1/llmzip_all_findings_v1_safe.zip")
inner = zipfile.ZipFile(io.BytesIO(inner_b))
f5b = inner.read("publication_all_findings_v1/evidence/benchmark_all_v1/SUMMARY.json")
s = "file:LLMZIP_ALL_FINDINGS_PUBLICATION_V1.zip!safe.zip!evidence/benchmark_all_v1/SUMMARY.json"
SRC_SHA[s] = hashlib.sha256(f5b).hexdigest()
f5 = json.loads(f5b)
add("f5.archives", f5["completed_archives"], "count", s, "completed_archives", "F5 archives completed")
for b, v in f5["summary"].items():
    add(f"f5.{b}.queries", v["queries"], "count", s, f"summary.{b}.queries", "F5 queries")
    add(f"f5.{b}.flips", v["dual_doc_flips"] + v["dual_query_flips"], "count", s, f"summary.{b}.dual_*_flips", "dual64 vs float32 flips")
    for arm, m in v["arms"].items():
        for k in ("memory_median_bytes", "query_wall_median_ms", "hit10", "recall10"):
            add(f"f5.{b}.{arm}.{k}", m[k], k.split("_")[-1] if "_" in k else "fraction", s, f"summary.{b}.arms.{arm}.{k}", "F5 cost/quality")
cf = z.read("research_all_findings_v1/CANONICAL_FINDINGS.md").decode("utf-8")
s2 = "file:LLMZIP_ALL_FINDINGS_PUBLICATION_V1.zip!CANONICAL_FINDINGS.md"
SRC_SHA[s2] = hashlib.sha256(cf.encode("utf-8")).hexdigest()
F14 = [("f1.before", r"object-graph bytes: \*\*(\d+) →", "F1 retained encoder bytes before"),
       ("f1.after", r"object-graph bytes: \*\*\d+ → (\d+)\*\*", "F1 after owner compaction"),
       ("f2.after", r"float32 graph \*\*(\d+)\*\*", "F2 after float32 final SVD"),
       ("f4.after", r"dual \*\*(\d+)\*\*", "F4 dual deployment named-root bytes"),
       ("f4.ms_before", r"old median ([\d.]+) ms", "F4 warm query, old"),
       ("f4.ms_after", r"dual ([\d.]+) ms \(ratio", "F4 warm query, dual"),
       ("f3.payload_saving_pct", r"\*\*([\d.]+)%\*\* component-payload saving", "F3 component payload saving")]
for cid, pat, meaning in F14:
    m = re.search(pat, cf)
    add(cid, float(m.group(1)) if "." in m.group(1) else int(m.group(1)), "bytes" if "ms" not in cid and "pct" not in cid else ("ms" if "ms" in cid else "%"),
        s2, f"regex {pat}", meaning)
_b = next(r["value"] for r in ROWS if r["claim_id"] == "f1.before")
_a = next(r["value"] for r in ROWS if r["claim_id"] == "f4.after")
add("f1f4.total_saving_pct", 100 * (1 - _a / _b), "%", s2, "derived f4.after/f1.before", "F1-F4 combined, single QID")

# ------------------------------------------------------------------ prior owner ideas
F1 = W / "incoming_20260916b/extracted/LLMZIP_FIKIR1_METIN_YENIDEN_SIRALAMA_2026-09-16/LLMZIP_FIKIR1_2026-09-16/results"
d = disk(F1 / "rerank_summary.json"); s = f"file:{F1 / 'rerank_summary.json'}"
for b in ("LME", "PerLTQA", "LoCoMo"):
    for arm in ("BM25_full", "qscale96", "qscale96_bm25", "float_raw32_bm25"):
        add(f"rerank.{b}.{arm}.fr3", d[b][arm]["fr3"], "fraction", s, f"{b}.{arm}.fr3", "idea 1: compact first stage, BM25 rerank")
        add(f"rerank.{b}.{arm}.hit10", d[b][arm]["hit10"], "fraction", s, f"{b}.{arm}.hit10", "idea 1")
IK = W / "incoming_20260916b/extracted/LLMZIP_IKI_FIKIR_DENEY_PAKETI_2026-09-16/LLMZIP_IKI_FIKIR_2026-09-16/results"
d = disk(IK / "SUMMARY.json"); s = f"file:{IK / 'SUMMARY.json'}"
for r in d["quality_levels_percent"]:
    if r["arm"] in ("base192", "shared_seed2026091601"):
        add(f"hashed.{r['dataset']}.{r['arm']}.fr3", r["fr3"], "pp", s, "quality_levels_percent", "idea 2: shared hashed encoder")
        add(f"hashed.{r['dataset']}.{r['arm']}.hit10", r["hit10"], "pp", s, "quality_levels_percent", "idea 2")

# ------------------------------------------------------------------ channel ablation
a = "7df5ff8a-1601-4c3d-8a22-3e0a3ea5740b"; d = art(a)["summary"]; s = f"artifact:{a}"
for b, arms in d.items():
    for arm, v in arms.items():
        for k in ("fr3", "hit", "mb", "n", "arch", "d", "lo", "hi", "sig"):
            if k in v:
                add(f"chan.{b}.{arm}.{k}", v[k], "", s, f"summary.{b}.{arm}.{k}", "channel ablation, k=96 sign codes")

# ------------------------------------------------------------------ vocabulary compaction
for b in ("locomo", "perltqa", "lme"):
    p = RE / "runs" / "vocab" / f"VOCAB_COMPACTION_{b}_2026-09-21.json"; d = disk(p); s = f"file:{p}"
    ag = d["aggregate"]
    st = sum(ag[k]["stock_bytes"] for k in ag); cp = sum(ag[k]["compact_bytes"] for k in ag)
    add(f"vocab.{b}.archives", len(d["per_archive"]), "count", s, "per_archive", "archives")
    add(f"vocab.{b}.stock", st, "bytes", s, "aggregate.*.stock_bytes", "stock vocab bytes")
    add(f"vocab.{b}.compact", cp, "bytes", s, "aggregate.*.compact_bytes", "compact vocab bytes")
    add(f"vocab.{b}.saving_pct", round(100 * (1 - cp / st), 4), "%", s, "derived", "saving")
    add(f"vocab.{b}.vectors", sum(ag[k]["queries_compared"] for k in ag), "count", s, "aggregate.*.queries_compared", "query vectors compared")
    add(f"vocab.{b}.mismatch", sum(ag[k]["bit_mismatches"] for k in ag), "count", s, "aggregate.*.bit_mismatches", "differing vectors")
    add(f"vocab.{b}.latency", d["gate"]["latency_ratio"], "ratio", s, "gate.latency_ratio", "compact/stock transform time")
    add(f"vocab.{b}.gate", str(d["gate"]["adopt"]), "bool", s, "gate.adopt", "gate outcome")

# ------------------------------------------------------------------ reach work + policy shaped
a = "50cac9a7-c6ea-469a-a9a0-7f1c99691821"; d = art(a); s = f"artifact:{a}"
add("reach.no_index", d["no_index_ET"], "docs", s, "no_index_ET", "E[T] with no index")
add("reach.floor", d["bound_96bit_ET"], "docs", s, "bound_96bit_ET", "floor for 96 routing bits")
for arm, v in d["arms"].items():
    for k in ("E_T", "median", "p90", "max", "n"):
        add(f"reach.{arm}.{k}", v[k], "docs", s, f"arms.{arm}.{k}", "E[T] reach work, LoCoMo")
pq = d["per_query"]
sg = np.array([q["sign96"] for q in pq], float); bm = np.array([q["bm25"] for q in pq], float); fl = np.array([q["float96"] for q in pq], float)
add("reach.oracle_min", float(np.minimum(sg, bm).mean()), "docs", s, "derived per_query", "per-query oracle min(sign96,bm25)")
add("reach.oracle_min_float", float(np.minimum(fl, bm).mean()), "docs", s, "derived per_query", "oracle min(float96,bm25)")
add("reach.code_better_pct", float(100 * (sg < bm).mean()), "%", s, "derived", "queries where code opens fewer docs")
add("reach.tie_pct", float(100 * (sg == bm).mean()), "%", s, "derived", "ties")
add("reach.interleave", float((2 * np.minimum(sg, bm) - 1).mean()), "docs", s, "derived", "naive interleave upper bound")
a = "56cf47df-fe7d-49c8-8ff4-fcf5eb4554dc"; d = art(a); s = f"artifact:{a}"
for k in ("static", "adaptive", "delta", "lo", "hi"):
    add(f"policy.code.{k}", d["code"][k], "docs", s, f"code.{k}", "policy-shaped arm")
    add(f"policy.bm25.{k}", d["bm25_control"][k], "docs", s, f"bm25_control.{k}", "same penalty on BM25 (control)")
for arm in ("code", "bm25"):
    for lam, v in d["grid_mean_T"][arm].items():
        add(f"policy.grid.{arm}.{lam}", v, "docs", s, f"grid_mean_T.{arm}.{lam}", "mean T by lambda")
add("policy.lambda_loo", json.dumps(sorted(set(d["lambda_loo"]["code"].values()))), "list", s, "lambda_loo.code", "lambda chosen by LOO")

# ------------------------------------------------------------------ fusion + compact BM25
a = "bbeda58c-84b3-47df-8cc6-4103e0afc47a"; FZ = art(a); s = f"artifact:{a}"
for b, r in FZ["results"].items():
    for k in ("E_T", "FR3", "Hit10"):
        add(f"fusion.{b}.bm25.{k}", r["bm25"][k], "", s, f"results.{b}.bm25.{k}", "BM25 reference")
    for kind in ("code", "W", "G"):
        for k in ("E_T", "FR3", "Hit10"):
            add(f"fusion.{b}.{kind}.{k}", r[kind][k], "", s, f"results.{b}.{kind}.{k}", "fusion arm level")
        for k in ("dE_T", "dFR3", "dHit10"):
            for j, nm in enumerate(("", ".lo", ".hi")):
                add(f"fusion.{b}.{kind}.{k}{nm}", r[kind][k][j], "", s, f"results.{b}.{kind}.{k}[{j}]", "97.5% Bonferroni interval")
    add(f"fusion.{b}.W.w_loo", json.dumps(r["W"]["w_loo"]), "list", s, f"results.{b}.W.w_loo", "weights chosen by LOO")
    add(f"fusion.{b}.G.fallback", r["G"]["tau_loo_none_share"], "share", s, f"results.{b}.G.tau_loo_none_share", "archives falling back to BM25")
for b, g in FZ["gate"].items():
    add(f"fusion.gate.{b}", str(g["adopt"]), "bool", s, f"gate.{b}.adopt", "gate outcome")
for b, m in FZ["bm25_storage"].items():
    for k in ("stock_bm25_bytes", "compact_bm25_bytes", "packed_code_bytes", "score_bit_mismatches", "queries_compared", "n_archives"):
        add(f"cbm25.{b}.{k}", m[k], "", s, f"bm25_storage.{b}.{k}", "CompactBM25 storage")
    add(f"cbm25.{b}.saving_pct", round(100 * (1 - m["compact_bm25_bytes"] / m["stock_bm25_bytes"]), 4), "%", s, "derived", "saving")
    add(f"cbm25.{b}.latency", m["compact_seconds"] / m["stock_seconds"], "ratio", s, "derived", "compact/stock scoring time")
enc = {"LoCoMo": "locomo", "PerLTQA": "perltqa", "LongMemEval": "lme"}
for b, k in enc.items():
    est = next(r["value"] for r in ROWS if r["claim_id"] == f"vocab.{k}.stock")
    ecp = next(r["value"] for r in ROWS if r["claim_id"] == f"vocab.{k}.compact")
    m = FZ["bm25_storage"][b]
    add(f"ratio.{b}.stock", est / m["stock_bm25_bytes"], "x", "derived", "vocab stock / cbm25 stock", "encoder/BM25 both stock")
    add(f"ratio.{b}.compact", ecp / m["compact_bm25_bytes"], "x", "derived", "vocab compact / cbm25 compact", "encoder/BM25 both compacted")
    add(f"ratio.{b}.fused", (m["compact_bm25_bytes"] + ecp + m["packed_code_bytes"]) / m["compact_bm25_bytes"], "x", "derived", "(cbm25+enc+codes)/cbm25", "fusion serving cost")
    add(f"ratio.{b}.codes_pct", 100 * m["packed_code_bytes"] / m["compact_bm25_bytes"], "%", "derived", "codes/cbm25", "codes as share of compact BM25")

rng = np.random.default_rng(20260923)
for b, arch in FZ["per_query"].items():
    tags = sorted(arch); rows_ = [(a_, r) for a_ in tags for r in arch[a_]]
    cl = np.array([a_ for a_, _ in rows_]); idx = {a_: np.flatnonzero(cl == a_) for a_ in tags}; U = np.array(tags)
    ref = np.array([r["bm25"] for _, r in rows_], float); x = np.array([r["rrf"]["0.1"] for _, r in rows_], float)
    add(f"posthoc.{b}.E_T", float(x[:, 0].mean()), "docs", s, "per_query rrf[0.1]", "w=0.1 level")
    for k, name, sc in ((0, "dE_T", 1), (1, "dFR3", 100)):
        dd = sc * (x[:, k] - ref[:, k]); dr = np.empty(20000)
        for i in range(20000):
            p_ = rng.integers(0, len(U), len(U)); dr[i] = dd[np.concatenate([idx[U[j]] for j in p_])].mean()
        lo, hi = np.percentile(dr, [1.25, 98.75])
        add(f"posthoc.{b}.{name}", float(dd.mean()), "", s, "recomputed", "post-hoc w=0.1 vs BM25")
        add(f"posthoc.{b}.{name}.lo", float(lo), "", s, "recomputed", "97.5% lower")
        add(f"posthoc.{b}.{name}.hi", float(hi), "", s, "recomputed", "97.5% upper")

# ------------------------------------------------------------------ all-evidence
a = "9589b5d6-61ea-4899-8c09-d465348f30ec"; AE = art(a); s = f"artifact:{a}"
for b, v in AE["summary"].items():
    add(f"allev.{b}.n", v["n_queries"], "count", s, f"summary.{b}.n_queries", "queries")
    add(f"allev.{b}.multi", v["arms"]["bm25"]["n_multi_evidence"], "count", s, f"summary.{b}.arms.bm25.n_multi_evidence", "multi-evidence queries")
    for arm, m in v["arms"].items():
        for k in ("T_first", "T_all", "any@3", "all@3", "all@5", "frac@5"):
            add(f"allev.{b}.{arm}.{k}", m[k], "", s, f"summary.{b}.arms.{arm}.{k}", "all-evidence metric")
rng = np.random.default_rng(20260923)
G = AE["gold_ranks"]
for b, arch in G.items():
    tags = sorted(arch); Wg = list(arch[tags[0]][0]["rrf"])
    w_of = {}
    for h in tags:
        tr = [r for a_ in tags if a_ != h for r in arch[a_]]
        mw = {w: np.mean([r["rrf"][w][0] for r in tr]) for w in Wg}; w_of[h] = min(mw, key=mw.get)
    rows_ = [(a_, r) for a_ in tags for r in arch[a_]]; cl = np.array([a_ for a_, _ in rows_])
    idx = {a_: np.flatnonzero(cl == a_) for a_ in tags}; U = np.array(tags)
    arr = lambda get, f: np.array([f(get(a_, r)) for a_, r in rows_], float)
    for name, get in (("W_loo", lambda a_, r: r["rrf"][w_of[a_]]), ("w0.1", lambda a_, r: r["rrf"]["0.1"])):
        for mname, f, sc in (("all@5", lambda x: 1.0 if x[-1] <= 5 else 0.0, 100), ("T_all", lambda x: x[-1], 1),
                             ("frac@5", lambda x: sum(1 for v_ in x if v_ <= 5) / len(x), 100)):
            dd = sc * (arr(get, f) - arr(lambda a_, r: r["bm25"], f)); dr = np.empty(10000)
            for i in range(10000):
                p_ = rng.integers(0, len(U), len(U)); dr[i] = dd[np.concatenate([idx[U[j]] for j in p_])].mean()
            lo, hi = np.percentile(dr, [2.5, 97.5])
            add(f"allev.{b}.{name}.d{mname}", float(dd.mean()), "", s, "recomputed", "difference vs BM25")
            add(f"allev.{b}.{name}.d{mname}.lo", float(lo), "", s, "recomputed", "95% lower")
            add(f"allev.{b}.{name}.d{mname}.hi", float(hi), "", s, "recomputed", "95% upper")

# ------------------------------------------------------------------ Codex strand
a = "ea16b81c-3983-4a08-acbf-aec6ca098dd5"; d = art(a); s = f"artifact:{a}"
for k, v in d["manifests"].items():
    add(f"codex.manifest.{k}", v, "count", s, f"manifests.{k}", "Codex round 1 manifest check")
for k in ("scripts", "exit_zero", "stdout_byte_identical", "timing_or_provenance_only", "content_differences",
          "regenerated_files_differing", "regenerated_files_differing_after_stripping_timing"):
    add(f"codex.rep.{k}", d["replication"][k], "count", s, f"replication.{k}", "Codex round 1 replication")
for n_, v in d["replication"]["time_limited_rows"].items():
    for k, vv in v.items():
        add(f"codex.timelimited.{n_}.{k}", vv, "", s, f"replication.time_limited_rows.{n_}.{k}", "time-limited hard master rows")
for fam, v in d["gap_families_percent"].items():
    if fam != "N":
        for n_, vv in zip(d["gap_families_percent"]["N"], v):
            add(f"codex.gap.{fam}.N{n_}", vv, "%", s, f"gap_families_percent.{fam}", "gap to optimum")
a = "da03d2e8-5e7f-46b6-923f-23fc4e1efbed"; d = art(a); s = f"artifact:{a}"
for r in d["results"]:
    for k in ("worlds", "wrong_answers", "expected_cost", "exact_match", "worst_case_cost", "action_nodes", "total_nodes", "program_bytes"):
        add(f"ctrl.N{r['N']}.{k}", r[k] if not isinstance(r[k], bool) else str(r[k]), "", s, f"results[N={r['N']}].{k}", "compiled controller, independent audit")
for n_ in (4, 8, 12):
    p = CX / f"leakage_cold_start_N{n_}.json"; d = disk(p); s = f"file:{p}"
    for k in ("LB", "UB", "relaxed_pair_states", "original_active_states", "conditional_zero_mean_checks", "total_seconds_including_preparation_and_audits"):
        add(f"codex.cold.N{n_}.{k}", d[k], "", s, k, "Codex cold-start certificate")
p = CX / "nonanticipativity_results.json"; d = disk(p); s = f"file:{p}"
for m in d["models"]:
    for k in ("penalty_pair_states", "martingale_checks", "negative_potential_action_residuals", "certified_gap"):
        add(f"codex.cert.N{m['N']}.{k}", m[k], "", s, f"models[N={m['N']}].{k}", "Codex LB=UB certificate")
p = CX / "structural_compression_results.json"; d = disk(p); s = f"file:{p}"
for block, label in (("original_table_diagrams", "table"), ("quotient_diagrams", "quotient")):
    for e in d[block]:
        if e.get("N") != 12:
            continue
        best = {}
        for pr in e["profiles"]:
            k = (pr["target"], pr["mode"])
            if k not in best or pr["total_nodes"] < best[k]["total_nodes"]:
                best[k] = pr
        for (tg, md), pr in best.items():
            add(f"codex.dd.{label}.{tg}.{md}.nodes", pr["total_nodes"], "nodes", s, f"{block}[N=12] min over orders", "decision-diagram size")
            add(f"codex.dd.{label}.{tg}.{md}.bytes", pr["serialized_bytes"], "bytes", s, f"{block}[N=12] min over orders", "decision-diagram bytes")
        if "value_terminal_lower_bound" in e:
            add(f"codex.dd.{label}.value_terminal_lb", e["value_terminal_lower_bound"], "count", s, f"{block}[N=12].value_terminal_lower_bound", "distinct exact values")
for q in d["quotients"]:
    add(f"codex.quot.N{q['N']}.states", q["new_active_planning_states"], "count", s, "quotients.new_active_planning_states", "symmetry quotient states")
    add(f"codex.quot.N{q['N']}.old", q["old_active_states_checked"], "count", s, "quotients.old_active_states_checked", "old active states")

# ------------------------------------------------------------------ parallel line
def mcnemar(b_, c_):
    from math import comb
    n = b_ + c_; k = min(b_, c_)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
val = lambda v: bool(v) if not isinstance(v, dict) else bool(v.get("correct"))
def pair(A, B):
    ks = sorted(set(A) & set(B)); x = [val(A[k]) for k in ks]; y = [val(B[k]) for k in ks]
    imp = sum(1 for p_, q_ in zip(x, y) if not p_ and q_); wor = sum(1 for p_, q_ in zip(x, y) if p_ and not q_)
    return len(ks), sum(x), sum(y), imp, wor, mcnemar(imp, wor)
p = RT / "a1_qa" / "or_run2" / "verdicts.json"; d = disk(p); s = f"file:{p}"
n_, x, y, imp, wor, pv = pair(d["B1c"], d["ORACLE"])
for k, v in (("n", n_), ("B1c", x), ("ORACLE", y), ("improved", imp), ("worsened", wor), ("p", pv)):
    add(f"par.qa2.{k}", v, "", s, "recomputed from verdicts", "QA run 2 (gpt-5-mini reader)")
p = RT / "a1_qa" / "or_run" / "verdicts.json"; d = disk(p)["arms"]; s = f"file:{p}"
n_, x, y, imp, wor, pv = pair(d["B0"], d["B1c"])
for k, v in (("B0", x), ("B1c", y), ("ORACLE", sum(val(v_) for v_ in d["ORACLE"].values())), ("p", pv)):
    add(f"par.qa1.{k}", v, "", s, "recomputed from verdicts", "QA run 1 (weak reader)")
txt = disk(RT / "a1_qa" / "RESULTS_A1_OR2.md"); s = f"file:{RT / 'a1_qa' / 'RESULTS_A1_OR2.md'}"
m = re.search(r"all gold in top-5 → (\d+)/(\d+) correct \((\d+)%\); gold missing → (\d+)/(\d+) \((\d+)%\)", txt)
add("par.qa2.allgold_correct", f"{m.group(1)}/{m.group(2)}", "frac", s, "text", "reader correct when all gold in top-5")
add("par.qa2.allgold_pct", int(m.group(3)), "%", s, "text", "")
add("par.qa2.missing_correct", f"{m.group(4)}/{m.group(5)}", "frac", s, "text", "reader correct when gold missing")
add("par.qa2.missing_pct", int(m.group(6)), "%", s, "text", "")
p = RT / "headroom" / "stem_development.json"; d = disk(p)["summary"]["all_dev"]; s = f"file:{p}"
add("par.stem.all5", f"{d['all5'][0]}->{d['all5'][1]}", "of 230", s, "summary.all_dev.all5", "stemming all-gold@5")
add("par.stem.p", d["all5_exact_mcnemar_p"], "p", s, "summary.all_dev.all5_exact_mcnemar_p", "")
txt = disk(RT / "headroom" / "RESULTS_STEMCACHE.md"); s = f"file:{RT / 'headroom' / 'RESULTS_STEMCACHE.md'}"
add("par.stemcache.speedup", float(re.search(r"Stemming speed-up ([\d.]+)×", txt).group(1)), "x", s, "text", "cached stemming speed-up")
txt = disk(RT / "headroom" / "AUDIT24_REPORT.md"); s = f"file:{RT / 'headroom' / 'AUDIT24_REPORT.md'}"
add("par.audit.instance_vocab", int(re.search(r"INSTANCE_VOCAB (\d+)", txt).group(1)), "of 27", s, "text", "primary cause among missed pairs")
add("par.audit.no_flag_pct", float(re.search(r"23 of 425 gold sessions \(([\d.]+)%\)", txt).group(1)), "%", s, "text", "gold sessions lacking has_answer")
p = RT / "qexp" / "qexp_qa.json"; d = disk(p)["summary"]; s = f"file:{p}"
add("par.qexp_dev.qa", f"{d['B1c_correct']}->{d['E_correct']}", "of 250", s, "summary", "query expansion QA, dev")
add("par.qexp_dev.p", d["mcnemar_p"], "p", s, "summary.mcnemar_p", "")
p = RT / "qexp" / "qexp_retrieval.json"; d = disk(p)["summary"]; s = f"file:{p}"
add("par.qexp_dev.all5_p", d["all5_mcnemar_p"], "p", s, "summary.all5_mcnemar_p", "query expansion retrieval, dev")
p = RT / "qexp_holdout" / "result.json"; d = disk(p)["summary"]; s = f"file:{p}"
add("par.qexp_ho.qa", f"{d['QA_correct']['B1c']}->{d['QA_correct']['E']}", "of 250", s, "summary.QA_correct", "query expansion QA, held-out")
add("par.qexp_ho.iw", f"{d['QA_improved_worsened'][0]}/{d['QA_improved_worsened'][1]}", "", s, "summary.QA_improved_worsened", "")
add("par.qexp_ho.p", d["QA_mcnemar_p"], "p", s, "summary.QA_mcnemar_p", "")
add("par.qexp_ho.all5", f"{d['retrieval_[B1c,E]']['all5'][0]}->{d['retrieval_[B1c,E]']['all5'][1]}", "of 240", s, "summary.retrieval", "")
add("par.qexp_ho.all5_p", d["retrieval_all5_p"], "p", s, "summary.retrieval_all5_p", "")
add("par.qexp_ho.usd", d["usd"], "USD", s, "summary.usd", "cost")
p = RT / "headroom" / "SPLIT_V1.json"; d = disk(p); s = f"file:{p}"
for k in ("discovery", "development", "final_locked"):
    add(f"par.split.{k}", len(d[k]), "count", s, k, "LongMemEval-S split size")
mine = set(FZ["per_query"]["LongMemEval"].keys())
for k in ("discovery", "development", "final_locked"):
    add(f"par.split.overlap.{k}", len(mine & set(d[k])), "count", s, "derived", "overlap with this pilot's 470")


# ------------------------------------------------------------------ RealTalk ladder, all 17 arms (incl. never-reported NOPROJ)
a = "22592fd4-2b70-4d2b-9ce4-3a60ee7ad19d"; LD = art(a); s = f"artifact:{a}"
recs_ = LD["records"]
arms_ = sorted({r["arm"] for r in recs_})
for arm in arms_:
    rr = [r for r in recs_ if r["arm"] == arm]
    h = np.concatenate([r["hit"] for r in rr]); f = np.concatenate([r["fr3"] for r in rr])
    add(f"ladder.{arm}.hit10", float(100 * h.mean()), "pp", s, f"records[arm={arm}].hit", "RealTalk ladder level")
    add(f"ladder.{arm}.fr3", float(100 * f.mean()), "pp", s, f"records[arm={arm}].fr3", "RealTalk ladder level")
rng = np.random.default_rng(20260924)
def _perarch(arm):
    return {r["arch"]: (np.asarray(r["hit"], float), np.asarray(r["fr3"], float)) for r in recs_ if r["arm"] == arm}
for cand, ref in (("NOPROJ_FULL/qscale", "BM25_frozen/-"), ("NOPROJ_FULL/qscale", "BM25_coarse/-"),
                  ("NOPROJ_WORD/float", "NOPROJ_FULL/float")):
    A_, B_ = _perarch(cand), _perarch(ref); tags = sorted(A_)
    for j, m in ((0, "hit10"), (1, "fr3")):
        dd = {t: 100 * (A_[t][j] - B_[t][j]) for t in tags}
        allv = np.concatenate([dd[t] for t in tags]); dr = np.empty(20000)
        for i in range(20000):
            pick = rng.integers(0, len(tags), len(tags)); dr[i] = np.concatenate([dd[tags[p_]] for p_ in pick]).mean()
        lo, hi = np.percentile(dr, [2.5, 97.5])
        k = f"ladder.diff.{cand}-vs-{ref}.{m}"
        add(k, float(allv.mean()), "pp", s, "recomputed, paired archive-clustered, 20000, seed 20260924", "descriptive, not gated")
        add(k + ".lo", float(lo), "pp", s, "recomputed", "95% lower"); add(k + ".hi", float(hi), "pp", s, "recomputed", "95% upper")

# ------------------------------------------------------------------ gate registry + correction log
def declared(cid, value, unit, path, pattern, meaning):
    """A declared threshold: the literal must appear in the document that declared the gate."""
    t = disk(path)
    assert re.search(pattern, t), (cid, path, pattern)
    add(cid, value, unit, f"file:{Path(path)}", f"declared text /{pattern}/", meaning)

SNAP = Path(os.environ.get("LLMZIP_REPO", "llmzip")) / "research_top10_comparison_2026_09_16"
declared("gate.c1.min_pp", 2.0, "pp", RE / "C1_FIRST_REAL_EVALUATION_2026-09-20.md", r"Δ FR@3 ≥ 2\.0 pp", "C1 declared minimum effect")
declared("gate.c1.ci", 95, "%", RE / "C1_FIRST_REAL_EVALUATION_2026-09-20.md", r"95 % CI excludes 0", "C1 interval level")
declared("gate.c3.min_pp", 1.0, "pp", SNAP / "coordinator" / "decision_tests.py", r">= \+1\.0 pp FR@3, CI excluding 0", "C3 declared minimum effect")
declared("gate.vocab.latency_max", 1.25, "x", RE / "VOCAB_COMPACTION_2026-09-21.md", r"at most 1\.25×", "vocab compaction latency ceiling")
declared("gate.fusion.min_cut_pct", 5, "%", RE / "SELECTIVE_FUSION_2026-09-23.md", r"en az %5 düşüş", "fusion primary minimum E[T] cut, LoCoMo")
declared("gate.fusion.ci", 97.5, "%", RE / "SELECTIVE_FUSION_2026-09-23.md", r"%97,5", "fusion interval level (Bonferroni, two arms)")
declared("gate.fusion.margin_pp", -1.0, "pp", RE / "SELECTIVE_FUSION_2026-09-23.md", r"−1,0 pp", "fusion FR@3 non-inferiority margin")
declared("gate.fusion.reps", 20000, "reps", RE / "SELECTIVE_FUSION_2026-09-23.md", r"20\.000 tekrar", "fusion bootstrap replicates")

_rr = {r["claim_id"]: float(r["value"]) for r in ROWS if r["claim_id"].startswith("rerank.") and r["claim_id"].endswith(".fr3")}
for b in ("LME", "PerLTQA", "LoCoMo"):
    add(f"gate.c3.{b}.delta", 100 * (_rr[f"rerank.{b}.qscale96_bm25.fr3"] - _rr[f"rerank.{b}.BM25_full.fr3"]), "pp", "derived",
        "rerank qscale96->BM25 minus BM25_full, FR@3", "C3 point estimate")

_p = Path(os.environ.get("LLMZIP_REPO", "llmzip")) / "research_twelve_byte_pilot_2026_09_15" / "results" / "BM25.json"
_b = disk(_p)["benchmarks"]["locomo"]
for m in ("fr3", "hit10"):
    c_ = _b["contrasts"][f"{m}:bm25_rrf_sym-bm25"]
    add(f"rrf16.locomo.{m}", c_["delta_pp"], "pp", f"file:{_p}", f"benchmarks.locomo.contrasts.{m}:bm25_rrf_sym-bm25", "unweighted RRF vs BM25, 2026-09-16")
    add(f"rrf16.locomo.{m}.lo", c_["ci95"][0], "pp", f"file:{_p}", "ci95[0]", "95% lower")
    add(f"rrf16.locomo.{m}.hi", c_["ci95"][1], "pp", f"file:{_p}", "ci95[1]", "95% upper")
for arm in ("bm25", "bm25_rrf_sym"):
    add(f"rrf16.locomo.level.{arm}.fr3", _b["levels"]["fr3"][arm], "%", f"file:{_p}", f"levels.fr3.{arm}", "2026-09-16 pilot configuration")

_g = {r["claim_id"]: float(r["value"]) for r in ROWS if r["claim_id"] in ("policy.code.static", "policy.code.adaptive", "policy.bm25.static", "reach.floor")}
_gap = _g["policy.code.static"] - _g["policy.bm25.static"]
add("policy.gap_to_bm25", _gap, "docs", "derived", "policy.code.static - policy.bm25.static", "E[T] gap, code vs BM25")
add("policy.gap_to_floor", _g["policy.code.static"] - _g["reach.floor"], "docs", "derived", "policy.code.static - reach.floor", "E[T] gap, code vs 96-bit floor")
add("policy.closed_bm25_pct", 100 * (_g["policy.code.static"] - _g["policy.code.adaptive"]) / _gap, "%", "derived", "", "share of gap to BM25 closed")
add("policy.closed_floor_pct", 100 * (_g["policy.code.static"] - _g["policy.code.adaptive"]) / (_g["policy.code.static"] - _g["reach.floor"]), "%", "derived", "", "share of gap to floor closed")

_sp = SNAP / "SUPERSESSION_LEDGER_2026-09-17.json"
_sl = disk(_sp)
add("sup.entries", len(_sl["claims"]), "count", f"file:{_sp}", "len(claims)", "programme supersession entries")
for st, n_ in sorted(collections.Counter(c["current_status"] for c in _sl["claims"]).items()):
    add(f"sup.status.{st}", n_, "count", f"file:{_sp}", "claims[].current_status", "entries with this status")
for c in _sl["claims"]:
    add(f"sup.id.{c['claim_id']}", c["current_status"], "status", f"file:{_sp}", "claims[].current_status", c["historical_text_or_heading"][:120])
_s10 = [c for c in _sl["claims"] if c["claim_id"] == "SIGN-BEATS-FLOAT-10PP"][0]["evidence"]
_m = re.search(r"float_std - sym = \+([\d.]+) \[(-[\d.]+), \+([\d.]+)\]", _s10); assert _m
add("sup.sign10.std_minus_sym", float(_m.group(1)), "pp", f"file:{_sp}", "SIGN-BEATS-FLOAT-10PP.evidence", "standardized float minus sign, FR@3, RealTalk")
add("sup.sign10.lo", float(_m.group(2)), "pp", f"file:{_sp}", "SIGN-BEATS-FLOAT-10PP.evidence", "95% lower")
add("sup.sign10.hi", float(_m.group(3)), "pp", f"file:{_sp}", "SIGN-BEATS-FLOAT-10PP.evidence", "95% upper")
_rp = RE / "README_PROPOSED_2026-09-20.md"
_t = disk(_rp); _m = re.search(r"\+(10\.037943) pp", _t); assert _m
add("sup.sign10.headline", float(_m.group(1)), "pp", f"file:{_rp}", "retracted public headline", "SIGN96 above uncentered FLOAT96")

_tp = RE / "T1_RUN_MATRIX.json"
_t1 = disk(_tp); _s = json.dumps(_t1, ensure_ascii=False)
assert "withdrawn REFUTED verdict" in _s and "~12.5% event" in _s
_m = re.search(r'"kind": "in-process forced permutations \(order-seeds 0-5\)", "n": (\d+)', _s); assert _m
_n6 = int(_m.group(1))
add("corr.t1.permutations", _n6, "count", f"file:{_tp}", "forced permutations n", "permutations behind the withdrawn REFUTED verdict")
add("corr.t1.event_rate_pct", 12.5, "%", f"file:{_tp}", "why_v1_got_it_wrong (~12.5% event)", "per-seed event rate")
add("corr.t1.p_miss", (1 - 0.125) ** _n6, "p", "derived", "(1-0.125)^n", "chance all draws miss the event")
_fp = RE / "runs" / "fusion" / "SELECTIVE_FUSION_2026-09-23.json"
_fj = disk(_fp)
add("corr.bm25est.measured_bytes", _fj["bm25_storage_per_archive"]["LoCoMo"][0]["compact_bm25_bytes"], "bytes", f"file:{_fp}",
    "bm25_storage_per_archive.LoCoMo[0].compact_bm25_bytes", "measured compact BM25, locomo_0")
_mdp = RE / "SELECTIVE_FUSION_2026-09-23.md"
_md = disk(_mdp)
_m = re.search(r"tahmin ettiğim (\d+) kB.*?oran (\d+),(\d+)× değil \*\*(\d+),(\d+)×", _md, re.S); assert _m
add("corr.bm25est.estimate_kB", float(_m.group(1)), "kB", f"file:{_mdp}", "text", "earlier estimate")
add("corr.bm25est.ratio_est", float(f"{_m.group(2)}.{_m.group(3)}"), "x", f"file:{_mdp}", "text", "encoder/BM25 ratio implied by the estimate")
add("corr.bm25est.ratio_meas", float(f"{_m.group(4)}.{_m.group(5)}"), "x", f"file:{_mdp}", "text", "measured ratio, locomo_0")

# ------------------------------------------------------------------ Codex round 2 manifest (re-verified here)
_mp = CX / "structural_compression_manifest.json"
_mj = disk(_mp)["files"]
_ok = sum(1 for n_, e_ in _mj.items() if (CX / n_).exists() and hashlib.sha256((CX / n_).read_bytes()).hexdigest() == e_["sha256"])
add("codex2.manifest.files", len(_mj), "count", f"file:{_mp}", "len(files)", "round-2 manifest entries")
add("codex2.manifest.verified", _ok, "count", "recomputed", "sha256 match on disk", "round-2 files verified")
_cm = disk(Path(artifact_path("a1c81008-b32d-463c-b8b3-48eff013a94a")))
SRC_SHA["artifact:a1c81008-b32d-463c-b8b3-48eff013a94a"] = SRC_SHA.pop(f"file:{Path(artifact_path('a1c81008-b32d-463c-b8b3-48eff013a94a'))}")
_m = re.search(r"\*\*(\d+)'si de hatasız\*\*", _cm); assert _m
add("codex2.commands_clean", int(_m.group(1)), "count", "artifact:a1c81008-b32d-463c-b8b3-48eff013a94a", "section 1", "round-2 commands re-run without error")

# ------------------------------------------------------------------ write
out = Path("paper") / "CLAIMS_LEDGER.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["claim_id", "value", "unit", "source", "source_sha256", "field", "meaning"])
    w.writeheader()
    for r in ROWS:
        r["source_sha256"] = SRC_SHA.get(r["source"], "")
        for k_ in ("source", "field"):
            s_ = str(r[k_])
            for root, name in ((W, "llmzip-work"), (RE.parent, "llmzip"), (CX, "codex-package")):
                s_ = s_.replace(str(root), name)
            r[k_] = s_.replace("\\", "/")
        w.writerow(r)
print(f"WROTE {out}: {len(ROWS)} claims from {len(SRC_SHA)} sources")
