import logging
import numpy as np
from typing import List, Tuple
from sqlalchemy.orm import Session
from db.models import RagSource, Embedding
from sqlalchemy import select, or_
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine

from services.embedding_service import EmbeddingGenerator

logger = logging.getLogger(__name__)


class SearchService:
    """Сервис для поиска похожих текстов."""

    def __init__(self, session: Session):
        """Сервис использует веса: 70% для семантического (векторного)
        поиска и 30% для поиска по ключевым словам"""
        self.session = session
        self.semantic_weight = 0.7
        self.keyword_weight = 0.3

    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисляет косинусное сходство между векторами."""
        return 1 - cosine(vec1, vec2)

    def calculate_keyword_similarity(self, query: str, text: str) -> float:
        """Вычисляет сходство на основе ключевых слов. TF-IDF."""
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([query, text])
            return (tfidf_matrix * tfidf_matrix.T).toarray()[0][1]
        except:
            return 0.0

    def mmr_rerank(
            self,
            query_vector: List[float],
            candidates: List[Tuple[str, List[float]]],
            lambda_param: float = 0.5,
            max_results: int = 5
    ) -> List[str]:
        """Переранжирует результаты с использованием MMR."""
        selected = []
        remaining = candidates.copy()

        while len(selected) < max_results and remaining:
            mmr_scores = []
            for cand in remaining:
                relevance = self.calculate_cosine_similarity(query_vector, cand[1])

                if not selected:
                    diversity = 0
                else:
                    # Максимальное сходство с уже выбранными документами
                    diversity = max(
                        self.calculate_cosine_similarity(cand[1], sel[1])
                        for sel in selected
                    )

                mmr = lambda_param * relevance - (1 - lambda_param) * diversity
                mmr_scores.append((cand, mmr))

            best_candidate = max(mmr_scores, key=lambda x: x[1])[0]
            selected.append(best_candidate)
            remaining.remove(best_candidate)

        return [text for text, _ in selected]

    async def search(self, source_id: str, query: str, limit: int = 5) -> List[str]:
        """Поиск похожих текстов с гибридным подходом и MMR."""
        logger.info("——— Start search vectors ———")
        logger.info(f"Search query: {query}")

        # Получаем RAG источник
        stmt = select(RagSource).where(RagSource.id == source_id)
        result = self.session.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            raise ValueError(f"Source with ID {source_id} not found")

        # Создаем эмбеддинг для запроса
        embedding_generator = EmbeddingGenerator()
        query_vector = embedding_generator.create_embeddings([query])[0]

        # Получаем расширенный набор кандидатов для последующего переранжирования
        stmt = (
            select(Embedding.text_chunk, Embedding.vector_512)
            .where(Embedding.source_id == source_id)
            .order_by(Embedding.vector_512.op("<=>")(query_vector))
            .limit(limit * 2)  # Берем больше результатов для переранжирования
        )

        result = self.session.execute(stmt)
        candidates = [(row[0], row[1]) for row in result]

        # Гибридное ранжирование
        ranked_results = []
        for text, vector in candidates:
            semantic_score = self.calculate_cosine_similarity(query_vector, vector)
            keyword_score = self.calculate_keyword_similarity(query, text)
            final_score = (
                    semantic_score * self.semantic_weight +
                    keyword_score * self.keyword_weight
            )
            ranked_results.append((text, vector, final_score))

        # Сортируем по финальному скору
        ranked_results.sort(key=lambda x: x[2], reverse=True)

        # Применяем MMR для обеспечения разнообразия
        final_results = self.mmr_rerank(
            query_vector,
            [(text, vector) for text, vector, _ in ranked_results[:limit * 2]],
            lambda_param=0.5,
            max_results=limit
        )

        logger.info("——— End search vectors ———")
        logger.info(f"Found {len(final_results)} chunks")

        # Логируем результаты
        for i, text in enumerate(final_results, 1):
            logger.info(f"Chunk {i}/{len(final_results)}:")
            logger.info(f"{text}")
            logger.info("---")

        return final_results
