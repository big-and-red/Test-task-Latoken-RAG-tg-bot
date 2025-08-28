import logging
from typing import List
import numpy as np
from sqlalchemy.orm import Session
from db.models import Embedding, RagSource

logger = logging.getLogger(__name__)


class EmbeddingRepo:
    """Репозиторий для работы с векторными эмбеддингами."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def delete_by_source_id(self, source_id: str) -> None:
        """Удаляет эмбеддинги для указанного источника."""
        try:
            self.session.query(Embedding).filter_by(source_id=source_id).delete()
            self.session.commit()
            logger.info(f"Удалены все эмбеддинги для источника: {source_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Ошибка при удалении эмбеддингов: {e}")
            raise

    def insert_data(
            self, embeddings_np: np.ndarray, chunks: List[str], source_id: str
    ) -> None:
        """Вставляет эмбеддинги в БД."""
        try:
            # Проверяем существование источника
            source = self.session.query(RagSource).filter_by(id=source_id).first()
            if not source:
                raise ValueError(f"Источник с id {source_id} не найден")

            # Создаем объекты эмбеддингов
            embeddings = [
                Embedding(
                    vector_512=vector.tolist(),
                    text_chunk=text,
                    source_id=source_id
                )
                for vector, text in zip(embeddings_np, chunks)
            ]

            self.session.bulk_save_objects(embeddings)
            self.session.commit()

            logger.info(
                "Добавлено %d новых эмбеддингов для источника: %s",
                len(embeddings),
                source_id
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Ошибка при сохранении эмбеддингов: {e}")
            raise

    def search_similar(
            self, query_vector: np.ndarray, source_ids: List[str], limit: int = 5
    ) -> List[str]:
        """Поиск похожих текстовых фрагментов."""
        try:
            results = (
                self.session.query(Embedding)
                .filter(Embedding.source_id.in_(source_ids))
                .order_by(Embedding.vector_512.op("<->")(query_vector))
                .limit(limit)
                .all()
            )

            texts = [result.text_chunk for result in results]

            logger.info("Найдено %d похожих фрагментов", len(texts))
            logger.debug("Найденные фрагменты: %s", texts)

            return texts

        except Exception as e:
            logger.error(f"Ошибка при поиске похожих фрагментов: {e}")
            raise
        finally:
            self.session.close()
