"""Probe the DS1 endpoint: response shape, dims, norms, latency. Key read from .env, never printed."""
import json, math, os, time, urllib.request

env = dict(l.strip().split("=", 1) for l in open(".env") if "=" in l and not l.startswith("#"))
base, model, key = env["MIRU_OPENAI_BASE_URL"], env["MIRU_OPENAI_EMBEDDING_MODEL"], env["TAKARA_API_KEY"]


def call(inp, q):
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if q:
        h["X-Q"] = "1"
    req = urllib.request.Request(f"{base}/embeddings", json.dumps({"model": model, "input": inp}).encode(), h)
    t = time.perf_counter()
    d = json.load(urllib.request.urlopen(req, timeout=60))
    return d, (time.perf_counter() - t) * 1000


d, ms = call(["resource slice indexers", "func CreateToken(ctx context.Context)"], True)
e = d["data"][0]["embedding"]
print("embedding keys:", {k: (v if k != "values" else f"<{len(v)} ints>") for k, v in e.items()})
print("top-level keys:", [k for k in d if k != "data"], "usage:", d.get("usage"))
print("n items:", len(d["data"]), "first-call ms:", round(ms, 1))
v = e["values"]
print("L2 of raw ints:", round(math.sqrt(sum(x * x for x in v)), 3), "min/max:", min(v), max(v))

for q in (True, False):
    ts = [call(["resource slice indexers"], q)[1] for _ in range(10)]
    ts.sort()
    print(f"single-query latency X-Q={q}: p50={ts[5]:.0f} ms, p95~{ts[-1]:.0f} ms")

# batch limits
for n in (16, 64, 128):
    try:
        _, ms = call([f"func f{i}() {{}}" for i in range(n)], False)
        print(f"batch {n}: ok {ms:.0f} ms")
    except Exception as ex:
        print(f"batch {n}: {ex}")
        break
