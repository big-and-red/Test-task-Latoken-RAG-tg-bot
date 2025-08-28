import logging
from sqlalchemy.orm import Session
from db.models import ActiveRagSource, RagSource

logger = logging.getLogger(__name__)


class ActiveRagSourceRepo:
    def __init__(self, session: Session):
        self.session = session

    def set_active_source(self, user_id: int, source_id: str) -> None:
        """Установка активного RAG источника для пользователя"""
        active_source = self.session.query(ActiveRagSource).filter(
            ActiveRagSource.user_id == user_id
        ).first()

        if active_source:
            active_source.source_id = source_id
        else:
            active_source = ActiveRagSource(user_id=user_id, source_id=source_id)
            self.session.add(active_source)

        self.session.commit()

    def get_active_source(self, user_id: int) -> RagSource:
        """Получение активного RAG источника пользователя"""
        active_source = self.session.query(ActiveRagSource).filter(
            ActiveRagSource.user_id == user_id
        ).first()
        return active_source.source if active_source else None

    def get_all_sources(self, user_id: int = None) -> list[RagSource]:
        """Получение всех доступных RAG источников"""
        query = self.session.query(RagSource).filter(
            RagSource.index_status == 'completed'
        )

        # if user_id is not None:
        #     query = query.filter(RagSource.user_id == user_id)

        return query.all()
