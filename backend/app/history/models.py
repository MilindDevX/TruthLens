"""
AnalysisHistory SQLAlchemy ORM model.
Stores all analysis results per user with dedup support via content_hash.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SAEnum, Index, Uuid
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ContentType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class AnalysisHistory(Base):
    """
    Stores every analysis result with:
    - Content hash for dedup (SHA-256)
    - Full model scores breakdown (JSON)
    - Explainability data (JSON)
    - Low confidence flag for human-in-the-loop
    """
    __tablename__ = "analysis_history"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(SAEnum(ContentType), nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256 for dedup
    input_preview = Column(Text, nullable=True)  # First 200 chars or thumbnail path
    prediction = Column(String(10), nullable=False)  # "real" or "fake"
    confidence_score = Column(Float, nullable=False)
    credibility_score = Column(Float, nullable=False)
    model_scores = Column(JSON, nullable=True)  # Per-model breakdown
    explainability_data = Column(JSON, nullable=True)  # SHAP values or Grad-CAM path
    model_version = Column(String(20), nullable=False)
    low_confidence_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="analysis_history")

    # Index for user history queries
    __table_args__ = (
        Index("ix_history_user_created", "user_id", "created_at"),
        Index("ix_history_content_hash_user", "content_hash", "user_id"),
    )

    def __repr__(self):
        return f"<AnalysisHistory(id={self.id}, prediction={self.prediction}, confidence={self.confidence_score})>"
