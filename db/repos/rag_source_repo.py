import logging
from sqlalchemy.orm import Session
from db.models import RagSource

logger = logging.getLogger(__name__)


class RagSourceRepo:
    """Упрощенный репозиторий для работы с RAG источниками данных."""

    def __init__(self, session: Session):
        self.session = session

    def create_source_from_archive(self, filename: str, user_id: int) -> RagSource:
        """Создание нового RAG источника из архива."""
        source = RagSource(
            name=filename,
            source_type='archive',
            index_status='pending',
            user_id=user_id
        )

        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)

        return source

    def update_index_status(self, source_id: str, status: str) -> None:
        """Обновляет статус индексации источника."""
        source = self.session.query(RagSource).filter(RagSource.id == source_id).first()
        if source:
            source.index_status = status
            self.session.commit()

    def get_by_id(self, source_id: str) -> RagSource:
        """Получение источника по ID."""
        return self.session.query(RagSource).filter(RagSource.id == source_id).first()
