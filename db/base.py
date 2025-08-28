from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, UUID
import uuid

Base = declarative_base()


class BaseModel:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
