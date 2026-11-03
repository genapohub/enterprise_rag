"""Embedding client: SiliconFlow BGE-M3 or deterministic stub."""
import hashlib
import math
from typing import List
import httpx
from app.config import Settings


class EmbeddingClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.stub = settings.use_embedding_stub()

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.stub:
            return [self._stub_vec(t) for t in texts]
        return self._api_embed(texts)

    def _stub_vec(self, text: str) -> List[float]:
        dim = self.settings.embedding_dim
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        vals = []
        buf = seed
        while len(vals) < dim:
            buf = hashlib.sha256(buf).digest()
            for b in buf:
                vals.append((b / 255.0) * 2 - 1)
                if len(vals) >= dim:
                    break
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        return [v / norm for v in vals]

    def _api_embed(self, texts: List[str]) -> List[List[float]]:
        url = self.settings.embedding_base_url.rstrip("/") + "/embeddings"
        headers = {
            "Authorization": f"Bearer {self.settings.embedding_api_key}",
            "Content-Type": "application/json",
        }
        out: List[List[float]] = []
        batch = 32
        with httpx.Client(timeout=60.0) as client:
            for i in range(0, len(texts), batch):
                payload = {"model": self.settings.embedding_model, "input": texts[i : i + batch]}
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()["data"]
                data = sorted(data, key=lambda x: x["index"])
                out.extend([d["embedding"] for d in data])
        return out
