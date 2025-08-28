from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from services.embedding_service import EmbeddingGenerator


class TextService:
    """Сервис для обработки текста."""

    @staticmethod
    def split_text_into_chunks(
            text: str, chunk_size: int = 500, chunk_overlap: int = 200
    ) -> List[str]:
        """Разбиваем текст на чанки."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(text)

    @staticmethod
    def create_embeddings_from_chunks(chunks, model_name_or_path: str) -> np.ndarray:
        """Используем EmbeddingGenerator для создания эмбеддингов."""
        embed_generator = EmbeddingGenerator()
        embeddings = embed_generator.create_embeddings(chunks)
        return embeddings
