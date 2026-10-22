# Kalpana on Miru: docstring-style natural-language queries

Query = first sentence of the doc comment of one definition (up to 200 per repo, seed from benchmark/identifier_repos.json). Corpus = the pinned repo with every definition doc comment removed. Correct = a chunk in the file holding that definition (File@3), and for Chunk@3 a chunk in that file that defines the identifier. Miru unmodified (top-5 pool); alpha by 5-fold CV, scored on held-out folds.

### Docstring-style queries, chunk level  (`ds1-miru-int8`)

| Repo | n | Native Chunk@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p | Top-5 ceiling |
|---|---|---|---|---|---|---|---|---|
| c — redis | 200 | 26.0% | 26.0% | 2 / 2 | 1.000 | 4 / 0 | 0.125 | 26.5% |
| cpp — abseil | 200 | 20.0% | 25.5% | 11 / 0 | 0.001 | 10 / 0 | 0.002 | 26.5% |
| csharp — newtonsoft | 200 | 28.0% | 34.0% | 12 / 0 | 0.000 | 11 / 0 | 0.001 | 34.5% |
| scala — play | 200 | 39.5% | 46.5% | 15 / 1 | 0.001 | 14 / 1 | 0.001 | 48.0% |
| haskell — pandoc | 200 | 27.0% | 30.0% | 8 / 2 | 0.109 | 9 / 2 | 0.065 | 32.0% |
| elixir — ecto | 200 | 29.0% | 37.0% | 18 / 2 | 0.000 | 14 / 0 | 0.000 | 37.5% |
| rust — tokio | 200 | 27.5% | 31.0% | 9 / 2 | 0.065 | 8 / 1 | 0.039 | 32.0% |
| typescript — vite | 137 | 25.5% | 28.5% | 5 / 1 | 0.219 | 5 / 1 | 0.219 | 29.2% |
| **Pooled** | 1537 | 27.9% | 32.5% | **80 / 10** | 0.000 | 75 / 5 | 0.000 | |

### Docstring-style queries, file level  (`ds1-miru-int8`)

| Repo | n | Native File@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p | Top-5 ceiling |
|---|---|---|---|---|---|---|---|---|
| c — redis | 200 | 74.5% | 74.0% | 9 / 10 | 1.000 | 9 / 10 | 1.000 | 82.5% |
| cpp — abseil | 200 | 61.5% | 61.0% | 14 / 15 | 1.000 | 14 / 16 | 0.856 | 72.0% |
| csharp — newtonsoft | 200 | 52.0% | 56.0% | 17 / 9 | 0.169 | 16 / 10 | 0.327 | 65.0% |
| scala — play | 200 | 56.0% | 62.5% | 17 / 4 | 0.007 | 16 / 4 | 0.012 | 66.0% |
| haskell — pandoc | 200 | 61.0% | 62.0% | 12 / 10 | 0.832 | 14 / 8 | 0.286 | 69.5% |
| elixir — ecto | 200 | 60.5% | 70.0% | 23 / 4 | 0.000 | 15 / 4 | 0.019 | 75.0% |
| rust — tokio | 200 | 67.0% | 67.5% | 5 / 4 | 1.000 | 4 / 2 | 0.688 | 71.0% |
| typescript — vite | 137 | 56.2% | 57.7% | 4 / 2 | 0.688 | 5 / 1 | 0.219 | 62.8% |
| **Pooled** | 1537 | 61.3% | 64.1% | **101 / 58** | 0.001 | 93 / 55 | 0.002 | |

### Split by name overlap, chunk level  (`ds1-miru-int8`)

Queries whose words include every word of the identifier name (e.g. 'parse request' for parseRequest) are easier by construction. The second block keeps only queries that do not.

| Subset | n | Native Chunk@3 | + Kalpana | Win / Loss | p |
|---|---|---|---|---|---|
| query contains every word of the identifier | 351 | 37.0% | 43.0% | 24 / 3 | 0.000 |
| query does not (pure natural language) | 1186 | 25.2% | 29.3% | 56 / 7 | 0.000 |

### Latency per query, ms (p50 / p95)  (`ds1-miru-int8`)

| Repo | Miru query embedding (API) | Miru search | Kalpana query, cold | Kalpana query, warm | Kalpana pool scoring |
|---|---|---|---|---|---|
| doc-redis | 126.5 / 164.7 | 29.1 / 61.8 | 361.4 / 505.5 | 0.2 / 0.5 | 0.1 / 0.1 |
| doc-abseil | 123.0 / 145.5 | 20.7 / 37.9 | 359.4 / 453.1 | 0.2 / 0.3 | 0.1 / 0.1 |
| doc-newtonsoft | 124.2 / 156.5 | 18.8 / 40.2 | 356.5 / 579.2 | 0.2 / 0.4 | 0.0 / 0.1 |
| doc-play | 124.2 / 160.0 | 28.5 / 53.1 | 361.8 / 527.0 | 0.2 / 0.5 | 0.1 / 0.1 |
| doc-pandoc | 126.7 / 187.7 | 16.7 / 37.2 | 365.2 / 474.5 | 0.2 / 0.6 | 0.0 / 0.1 |
| doc-ecto | 123.8 / 161.9 | 6.5 / 12.5 | 355.3 / 429.7 | 0.2 / 0.4 | 0.0 / 0.1 |
| doc-tokio | 127.5 / 155.8 | 11.4 / 18.1 | 366.1 / 484.7 | 0.2 / 0.4 | 0.1 / 0.1 |
| doc-vite | 129.7 / 555.3 | 15.1 / 25.5 | 360.5 / 457.4 | 0.2 / 0.4 | 0.1 / 0.1 |
