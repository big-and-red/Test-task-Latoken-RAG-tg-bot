# utils/embedding_generator.py
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from configs.config import config

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Генератор векторов с помощью SentenceTransformer."""

    def __init__(self):
        model_path = Path(
            config.RAG_EMBED_MODELS_CACHE) / "models--sentence-transformers--distiluse-base-multilingual-cased-v1/snapshots/457e815abce54e7e5841550b602b28c0811fd286"

        logger.info(f"Loading model from: {model_path}")

        if not model_path.exists():
            raise ValueError(f"Model not found at {model_path}")

        self.model = SentenceTransformer(str(model_path))
        logger.info(f"Model loaded successfully from: {model_path}")

    def create_embeddings(self, texts: list[str]) -> np.ndarray:
        logger.info(f"Creating embeddings for {len(texts)} texts")
        result = self.model.encode(texts, convert_to_numpy=True)
        logger.info(f"Created embeddings with shape: {result.shape}")
        return result
