#!/usr/bin/env python3
"""
relabel_independent.py
----------------------
Cross-check for the identifier-style results: does the Kalpana gain survive when "this chunk defines X" is decided
WITHOUT Miru's tree-sitter extraction (which also produces Kalpana's role features)?

Independent labeller (universal-ctags could not be installed on this macOS):
  * Pygments lexers (token types Name.Function / Name.Class) for C, C++, C#, Scala, Haskell, PHP, Java, Ruby, Rust
  * hand-written definition regexes for Go, Elixir, JavaScript, TypeScript (Pygments does not tag definitions there)
A returned chunk counts as correct when its text lexically defines the query identifier (any file; the tree-sitter
`definedIn` list is not used). Same arms, same pools, same held-out alphas as the main tables.

    .venv/bin/python miru_kalpana/relabel_independent.py [--tag ds1-miru-int8] [--out benchmark/summary.independent.md]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

from pygments.lexers import get_lexer_for_filename
from pygments.token import Name
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_kalpana_fusion import sign_test  # noqa: E402
import summarize_results as S  # noqa: E402


def _rx(pattern: str, ident: str) -> bool:
    return re.search(pattern.replace("{I}", re.escape(ident)), "", re.M) is not None  # placeholder (never used)


_RX = {
    "go": [r"^\s*func\s+(?:\([^)]*\)\s*)?{I}\b", r"^\s*type\s+{I}\b", r"^\t{I}\s+(?:struct|interface)\b"],
    "elixir": [r"^\s*(?:defp?|defmacrop?|defguardp?|defdelegate|defmodule|defprotocol|defimpl)\s+(?:[\w.]*\.)?{I}\b"],
    "js": [r"\bfunction\s*\*?\s*{I}\b", r"\bclass\s+{I}\b", r"\binterface\s+{I}\b", r"\benum\s+{I}\b",
           r"\btype\s+{I}\s*(?:<[^>]*>)?\s*=", r"\b(?:const|let|var)\s+{I}\s*(?::[^=]+)?=\s*(?:async\s*)?(?:function\b|\()",
           r"^\s*(?:(?:public|private|protected|static|async|get|set|readonly|override|export|default)\s+)*{I}\s*(?:<[^>]*>)?\s*\([^)]*\)\s*(?::[^{;]+)?\{",
           r"\b{I}\s*:\s*(?:async\s*)?function\b"],
}
_EXT = {".go": "go", ".ex": "elixir", ".exs": "elixir", ".js": "js", ".mjs": "js", ".cjs": "js", ".jsx": "js",
        ".ts": "js", ".tsx": "js", ".mts": "js", ".cts": "js"}


def defines_independent(content: str, ident: str, path: str) -> bool:
    ext = Path(path).suffix.lower()
    if ext in _EXT:
        return any(re.search(p.replace("{I}", re.escape(ident)), content, re.M) for p in _RX[_EXT[ext]])
    try:
        lexer = get_lexer_for_filename(path)
    except ClassNotFound:
        return False
    if ext == ".php" and "<?php" not in content:  # mid-file chunks are lexed as inline HTML otherwise
        content = "<?php\n" + content
    for tok, val in lexer.get_tokens(content):
        if (tok in Name.Function or tok in Name.Class) and re.split(r"::|\.", val)[-1] == ident:
            return True
    return False


def load_pools(path: Path) -> dict:
    return {r["id"]: {f'{c["file_path"]}:{c["start_line"]}': c for c in r["candidates"]}
            for r in json.loads(path.read_text())["queries"]}


def relabel(tag: str, repo: str):
    st = f".queries.{repo}"
    rf = ROOT / "benchmark" / f"results.kalpana.{tag}{st}.k5.ts.json"
    f5 = ROOT / ".bench" / "kalpana" / f"candidates.{tag}{st}.k5.ts.json"
    f3 = ROOT / ".bench" / "kalpana" / f"candidates.{tag}{st}.k3.ts.json"
    qf = ROOT / "benchmark" / f"queries.{repo}.json"
    if not all(p.exists() for p in (rf, f5, f3, qf)):
        return None
    spec = {q["id"]: q for q in json.loads(qf.read_text())["queries"]}
    res = json.loads(rf.read_text())
    p5, p3 = load_pools(f5), load_pools(f3)
    pq = res["perQuery"]
    ids = list(range(len(pq)))
    random.Random(res["cv"]["seed"]).shuffle(ids)
    F = res["cv"]["folds"]
    alpha_of = {i: res["cv"]["alphas"][f] for f in range(F) for i in ids[f::F]}
    rows = []
    for i, r in enumerate(pq):
        q = spec[r["id"]]
        ident = q["identifier"]
        ok = lambda c: defines_independent(c["content"], ident, c["file_path"])  # noqa: E731
        native = any(ok(c) for c in list(p3[r["id"]].values())[:3])
        keys = r[f"lin{alpha_of[i]}"]["top3"]
        kal = any(ok(p5[r["id"]][k]) for k in keys if k in p5[r["id"]])
        base = any(ok(p5[r["id"]][k]) for k in r["baseline"]["top3"] if k in p5[r["id"]])
        # tree-sitter labels for the same arms (from the main tables), to measure agreement
        ts_native = any(h and ident in c.get("defs", []) for h, c in
                        zip([S.in_defined(c["file_path"], q["definedIn"]) for c in list(p3[r["id"]].values())[:3]],
                            list(p3[r["id"]].values())[:3]))
        rows.append({"native": native, "base": base, "kal": kal, "ts_native": ts_native,
                     "ts_kal": r[f"lin{alpha_of[i]}"]["def3"]})
    return rows


def wl(rows, a, b):
    w = sum(r[a] and not r[b] for r in rows)
    l = sum(r[b] and not r[a] for r in rows)
    return w, l


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="ds1-miru-int8")
    ap.add_argument("--out", default="benchmark/summary.independent.md")
    a = ap.parse_args()
    man = json.loads((ROOT / "benchmark" / "identifier_repos.json").read_text())
    live = [r for r in man["repos"] if not r.get("skip")]
    lines = ["# Independent re-labelling of the identifier-style results", "",
             "A chunk is correct if its text lexically defines the query identifier, decided by Pygments lexers "
             "(C, C++, C#, Scala, Haskell, PHP, Java, Ruby, Rust) or hand-written regexes (Go, Elixir, JavaScript, "
             "TypeScript), **not** by Miru's tree-sitter extraction. Same pools, arms and held-out alphas as the main table. "
             "Win/loss is Kalpana vs Miru native top-3.", "",
             "| Language (repo) | n | Native (tree-sitter label) | + Kalpana (tree-sitter) | Native (independent) | + Kalpana (independent) | Win / Loss (independent) | p | vs same top-5 pool W / L |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    tot = {"n": 0, "nat": 0, "kal": 0, "w": 0, "l": 0, "hw": 0, "hl": 0, "tn": 0, "tk": 0}
    for r in live:
        rows = relabel(a.tag, f"id-{r['name']}")
        name = f"{r['lang']} ({r['name']})" + (" †" if r.get("seen") else "")
        if not rows:
            lines.append(f"| {name} | not run | | | | | | | |")
            continue
        n = len(rows)
        w, l = wl(rows, "kal", "native"); hw, hl = wl(rows, "kal", "base")
        nat, kal = sum(x["native"] for x in rows), sum(x["kal"] for x in rows)
        tn, tk = sum(x["ts_native"] for x in rows), sum(x["ts_kal"] for x in rows)
        lines.append(f"| {name} | {n} | {tn/n:.1%} | {tk/n:.1%} | {nat/n:.1%} | {kal/n:.1%} | {w} / {l} | {sign_test(w, l):.3f} | {hw} / {hl} |")
        if not r.get("seen"):
            for k, v in (("n", n), ("nat", nat), ("kal", kal), ("w", w), ("l", l), ("hw", hw), ("hl", hl), ("tn", tn), ("tk", tk)):
                tot[k] += v
    n = tot["n"]
    if n:
        lines.append(f"| **Pooled held-out** | {n} | {tot['tn']/n:.1%} | {tot['tk']/n:.1%} | {tot['nat']/n:.1%} | {tot['kal']/n:.1%} | "
                     f"**{tot['w']} / {tot['l']}** | {sign_test(tot['w'], tot['l']):.3f} | {tot['hw']} / {tot['hl']} |")
    lines += ["", "† not held-out (used in development); excluded from the pooled row.", ""]
    out = ROOT / a.out
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
