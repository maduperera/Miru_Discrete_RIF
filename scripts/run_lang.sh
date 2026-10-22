#!/bin/sh
# Per-repo multi-language pipeline: Miru topK=3/5 pools -> tree-sitter roles -> Kalpana benchmark -> paired tests.
#   sh scripts/run_lang.sh <repo>                    # MiniLM (default; reproduces the earlier results)
#   EMBEDDER=ds1 sh scripts/run_lang.sh <repo>       # Takara DS1 for Miru's retrieval AND the Kalpana codebook
# DS1 needs TAKARA_API_KEY (environment or the gitignored .env) and an index built with the same embedder:
#   EMBEDDER=ds1 npx tsx scripts/index_repo.ts <repo>      -> .miru/<repo>-ds1/index
# PY selects the Python interpreter (default python3), e.g. PY=.venv/bin/python
set -e
R=$1
EMB=${EMBEDDER:-minilm}
export EMBEDDER=$EMB   # an explicit value here beats whatever .env says
PY=${PY:-python3}
Q=benchmark/queries.$R.json
if [ "$EMB" = ds1 ]; then
  TAG=ds1-miru-int8; IDX=.miru/$R-ds1/index
else
  TAG=minilm-l6-256; IDX=.miru/$R/index
fi
B=.bench/kalpana/candidates.$TAG.queries.$R
for K in 3 5; do
  npx tsx benchmark/dump_candidates.ts --k $K --queries $Q --index $IDX
  npx tsx scripts/extract_roles.ts pool $B.k$K.json $B.k$K.ts.json
done
$PY miru_kalpana/benchmark_kalpana_fusion.py --extractor treesitter --examples 0 --embedder $EMB \
  --candidates $B.k5.ts.json --queries $Q
$PY miru_kalpana/rerank_vs_native.py --repo $R --tag $TAG
