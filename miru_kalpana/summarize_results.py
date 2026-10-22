#!/usr/bin/env python3
"""
summarize_results.py
--------------------
Builds the per-language table Jordan asked for from the saved per-query JSON (no re-running anything):
  Miru native Chunk@3 | + Kalpana (alpha chosen by 5-fold CV, scored on held-out folds) | win/loss vs native |
  sign-test p | do-no-harm win/loss vs the same top-5 pool un-reranked | latency incl. query embedding.

    .venv/bin/python miru_kalpana/summarize_results.py [--tags ds1-miru-int8 minilm-l6-256]
                                                      [--repos csn-ruby ...] [--out benchmark/summary.md]
Chunk@3 = a defining chunk for the target identifier is in the top 3 (tree-sitter ground truth);
File@3 = the defining file is in the top 3.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_kalpana_fusion import defines, in_defined, sign_test  # noqa: E402

CSN = ["csn-ruby", "csn-php", "csn-java", "csn-go", "csn-javascript", "csn-python"]
AB = ["ab-miru-code", "ab-phoenix", "ab-axum", "ab-serde"]


def _def(c: dict, ident: str) -> bool:
    if "defs" in c and c.get("language") != "go":
        return ident in c["defs"]
    return defines(c["content"], ident)


def load(tag: str, repo: str):
    st = f".queries.{repo}"
    rf = ROOT / "benchmark" / f"results.kalpana.{tag}{st}.k5.ts.json"
    nf = ROOT / ".bench" / "kalpana" / f"candidates.{tag}{st}.k3.ts.json"
    qf = ROOT / "benchmark" / f"queries.{repo}.json"
    if not (rf.exists() and nf.exists() and qf.exists()):
        return None
    spec = {q["id"]: q for q in json.loads(qf.read_text())["queries"]}
    res = json.loads(rf.read_text())
    nat = {r["id"]: r["candidates"][:3] for r in json.loads(nf.read_text())["queries"]}
    pq = res["perQuery"]
    ids = list(range(len(pq)))
    random.Random(res["cv"]["seed"]).shuffle(ids)
    F = res["cv"]["folds"]
    alpha_of = {i: res["cv"]["alphas"][f] for f in range(F) for i in ids[f::F]}
    rows = []
    for i, r in enumerate(pq):
        q, top = spec[r["id"]], nat[r["id"]]
        fh = [in_defined(c["file_path"], q["definedIn"]) for c in top]
        nat_row = {"hit3": any(fh), "def3": any(h and _def(c, q["identifier"]) for h, c in zip(fh, top))}
        rows.append((nat_row, r["baseline"], r[f"lin{alpha_of[i]}"]))
    return {"rows": rows, "lat": res["latencyMs"], "res": res, "ids": [r["id"] for r in pq], "spec": spec}


def wl(pairs, key):
    w = sum(a[key] and not b[key] for a, b in pairs)
    l = sum(b[key] and not a[key] for a, b in pairs)
    return w, l


def row_for(d: dict, key: str = "def3") -> dict:
    rows, n = d["rows"], len(d["rows"])
    nat = [r[0] for r in rows]; base = [r[1] for r in rows]; kal = [r[2] for r in rows]
    w, l = wl(list(zip(kal, nat)), key); hw, hl = wl(list(zip(kal, base)), key)
    return {
        "n": n, "nat": sum(x[key] for x in nat) / n, "kal": sum(x[key] for x in kal) / n,
        "w": w, "l": l, "p": sign_test(w, l), "hw": hw, "hl": hl, "hp": sign_test(hw, hl),
        "ceiling": sum(r["rr_def" if key == "def3" else "rr"] > 0 for r in base) / n,
    }


def table(tag: str, repos: list, title: str, lines: list, key: str = "def3", labels: dict | None = None,
          seen: set | None = None) -> dict:
    metric = "Chunk@3" if key == "def3" else "File@3"
    labels, seen = labels or {}, seen or set()
    lines += [f"### {title}  (`{tag}`)", "",
              f"| Repo | n | Native {metric} | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p | Top-5 ceiling |",
              "|---|---|---|---|---|---|---|---|---|"]
    tot = {"n": 0, "w": 0, "l": 0, "hw": 0, "hl": 0, "nat": 0.0, "kal": 0.0}
    for repo in repos:
        d = load(tag, repo)
        name = labels.get(repo, repo) + (" †" if repo in seen else "")
        if not d:
            lines.append(f"| {name} | — | not run | | | | | | |")
            continue
        r = row_for(d, key)
        lines.append(f"| {name} | {r['n']} | {r['nat']:.1%} | {r['kal']:.1%} | {r['w']} / {r['l']} | {r['p']:.3f} "
                     f"| {r['hw']} / {r['hl']} | {r['hp']:.3f} | {r['ceiling']:.1%} |")
        if repo in seen:
            continue
        for k in ("n", "w", "l", "hw", "hl"):
            tot[k] += r[k]
        tot["nat"] += r["nat"] * r["n"]; tot["kal"] += r["kal"] * r["n"]
    if tot["n"]:
        lines.append(f"| **Pooled{' (held-out only)' if seen else ''}** | {tot['n']} | {tot['nat']/tot['n']:.1%} | {tot['kal']/tot['n']:.1%} | "
                     f"**{tot['w']} / {tot['l']}** | {sign_test(tot['w'], tot['l']):.3f} | "
                     f"{tot['hw']} / {tot['hl']} | {sign_test(tot['hw'], tot['hl']):.3f} | |")
    if seen:
        lines.append("\n† used during development, not held-out; excluded from the pooled row.")
    lines.append("")
    return tot


def strat_table(tag: str, repos: list, lines: list, labels: dict) -> None:
    """Docstring suite only: split by whether the query already contains every word of the identifier name."""
    lines += [f"### Split by name overlap, chunk level  (`{tag}`)", "",
              "Queries whose words include every word of the identifier name (e.g. 'parse request' for parseRequest) are "
              "easier by construction. The second block keeps only queries that do not.", "",
              "| Subset | n | Native Chunk@3 | + Kalpana | Win / Loss | p |", "|---|---|---|---|---|---|"]
    for title, want in (("query contains every word of the identifier", True),
                        ("query does not (pure natural language)", False)):
        sel = []
        for repo in repos:
            d = load(tag, repo)
            if not d:
                continue
            sel += [row for row, i in zip(d["rows"], d["ids"]) if bool(d["spec"][i].get("nameWordsInQuery")) == want]
        n = len(sel)
        if not n:
            continue
        nat = [r[0] for r in sel]; kal = [r[2] for r in sel]
        w, l = wl(list(zip(kal, nat)), "def3")
        lines.append(f"| {title} | {n} | {sum(x['def3'] for x in nat)/n:.1%} | {sum(x['def3'] for x in kal)/n:.1%} "
                     f"| {w} / {l} | {sign_test(w, l):.3f} |")
    lines.append("")


def latency(tag: str, repos: list, lines: list) -> None:
    lines += [f"### Latency per query, ms (p50 / p95)  (`{tag}`)", "",
              "| Repo | Miru query embedding (API) | Miru search | Kalpana query, cold | Kalpana query, warm | Kalpana pool scoring |",
              "|---|---|---|---|---|---|"]
    f = lambda x: f"{x['p50']:.1f} / {x['p95']:.1f}" if x else "—"
    for repo in repos:
        d = load(tag, repo)
        if not d:
            continue
        L = d["lat"]
        lines.append(f"| {repo} | {f(L.get('miruQueryEmbedding'))} | {f(L['miru'])} | {f(L['queryTensorCold'])} "
                     f"| {f(L['queryTensorWarm'])} | {f(L['poolScoring'])} |")
    lines.append("")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["std", "id", "doc"], default="std",
                    help="std = CodeSearchNet + curated A/B; id = identifier-style set (benchmark/identifier_repos.json); "
                         "doc = docstring-style queries on the same repos (scripts/run_doc_suite.sh)")
    ap.add_argument("--tags", nargs="+", default=None)
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.suite == "doc":
        man = json.loads((ROOT / "benchmark" / "identifier_repos.json").read_text())
        names = ["redis", "abseil", "newtonsoft", "play", "pandoc", "ecto", "tokio", "vite"]
        langs = {r["name"]: r["lang"] for r in man["repos"]}
        labels = {f"doc-{n}": f"{langs[n]} — {n}" for n in names}
        repos = a.repos or list(labels)
        tags = a.tags or ["ds1-miru-int8"]
        out_name = a.out or "benchmark/summary.docstring.md"
        lines = ["# Kalpana on Miru: docstring-style natural-language queries", "",
                 "Query = first sentence of the doc comment of one definition (up to 200 per repo, seed from "
                 "benchmark/identifier_repos.json). Corpus = the pinned repo with every definition doc comment removed. "
                 "Correct = a chunk in the file holding that definition (File@3), and for Chunk@3 a chunk in that file "
                 "that defines the identifier. Miru unmodified (top-5 pool); alpha by 5-fold CV, scored on held-out folds.", ""]
        for tag in tags:
            table(tag, repos, "Docstring-style queries, chunk level", lines, labels=labels)
            table(tag, repos, "Docstring-style queries, file level", lines, key="hit3", labels=labels)
            strat_table(tag, repos, lines, labels)
            latency(tag, repos, lines)
    elif a.suite == "id":
        man = json.loads((ROOT / "benchmark" / "identifier_repos.json").read_text())
        live = [r for r in man["repos"] if not r.get("skip")]
        labels = {f"id-{r['name']}": f"{r['lang']} — {r['name']}" for r in live}
        seen = {f"id-{r['name']}" for r in live if r.get("seen")}
        repos = a.repos or list(labels)
        tags = a.tags or ["ds1-miru-int8"]
        out_name = a.out or "benchmark/summary.identifier.md"
        lines = ["# Kalpana on Miru: identifier-style ('where is X defined') queries", "",
                 "Held-out set, separate from the natural-language CodeSearchNet queries. Repos pinned in "
                 "benchmark/identifier_repos.lock.json; query rules and seed fixed in benchmark/identifier_repos.json. "
                 "Miru unmodified (top-5 pool); alpha by 5-fold CV, scored on held-out folds.", ""]
        for tag in tags:
            table(tag, repos, "Identifier-style queries", lines, labels=labels, seen=seen)
            latency(tag, repos, lines)
        skipped = [r for r in man["repos"] if r.get("skip")]
        if skipped:
            lines += ["### Not evaluated", ""] + [f"- **{r['lang']}** ({r['name']}): {r['skip']}" for r in skipped] + [""]
    else:
        repos, tags, out_name = a.repos or CSN + AB, a.tags or ["ds1-miru-int8", "minilm-l6-256"], a.out or "benchmark/summary.md"
        lines = ["# Kalpana on Miru: per-language results", "",
                 "Miru unmodified (top-5 pool). Kalpana fusion: alpha picked by 5-fold CV, scored on held-out folds. "
                 "Win/loss counts queries where a defining chunk enters / leaves the top 3.", ""]
        for tag in tags:
            table(tag, [r for r in repos if r.startswith("csn-")], "CodeSearchNet (docstring -> function)", lines)
            table(tag, [r for r in repos if r.startswith("ab-")], "Curated A/B suite (file-level labels, tiny n)", lines, key="hit3")
            latency(tag, repos, lines)
    out = ROOT / out_name
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
