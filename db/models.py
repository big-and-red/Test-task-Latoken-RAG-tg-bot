from sqlalchemy import Column, String, BigInteger, ForeignKey, Text
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from db.base import BaseModel, Base


class RagSource(Base, BaseModel):
    __tablename__ = "rag_sources"

    name = Column(String, nullable=False, comment="Source name (from filename)")
    source_type = Column(String, nullable=False, comment="Type of source (pdf, txt, doc, etc)")
    index_status = Column(String, nullable=False, default="pending", comment="Indexing status")
    user_id = Column(BigInteger, nullable=False, comment="Telegram user ID")

    # Связь с векторами
    embeddings = relationship("Embedding", back_populates="source", cascade="all, delete-orphan")


class Embedding(Base, BaseModel):
    __tablename__ = "embeddings"

    text_chunk = Column(Text, nullable=False, comment="Text chunk")
    vector_512 = Column(Vector(512), nullable=False, comment="Embedding vector (512 dimensions)")

    # Связь с источником
    source_id = Column(UUID, ForeignKey("rag_sources.id"), nullable=False)
    source = relationship("RagSource", back_populates="embeddings")


class ActiveRagSource(Base, BaseModel):
    __tablename__ = "active_rag_sources"

    user_id = Column(BigInteger, nullable=False, unique=True, comment="Telegram user ID")
    source_id = Column(UUID, ForeignKey("rag_sources.id"), nullable=False)
    source = relationship("RagSource")
