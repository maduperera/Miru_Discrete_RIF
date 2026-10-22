# Kalpana on Miru: identifier-style ('where is X defined') queries

Held-out set, separate from the natural-language CodeSearchNet queries. Repos pinned in benchmark/identifier_repos.lock.json; query rules and seed fixed in benchmark/identifier_repos.json. Miru unmodified (top-5 pool); alpha by 5-fold CV, scored on held-out folds.

### Identifier-style queries  (`ds1-miru-int8`)

| Repo | n | Native Chunk@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p | Top-5 ceiling |
|---|---|---|---|---|---|---|---|---|
| c — redis | 43 | 58.1% | 65.1% | 3 / 0 | 0.250 | 3 / 0 | 0.250 | 69.8% |
| cpp — abseil | 57 | 31.6% | 42.1% | 6 / 0 | 0.031 | 6 / 0 | 0.031 | 43.9% |
| csharp — newtonsoft | 200 | 52.5% | 56.5% | 12 / 4 | 0.077 | 11 / 3 | 0.057 | 59.0% |
| scala — play | 200 | 59.5% | 67.5% | 18 / 2 | 0.000 | 23 / 2 | 0.000 | 69.0% |
| haskell — pandoc | 78 | 64.1% | 76.9% | 10 / 0 | 0.002 | 13 / 0 | 0.000 | 78.2% |
| php — laravel | 200 | 64.0% | 74.0% | 22 / 2 | 0.000 | 22 / 1 | 0.000 | 76.0% |
| go — hugo | 200 | 43.5% | 53.0% | 19 / 0 | 0.000 | 27 / 0 | 0.000 | 54.0% |
| elixir — ecto | 28 | 71.4% | 78.6% | 3 / 1 | 0.625 | 2 / 1 | 1.000 | 82.1% |
| javascript — webpack | 200 | 22.0% | 28.0% | 13 / 1 | 0.002 | 16 / 0 | 0.000 | 28.5% |
| java — guava | 200 | 43.5% | 50.5% | 15 / 1 | 0.001 | 10 / 1 | 0.012 | 51.5% |
| ruby — rails | 200 | 66.5% | 73.0% | 16 / 3 | 0.004 | 21 / 3 | 0.000 | 76.5% |
| rust — tokio | 200 | 58.5% | 71.0% | 26 / 1 | 0.000 | 22 / 1 | 0.000 | 73.0% |
| typescript — vite | 47 | 34.0% | 44.7% | 5 / 0 | 0.062 | 5 / 0 | 0.062 | 44.7% |
| python — scikit-learn † | 91 | 58.2% | 71.4% | 12 / 0 | 0.000 | 13 / 0 | 0.000 | 71.4% |
| **Pooled (held-out only)** | 1853 | 51.2% | 59.5% | **168 / 15** | 0.000 | 181 / 12 | 0.000 | |

† used during development, not held-out; excluded from the pooled row.

### Latency per query, ms (p50 / p95)  (`ds1-miru-int8`)

| Repo | Miru query embedding (API) | Miru search | Kalpana query, cold | Kalpana query, warm | Kalpana pool scoring |
|---|---|---|---|---|---|
| id-redis | 128.9 / 176.4 | 19.8 / 23.6 | 362.8 / 454.4 | 0.2 / 0.5 | 0.0 / 0.1 |
| id-abseil | 127.8 / 189.4 | 13.8 / 18.9 | 360.1 / 475.1 | 0.2 / 0.5 | 0.0 / 0.1 |
| id-newtonsoft | 130.5 / 153.9 | 11.4 / 15.7 | 358.9 / 435.3 | 0.2 / 0.3 | 0.0 / 0.1 |
| id-play | 126.0 / 168.8 | 15.6 / 30.6 | 367.6 / 482.4 | 0.3 / 0.9 | 0.1 / 0.1 |
| id-pandoc | 127.6 / 145.8 | 11.2 / 14.6 | 369.7 / 465.1 | 0.2 / 0.3 | 0.0 / 0.1 |
| id-laravel | 128.8 / 150.5 | 24.0 / 71.3 | 359.6 / 437.9 | 0.2 / 0.4 | 0.1 / 0.1 |
| id-hugo | 125.6 / 232.8 | 13.0 / 20.2 | 362.0 / 476.9 | 0.2 / 0.5 | 0.0 / 0.1 |
| id-ecto | 130.2 / 209.7 | 5.3 / 6.8 | 368.0 / 416.4 | 0.2 / 1.6 | 0.0 / 0.1 |
| id-webpack | 127.6 / 167.4 | 45.7 / 60.9 | 369.0 / 460.7 | 0.3 / 0.4 | 0.1 / 0.1 |
| id-guava | 126.1 / 212.0 | 35.9 / 50.8 | 361.6 / 439.7 | 0.2 / 0.4 | 0.1 / 0.1 |
| id-rails | 124.2 / 182.7 | 25.8 / 34.3 | 362.7 / 487.1 | 0.2 / 0.4 | 0.1 / 0.1 |
| id-tokio | 125.7 / 221.5 | 8.7 / 12.2 | 359.7 / 480.2 | 0.2 / 0.3 | 0.0 / 0.1 |
| id-vite | 120.7 / 164.0 | 9.5 / 15.8 | 352.5 / 415.2 | 0.2 / 0.5 | 0.0 / 0.1 |
| id-scikit-learn | 122.0 / 162.4 | 20.6 / 29.7 | 363.7 / 459.4 | 0.2 / 0.5 | 0.0 / 0.1 |

### Not evaluated

- **dart** (flame): vendored tree-sitter-dart.wasm cannot be loaded by web-tree-sitter 0.26.13 (getDylinkMetadata fails: legacy dylink section), so neither roles nor definitions can be extracted
- **ocaml** (dune): Miru does not index .ml: no entry in @takara-ai/miru-code src/index/files.ts EXTENSION_TO_LANGUAGE although the OCaml grammar is vendored
- **solidity** (openzeppelin): Miru does not index .sol: no entry in EXTENSION_TO_LANGUAGE although the Solidity grammar is vendored (pilot: 0 of 2470 chunks were Solidity, pool recall 0%)
