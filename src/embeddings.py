from __future__ import annotations

import hashlib
import json
import math
from urllib import error
from urllib import request

LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI()

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


class OllamaEmbedder:
    """Ollama API-backed local embedder."""

    def __init__(
        self,
        model_name: str = "all-minilm:l6-v2",
        base_url: str = "http://127.0.0.1:11434",
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._backend_name = f"ollama:{model_name}"

    def __call__(self, text: str) -> list[float]:
        try:
            data = self._post_json(
                endpoint="/api/embed",
                payload={"model": self.model_name, "input": text},
            )
        except error.HTTPError as exc:
            if exc.code != 400:
                raise
            # Older Ollama versions may only support the legacy embeddings endpoint.
            data = self._post_json(
                endpoint="/api/embeddings",
                payload={"model": self.model_name, "prompt": text},
            )

        embeddings = data.get("embeddings")
        if isinstance(embeddings, list) and embeddings:
            first = embeddings[0]
            if isinstance(first, list):
                vector = [float(value) for value in first]
            else:
                vector = [float(value) for value in embeddings]
        elif "embedding" in data:
            vector = [float(value) for value in data["embedding"]]
        else:
            raise ValueError("Ollama embed response did not contain embeddings")

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _post_json(self, endpoint: str, payload: dict) -> dict:
        req = request.Request(
            url=f"{self.base_url}{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))


_mock_embed = MockEmbedder()
