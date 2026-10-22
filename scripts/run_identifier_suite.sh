#!/bin/sh
# Identifier-style multi-language suite, end to end, with Takara DS1 (Miru retrieval + Kalpana codebook).
#   PY=.venv/bin/python sh scripts/run_identifier_suite.sh [name ...]     (names from benchmark/identifier_repos.json)
# Steps per repo: pinned fetch -> tree-sitter definitions -> identifier queries (fixed seed, separate files
# benchmark/queries.id-<name>.json) -> DS1 index -> Miru top-3/5 pools -> Kalpana fusion + paired tests.
# One repo at a time so the latency numbers are not distorted by parallel load.
# Logs: benchmark/logs/ds1.id-<name>.log ; per-query results: benchmark/results.kalpana.ds1-miru-int8.queries.id-<name>.k5.ts.json
set -e
export EMBEDDER=ds1
PY=${PY:-python3}; export PY
mkdir -p benchmark/logs
SEED=$(node -p "require('./benchmark/identifier_repos.json').seed")
N=$(node -p "require('./benchmark/identifier_repos.json').queriesPerRepo")
LIST=$(node -e "const m=require('./benchmark/identifier_repos.json');const only=process.argv.slice(1);for(const r of m.repos)if(!r.skip&&(!only.length||only.includes(r.name)))console.log(r.name+' '+r.lang)" -- "$@")
echo "$LIST" | while read NAME LANG; do
  [ -n "$NAME" ] || continue
  R=id-$NAME
  echo "=== $R ($LANG) $(date +%H:%M:%S)"
  npx tsx scripts/fetch_identifier_repos.ts $NAME 2>&1 | tail -2
  [ -d eval-repos/$R ] || { echo "SKIP $R: fetch failed"; continue; }
  [ -f benchmark/queries.$R.json ] || $PY miru_kalpana/gen_queries_multi.py --repo $R --lang $LANG --n $N --seed $SEED 2>&1 | tail -3
  [ -f benchmark/queries.$R.json ] || { echo "SKIP $R: no queries generated"; continue; }
  [ -f .miru/$R-ds1/index/metadata.json ] || npx tsx scripts/index_repo.ts $R 2>&1 | tail -1
  sh scripts/run_lang.sh $R > benchmark/logs/ds1.$R.log 2>&1 || echo "FAILED $R (see benchmark/logs/ds1.$R.log)"
done
echo "=== done $(date +%H:%M:%S)"
