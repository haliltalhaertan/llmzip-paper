"""Render llmzip_paper.tmpl.tex -> llmzip_paper.tex, filling every number from CLAIMS_LEDGER.csv.

Placeholders
  «key|d|flags»      value of `key` with d decimals (default 2)
  «ci:key|d|flags»   "[lo, hi]" from key.lo / key.hi
  «raw:key»          the ledger string, verbatim
  «expr:EXPR|d|flags» arithmetic over ledger values written {key}; only + - * / ( ) and numbers
flags: s signed, t thousands separator, m /1e6, k /1e3, p x100, n negate, a absolute value
"""
import csv, json, re
from pathlib import Path

HERE = Path("paper")
L = {r["claim_id"]: r["value"] for r in csv.DictReader(open(HERE / "CLAIMS_LEDGER.csv", encoding="utf-8"))}
USED = {}


def num(x, d=2, signed=False, thousands=False):
    spec = ("+" if signed else "") + ("," if thousands else "") + f".{d}f"
    return format(x, spec).replace("-", "\\textminus{}").replace(",", "{,}")


def val(key, flags):
    x = float(L[key])
    if "m" in flags: x /= 1e6
    if "k" in flags: x /= 1e3
    if "p" in flags: x *= 100
    if "n" in flags: x = -x
    if "a" in flags: x = abs(x)
    return x


def expr(e):
    keys = re.findall(r"\{([^}]+)\}", e)
    py = re.sub(r"\{([^}]+)\}", lambda m_: repr(float(L[m_.group(1)])), e)
    assert re.fullmatch(r"[0-9eE+\-*/(). ]+", py), e
    return eval(py), keys


META = {"ledger_count": f"{len(L):,}".replace(",", "{,}"),
        "source_count": str(len({r["source"] for r in csv.DictReader(open(HERE / "CLAIMS_LEDGER.csv", encoding="utf-8")) if r["source"] not in ("derived", "recomputed")}))}


def sub(m):
    body = m.group(1)
    if body.startswith("meta:"):
        USED[body] = META[body[5:]]
        return META[body[5:]]
    if body.startswith("expr:"):
        e, *rest = body[5:].split("|")
        d = int(rest[0]) if rest and rest[0] else 2
        flags = rest[1] if len(rest) > 1 else ""
        x, keys = expr(e)
        if "a" in flags: x = abs(x)
        USED["expr:" + e] = x
        return num(x, d, "s" in flags, "t" in flags)
    kind, _, rest = body.partition(":") if body.startswith(("ci:", "raw:")) else ("v", "", body)
    parts = rest.split("|")
    key, d, flags = parts[0], int(parts[1]) if len(parts) > 1 and parts[1] else 2, parts[2] if len(parts) > 2 else ""
    if kind == "raw":
        USED[key] = L[key]
        return L[key].replace("_", "\\_").replace("->", " to ")
    if kind == "ci":
        a, b = val(key + ".lo", flags), val(key + ".hi", flags)
        a, b = min(a, b), max(a, b)
        USED[key + ".lo"] = a; USED[key + ".hi"] = b
        return f"[{num(a, d)}, {num(b, d)}]"
    x = val(key, flags)
    USED[key] = x
    return num(x, d, "s" in flags, "t" in flags)


src = (HERE / "llmzip_paper.tmpl.tex").read_text(encoding="utf-8")
def keys_of(b):
    if b.startswith("meta:"):
        return []
    if b.startswith("expr:"):
        return re.findall(r"\{([^}]+)\}", b)
    k = b.split("|")[0].split(":", 1)[-1]
    return [k] if not b.startswith("ci:") else [k + ".lo", k + ".hi"]
missing = sorted({k for m in re.finditer(r"«([^»]+)»", src) for k in keys_of(m.group(1)) if k not in L})
assert not missing, f"missing ledger keys: {missing}"
out = re.sub(r"«([^»]+)»", sub, src)
assert "«" not in out and "»" not in out
(HERE / "llmzip_paper.tex").write_text(out, encoding="utf-8")
(HERE / "prose_used_keys.json").write_text(json.dumps(USED, indent=0), encoding="utf-8")
print(f"rendered llmzip_paper.tex: {len(USED)} ledger values placed")
