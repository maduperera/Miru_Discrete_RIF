# Independent re-labelling of the identifier-style results

A chunk is correct if its text lexically defines the query identifier, decided by Pygments lexers (C, C++, C#, Scala, Haskell, PHP, Java, Ruby, Rust) or hand-written regexes (Go, Elixir, JavaScript, TypeScript), **not** by Miru's tree-sitter extraction. Same pools, arms and held-out alphas as the main table. Win/loss is Kalpana vs Miru native top-3.

| Language (repo) | n | Native (tree-sitter label) | + Kalpana (tree-sitter) | Native (independent) | + Kalpana (independent) | Win / Loss (independent) | p | vs same top-5 pool W / L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| c (redis) | 43 | 58.1% | 65.1% | 69.8% | 74.4% | 3 / 1 | 0.625 | 3 / 1 |
| cpp (abseil) | 57 | 31.6% | 42.1% | 29.8% | 33.3% | 2 / 0 | 0.500 | 3 / 0 |
| csharp (newtonsoft) | 200 | 52.5% | 56.5% | 50.0% | 53.0% | 10 / 4 | 0.180 | 12 / 3 |
| scala (play) | 200 | 59.5% | 67.5% | 75.5% | 81.0% | 14 / 3 | 0.013 | 19 / 2 |
| haskell (pandoc) | 78 | 64.1% | 76.9% | 44.9% | 51.3% | 5 / 0 | 0.062 | 6 / 0 |
| php (laravel) | 200 | 64.0% | 74.0% | 70.5% | 78.0% | 21 / 6 | 0.006 | 18 / 5 |
| go (hugo) | 200 | 43.5% | 53.0% | 43.5% | 53.0% | 19 / 0 | 0.000 | 26 / 0 |
| elixir (ecto) | 28 | 71.4% | 78.6% | 50.0% | 53.6% | 2 / 1 | 1.000 | 2 / 1 |
| javascript (webpack) | 200 | 22.0% | 28.0% | 50.0% | 52.5% | 9 / 4 | 0.267 | 8 / 4 |
| java (guava) | 200 | 43.5% | 50.5% | 52.0% | 58.0% | 16 / 4 | 0.012 | 11 / 6 |
| ruby (rails) | 200 | 66.5% | 73.0% | 65.5% | 70.5% | 13 / 3 | 0.021 | 19 / 3 |
| rust (tokio) | 200 | 58.5% | 71.0% | 64.0% | 75.5% | 26 / 3 | 0.000 | 22 / 3 |
| typescript (vite) | 47 | 34.0% | 44.7% | 55.3% | 63.8% | 5 / 1 | 0.219 | 5 / 1 |
| python (scikit-learn) † | 91 | 58.2% | 71.4% | 58.2% | 71.4% | 12 / 0 | 0.000 | 13 / 0 |
| **Pooled held-out** | 1853 | 51.2% | 59.5% | 57.4% | 63.6% | **145 / 30** | 0.000 | 154 / 29 |

† not held-out (used in development); excluded from the pooled row.
