#!/bin/sh
# Docstring-style natural-language suite, end to end, with Takara DS1 (Miru retrieval + Kalpana codebook).
#   PY=.venv/bin/python sh scripts/run_doc_suite.sh [name ...]      (names from benchmark/identifier_repos.json;
#                                                                    default: the 8 languages that had no NL queries)
# Per repo: pinned identifier-suite checkout (eval-repos/id-<name>) -> doc-comment extraction + doc-stripped copy
# (eval-repos/doc-<name>) -> 200 seeded queries (benchmark/queries.doc-<name>.json) -> DS1 index of the stripped copy
# -> Miru top-3/5 pools -> Kalpana fusion + paired tests. One repo at a time so latency is not distorted.
# Logs: benchmark/logs/ds1.doc-<name>.log ; results: benchmark/results.kalpana.ds1-miru-int8.queries.doc-<name>.k5.ts.json
set -e
export EMBEDDER=ds1
PY=${PY:-python3}; export PY
mkdir -p benchmark/logs .bench/docq
SEED=$(node -p "require('./benchmark/identifier_repos.json').seed")
N=$(node -p "require('./benchmark/identifier_repos.json').queriesPerRepo")
NAMES=${*:-"redis abseil newtonsoft play pandoc ecto tokio vite"}
for NAME in $NAMES; do
  LANG=$(node -p "(require('./benchmark/identifier_repos.json').repos.find(r=>r.name===process.argv[1])||{}).lang" "$NAME")
  R=doc-$NAME
  echo "=== $R ($LANG) $(date +%H:%M:%S)"
  [ -d eval-repos/id-$NAME ] || npx tsx scripts/fetch_identifier_repos.ts $NAME 2>&1 | tail -2
  [ -d eval-repos/id-$NAME ] || { echo "SKIP $R: no checkout"; continue; }
  [ -f .bench/docq/$NAME.json ] && [ -d eval-repos/$R ] || npx tsx scripts/extract_docqueries.ts eval-repos/id-$NAME $LANG .bench/docq/$NAME.json --strip eval-repos/$R 2>&1 | tail -2
  [ -f benchmark/queries.$R.json ] || $PY miru_kalpana/gen_queries_doc.py --name $NAME --n $N --seed $SEED 2>&1 | tail -2
  [ -f benchmark/queries.$R.json ] || { echo "SKIP $R: no queries generated"; continue; }
  # The Bun indexer crashed intermittently (tokio, vite on the first run) and worked on a plain re-run: retry once.
  for TRY in 1 2; do
    [ -f .miru/$R-ds1/index/metadata.json ] || npx tsx scripts/index_repo.ts $R 2>&1 | tail -1
  done
  sh scripts/run_lang.sh $R > benchmark/logs/ds1.$R.log 2>&1 || echo "FAILED $R (see benchmark/logs/ds1.$R.log)"
done
echo "=== done $(date +%H:%M:%S)"
