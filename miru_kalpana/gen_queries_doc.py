#!/usr/bin/env python3
"""
gen_queries_doc.py
------------------
Docstring-style natural-language query set for one repo, drawn from the candidates written by
scripts/extract_docqueries.ts. Counterpart of gen_queries_multi.py (identifier-style), kept in separate files.

    npx tsx scripts/extract_docqueries.ts eval-repos/id-redis c .bench/docq/redis.json --strip eval-repos/doc-redis
    python3 miru_kalpana/gen_queries_doc.py --name redis --n 200 --seed 0xA11CE

Each query is the first sentence of the doc comment of one definition. Ground truth: the file that holds that
definition, and (for chunk-level scoring) a chunk in that file that defines the identifier. The indexed corpus
is eval-repos/doc-<name>, the pinned repo with every definition doc comment removed, so the answer is not in
the text. Writes benchmark/queries.doc-<name>.json (ids D<REPO><i>). If fewer than --n candidates exist, all are used.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ident_words(ident: str) -> set:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", ident)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return {w for w in re.split(r"[_\s]+", s.lower()) if w}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="short repo name, e.g. redis (corpus eval-repos/doc-<name>)")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0xA11CE)
    args = ap.parse_args()

    cand_path = ROOT / ".bench" / "docq" / f"{args.name}.json"
    data = json.loads(cand_path.read_text())
    pool = sorted(data["candidates"], key=lambda c: (c["file"], c["name"]))
    n = min(args.n, len(pool))
    print(f"{args.name}: usable documented definitions {len(pool)}; drawing {n}")
    picked = random.Random(args.seed).sample(pool, n)
    tag = re.sub(r"\W", "", args.name).upper()[:6]
    qs = []
    for i, c in enumerate(picked):
        qwords = {w.lower() for w in re.findall(r"[A-Za-z]+", c["query"])}
        iw = ident_words(c["name"])
        qs.append({"id": f"D{tag}{i}", "query": c["query"], "identifier": c["name"], "definedIn": [c["file"]],
                   "line": c["line"], "nameWordsInQuery": bool(iw) and iw <= qwords})
    src = Path(data["repoDir"])
    commit = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    leak = sum(q["nameWordsInQuery"] for q in qs)
    out = ROOT / "benchmark" / f"queries.doc-{args.name}.json"
    out.write_text(json.dumps({
        "repo": f"doc-{args.name}", "source": src.name, "commit": commit, "lang": data["lang"],
        "metric": "defining file / defining chunk in top 3",
        "description": f"{n} docstring-style queries (first sentence of the doc comment of one definition), drawn by "
                       f"gen_queries_doc.py (seed {hex(args.seed)}); corpus is the pinned repo with all definition doc "
                       f"comments removed (scripts/extract_docqueries.ts --strip). Documented definitions available: "
                       f"{len(pool)} (of {data['defs']} definitions).",
        "queries": qs}, indent=1))
    print(f"wrote {out.relative_to(ROOT)}; {leak}/{n} queries contain every word of the identifier")


if __name__ == "__main__":
    main()
