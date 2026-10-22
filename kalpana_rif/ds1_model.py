"""
ds1_model.py -- Takara DS1 as a drop-in token encoder for NeuroVocab.

Duck-types the two SentenceTransformer calls NeuroVocab makes
(`encode`, `get_sentence_embedding_dimension`) on top of the OpenAI-compatible
DS1 endpoint Miru itself uses. numpy + stdlib only.

  * Credentials come from the environment (TAKARA_API_KEY), falling back to the
    gitignored `.env` at the repo root. The key is never printed or stored.
  * Vectors are int8 on the wire; they are dequantised (values * scale) and come
    back unit-norm, same as Miru sees them.
  * Every text is cached on disk (`.bench/ds1_token_cache.jsonl`, keyed by
    model|dim|text) so a re-run costs no API calls and no tokens.
  * `encode(list)` batches and fans out over a small thread pool; transient
    errors (429 / 5xx / network) are retried with backoff.
  * `evict(text)` drops one text from the cache so a benchmark can time a genuine
    cold network encode.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://infer.takara.ai/v1"
DEFAULT_MODEL = "ds1-miru-int8"


def _load_dotenv() -> None:
    f = ROOT / ".env"
    if not f.exists():
        return
    for raw in f.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("'\"")
        os.environ.setdefault(k, v)  # real environment wins over the file


class Ds1Model:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 dim: Optional[int] = None, api_key: Optional[str] = None,
                 cache_path: Optional[Path] = None, batch: int = 128, workers: int = 6) -> None:
        _load_dotenv()
        self.base_url = (base_url or os.environ.get("MIRU_OPENAI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.environ.get("MIRU_OPENAI_EMBEDDING_MODEL") or DEFAULT_MODEL
        self.dim = int(dim or os.environ.get("MIRU_EMBEDDING_DIMENSIONS") or 256)
        self._key = api_key or os.environ.get("TAKARA_API_KEY")
        if not self._key:
            raise RuntimeError("TAKARA_API_KEY is required for the DS1 codebook (set it in the environment or .env)")
        self.batch, self.workers = batch, workers
        self.calls = 0
        self._lock = threading.Lock()
        self._cache: Dict[str, np.ndarray] = {}
        self._path = Path(cache_path) if cache_path else ROOT / ".bench" / "ds1_token_cache.jsonl"
        self._prefix = f"{self.model}|{self.dim}|"
        self._load_cache()

    # ---- SentenceTransformer surface ------------------------------------------------
    def get_sentence_embedding_dimension(self) -> int:
        return self.dim

    def encode(self, texts: Union[str, Sequence[str]], convert_to_numpy: bool = True,
               batch_size: Optional[int] = None, **_: object) -> np.ndarray:
        single = isinstance(texts, str)
        items: List[str] = [texts] if single else list(texts)  # type: ignore[list-item]
        self._fill([t for t in dict.fromkeys(items) if self._prefix + t not in self._cache])
        out = np.stack([self._cache[self._prefix + t] for t in items]) if items else np.zeros((0, self.dim))
        return out[0] if single else out

    # ---- helpers ----------------------------------------------------------------------
    def evict(self, text: str) -> None:
        self._cache.pop(self._prefix + text, None)

    def _load_cache(self) -> None:
        if not self._path.exists():
            return
        with self._path.open() as fh:
            for line in fh:
                try:
                    k, scale, vals = json.loads(line)
                except ValueError:
                    continue
                if k.startswith(self._prefix):
                    self._cache[k] = np.asarray(vals, dtype=np.float32) * np.float32(scale)

    def _fill(self, missing: List[str]) -> None:
        if not missing:
            return
        chunks = [missing[i:i + self.batch] for i in range(0, len(missing), self.batch)]
        if len(chunks) == 1:
            results = [self._request(chunks[0])]
        else:
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                results = list(ex.map(self._request, chunks))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._path.open("a") as fh:
            for texts, rows in zip(chunks, results):
                for t, (scale, vals) in zip(texts, rows):
                    self._cache[self._prefix + t] = np.asarray(vals, dtype=np.float32) * np.float32(scale)
                    fh.write(json.dumps([self._prefix + t, scale, vals]) + "\n")

    def _request(self, texts: List[str]) -> List[tuple]:
        body = json.dumps({"model": self.model, "input": texts, "dimensions": self.dim}).encode()
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        last: Optional[BaseException] = None
        for attempt in range(6):
            try:
                req = urllib.request.Request(f"{self.base_url}/embeddings", body, headers)
                with urllib.request.urlopen(req, timeout=90) as r:
                    payload = json.load(r)
                self.calls += 1
                data = sorted(payload["data"], key=lambda d: d.get("index", 0))
                rows = []
                for d in data:
                    e = d["embedding"]
                    if isinstance(e, dict):
                        rows.append((float(e.get("scale", 1.0)) , [int(v) - int(e.get("zero_point", 0)) for v in e["values"]]))
                    else:  # plain float vector
                        rows.append((1.0, list(e)))
                if len(rows) != len(texts):
                    raise RuntimeError(f"DS1 returned {len(rows)} vectors for {len(texts)} inputs")
                return rows
            except urllib.error.HTTPError as ex:
                last = ex
                if ex.code not in (408, 429, 500, 502, 503, 504):
                    raise RuntimeError(f"DS1 embedding error {ex.code}: {ex.read()[:200]!r}") from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as ex:
                last = ex
            time.sleep(min(30.0, 1.5 * 2 ** attempt))
        raise RuntimeError(f"DS1 embedding failed after retries: {last}")
