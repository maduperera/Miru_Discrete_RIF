# Kalpana on Miru: per-language results

Miru unmodified (top-5 pool). Kalpana fusion: alpha picked by 5-fold CV, scored on held-out folds. Win/loss counts queries where a defining chunk enters / leaves the top 3.

### CodeSearchNet (docstring -> function)  (`ds1-miru-int8`)

| Repo | n | Native Chunk@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p |
|---|---|---|---|---|---|---|---|
| csn-ruby | 500 | 67.4% | 70.2% | 20 / 6 | 0.009 | 16 / 4 | 0.012 |
| csn-php | 500 | 68.8% | 71.2% | 15 / 3 | 0.008 | 15 / 4 | 0.019 |
| csn-java | 500 | 75.0% | 78.6% | 32 / 14 | 0.011 | 28 / 13 | 0.028 |
| csn-go | 500 | 86.4% | 87.8% | 10 / 3 | 0.092 | 9 / 2 | 0.065 |
| csn-javascript | 500 | 51.4% | 54.4% | 16 / 1 | 0.000 | 13 / 1 | 0.002 |
| csn-python | 500 | 91.0% | 91.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| **Pooled** | 3000 | 73.3% | 75.5% | **93 / 27** | 0.000 | 81 / 24 | 0.000 |

### Curated A/B suite (file-level labels, tiny n)  (`ds1-miru-int8`)

| Repo | n | Native File@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p |
|---|---|---|---|---|---|---|---|
| ab-miru-code | 3 | 100.0% | 100.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| ab-phoenix | 2 | 100.0% | 100.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| ab-axum | 3 | 0.0% | 0.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| ab-serde | 2 | 0.0% | 0.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| **Pooled** | 10 | 50.0% | 50.0% | **0 / 0** | 1.000 | 0 / 0 | 1.000 |

### Latency per query, ms (p50 / p95)  (`ds1-miru-int8`)

| Repo | Miru query embedding (API) | Miru search | Kalpana query, cold | Kalpana query, warm | Kalpana pool scoring |
|---|---|---|---|---|---|
| csn-ruby | 135.5 / 201.6 | 5.1 / 10.2 | 357.9 / 457.9 | 0.2 / 0.5 | 0.0 / 0.1 |
| csn-php | 131.7 / 208.0 | 4.9 / 7.2 | 359.0 / 449.7 | 0.2 / 0.5 | 0.0 / 0.1 |
| csn-java | 128.5 / 180.1 | 6.5 / 9.6 | 354.9 / 461.1 | 0.2 / 0.4 | 0.0 / 0.1 |
| csn-go | 124.0 / 157.9 | 5.5 / 9.1 | 354.5 / 422.2 | 0.2 / 0.4 | 0.1 / 0.1 |
| csn-javascript | 125.3 / 154.0 | 4.0 / 6.7 | 353.8 / 415.5 | 0.2 / 0.4 | 0.1 / 0.1 |
| csn-python | 125.0 / 157.5 | 5.6 / 10.1 | 354.0 / 425.0 | 0.2 / 0.5 | 0.0 / 0.1 |
| ab-miru-code | 246.1 / 412.1 | 10.2 / 11.7 | 359.7 / 378.1 | 0.3 / 0.3 | 0.1 / 0.1 |
| ab-phoenix | 329.9 / 509.9 | 7.4 / 8.2 | 341.6 / 368.2 | 0.2 / 0.3 | 0.0 / 0.1 |
| ab-axum | 255.9 / 370.2 | 8.3 / 9.6 | 355.8 / 357.5 | 0.2 / 0.2 | 0.0 / 0.1 |
| ab-serde | 119.2 / 371.4 | 5.8 / 7.6 | 414.0 / 463.5 | 0.2 / 6.1 | 0.0 / 0.1 |

### CodeSearchNet (docstring -> function)  (`minilm-l6-256`)

| Repo | n | Native Chunk@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p |
|---|---|---|---|---|---|---|---|
| csn-ruby | 500 | 69.8% | 71.8% | 11 / 1 | 0.006 | 11 / 2 | 0.022 |
| csn-php | 500 | 69.6% | 71.8% | 23 / 12 | 0.090 | 23 / 12 | 0.090 |
| csn-java | 500 | 73.0% | 74.6% | 18 / 10 | 0.185 | 16 / 9 | 0.230 |
| csn-go | 500 | 89.4% | 88.2% | 4 / 10 | 0.180 | 4 / 7 | 0.549 |
| csn-javascript | 500 | 54.2% | 54.0% | 8 / 9 | 1.000 | 7 / 9 | 0.804 |
| csn-python | 500 | 91.4% | 91.2% | 0 / 1 | 1.000 | 0 / 1 | 1.000 |
| **Pooled** | 3000 | 74.6% | 75.3% | **64 / 43** | 0.053 | 61 / 40 | 0.046 |

### Curated A/B suite (file-level labels, tiny n)  (`minilm-l6-256`)

| Repo | n | Native File@3 | + Kalpana | Win / Loss vs native | p | Do-no-harm W / L vs top-5 | p |
|---|---|---|---|---|---|---|---|
| ab-miru-code | 3 | 100.0% | 100.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| ab-phoenix | 2 | 100.0% | 100.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| ab-axum | 3 | 0.0% | 0.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| ab-serde | 2 | 0.0% | 0.0% | 0 / 0 | 1.000 | 0 / 0 | 1.000 |
| **Pooled** | 10 | 50.0% | 50.0% | **0 / 0** | 1.000 | 0 / 0 | 1.000 |

### Latency per query, ms (p50 / p95)  (`minilm-l6-256`)

| Repo | Miru query embedding (API) | Miru search | Kalpana query, cold | Kalpana query, warm | Kalpana pool scoring |
|---|---|---|---|---|---|
| csn-ruby | — | 4.3 / 6.2 | 13.8 / 38.7 | 0.1 / 0.2 | 0.0 / 0.0 |
| csn-php | — | 4.6 / 6.7 | 15.0 / 30.9 | 0.1 / 0.2 | 0.0 / 0.1 |
| csn-java | — | 7.6 / 11.6 | 59.4 / 87.8 | 0.1 / 0.2 | 0.0 / 0.1 |
| csn-go | — | 4.9 / 7.4 | 14.4 / 36.7 | 0.1 / 0.2 | 0.0 / 0.1 |
| csn-javascript | — | 4.1 / 7.0 | 11.4 / 28.1 | 0.1 / 0.1 | 0.0 / 0.0 |
| csn-python | — | 6.0 / 10.2 | 16.9 / 54.1 | 0.1 / 0.2 | 0.0 / 0.1 |
| ab-miru-code | — | 9.8 / 9.9 | 13.9 / 20.0 | 0.1 / 0.2 | 0.1 / 0.1 |
| ab-phoenix | — | 5.8 / 7.9 | 13.4 / 15.8 | 0.1 / 0.2 | 0.1 / 0.1 |
| ab-axum | — | 7.7 / 7.7 | 9.6 / 10.3 | 0.1 / 0.1 | 0.0 / 1.0 |
| ab-serde | — | 7.6 / 10.5 | 10.6 / 11.5 | 0.1 / 0.1 | 0.0 / 0.1 |
