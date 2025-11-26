from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    mood_rating = Column(Integer, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    ai_sentiment_score = Column(Float, nullable=True)
    ai_tags = Column(JSON, nullable=True)
    ai_suggested_action = Column(Text, nullable=True)
    processing_status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    owner = relationship("User", back_populates="evaluations")

