#!/bin/sh
# DS1 re-run of Miru's own suites (same repos/queries as scripts/run_miru_suite.sh), one repo at a time so the
# per-query latency numbers are not distorted by parallel load. Logs -> benchmark/logs/ds1.<repo>.log
#   PY=.venv/bin/python sh scripts/run_ds1_suite.sh [repo ...]
# Default repo list = CodeSearchNet x6 + the four curated A/B repos from the first report.
set -e
export EMBEDDER=ds1
mkdir -p benchmark/logs
REPOS=${*:-"csn-ruby csn-php csn-java csn-go csn-javascript csn-python ab-miru-code ab-phoenix ab-axum ab-serde"}
for R in $REPOS; do
  [ -f benchmark/queries.$R.json ] || { echo "skip $R (no query file)"; continue; }
  echo "=== $R $(date +%H:%M:%S)"
  [ -f .miru/$R-ds1/index/metadata.json ] || npx tsx scripts/index_repo.ts $R
  sh scripts/run_lang.sh $R > benchmark/logs/ds1.$R.log 2>&1 || echo "FAILED $R (see benchmark/logs/ds1.$R.log)"
done
echo "=== done $(date +%H:%M:%S)"
