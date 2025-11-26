from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, conint


class EvaluationBase(BaseModel):
    content: str
    mood_rating: conint(ge=1, le=10) = 5
    is_anonymous: bool = False
    ai_sentiment_score: float | None = None
    ai_tags: list[str] | None = None
    ai_suggested_action: str | None = None
    processing_status: str | None = "pending"

    @field_validator("ai_tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [tag.strip() for tag in value.split(",") if tag.strip()]
        return list(value)


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(BaseModel):
    content: str | None = None
    mood_rating: conint(ge=1, le=10) | None = None
    is_anonymous: bool | None = None
    ai_sentiment_score: float | None = None
    ai_tags: list[str] | None = None
    ai_suggested_action: str | None = None
    processing_status: str | None = None

    @field_validator("ai_tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [tag.strip() for tag in value.split(",") if tag.strip()]
        return list(value)


class EvaluationRead(EvaluationBase):
    id: int
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationListResponse(BaseModel):
    items: list[EvaluationRead]
    next_cursor: str | None
    has_more: bool

