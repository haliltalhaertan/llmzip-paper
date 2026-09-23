# llmzip-paper

`[LOCAL EXPLORATORY PILOT] [NOT PREREGISTERED] [NOT FOR CITATION] [DISCLOSE-BEFORE-USE]`

**Twelve Bytes Against an Inverted Index: What a Compact-Code Memory Retrieval Programme Found, and Which Configuration Choices Decided It** — [paper/llmzip_paper.pdf](paper/llmzip_paper.pdf)

The llmzip programme asked whether a 12-byte (96-bit) TF-IDF/SVD sign code per document can replace or complement a BM25 index when an agent retrieves evidence from its conversational memory (LongMemEval-S, LoCoMo, PerLTQA, RealTalk). In short:

- The compact code does **not** beat BM25 on any measured axis. The pre-specified gate failed.
- Five configuration choices each reversed a verdict with everything else held fixed: the document unit, the query cohort, the projection family, the benchmark and the metric.
- Two compactions that change no output bit reduce the encoder vocabulary by about 63% and the BM25 index by about 76%.
- One unconfirmed lead remains: weighted rank fusion of BM25 and the code with a fixed weight of 0.1, chosen after the fact.

The programme was not preregistered, its own code was not independently audited, and every on-disk benchmark has already been seen. The paper lists the programme's supersession entries and the head researcher's own errors.

## What is here

| path | content |
|---|---|
| `paper/llmzip_paper.pdf` | the paper |
| `paper/CLAIMS_LEDGER.csv` | every number in the paper: value, unit, source, field read, source SHA-256 |
| `paper/ARTEFACT_INDEX.csv` | file names and SHA-256 for the `artifact:<id>` sources in the ledger |
| `paper/fig*.py`, `figcommon.py` | figures, drawn from the ledger |
| `paper/make_tables.py` | all LaTeX tables, from the ledger |
| `paper/llmzip_paper.tmpl.tex`, `render.py` | manuscript template; every number is a ledger placeholder |
| `paper/verify_paper.py` | checks that no number is typed by hand, that citations resolve and that figure/table claims hold |
| `paper/build_ledger.py` | provenance script that built the ledger from the private run records (not runnable here) |

## Rebuild from the ledger

```
python build_all.py                      # figures, tables, llmzip_paper.tex
cd paper
pdflatex llmzip_paper && bibtex llmzip_paper && pdflatex llmzip_paper && pdflatex llmzip_paper
cd .. && python paper/verify_paper.py    # writes paper/PAPER_VERIFICATION.json
```

Requires Python 3 with NumPy and Matplotlib, plus a TeX distribution with `booktabs`, `tabularx`, `adjustbox`, `natbib` and `lmodern`.

## Data

No benchmark text is included. LongMemEval is MIT-licensed; LoCoMo and PerLTQA are CC BY-NC 4.0; RealTalk has no published licence and was used for local evaluation only. The external strands in Section 4 of the paper are summarised, not redistributed.

## Licence

Code (`*.py`) is MIT; see `LICENSE`. The paper, figures, tables and ledger are CC BY 4.0; see `LICENSE-CC-BY-4.0`.
