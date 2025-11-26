import base64
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import AuthenticatedUser, get_current_user, require_admin
from app.models import Evaluation
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationRead,
    EvaluationUpdate,
    EvaluationListResponse,
)

router = APIRouter()


def _encode_cursor(identifier: int) -> str:
    return base64.urlsafe_b64encode(str(identifier).encode()).decode().rstrip("=")


def _decode_cursor(cursor: Optional[str]) -> Optional[int]:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor + "==").decode()
        return int(raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor")


def _is_admin(auth: AuthenticatedUser) -> bool:
    return "admin" in auth.roles


@router.post("", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    payload: EvaluationCreate,
    db: Session = Depends(get_db),
    auth: AuthenticatedUser = Depends(get_current_user),
):
    evaluation = Evaluation(
        content=payload.content,
        mood_rating=payload.mood_rating,
        is_anonymous=payload.is_anonymous,
        ai_sentiment_score=payload.ai_sentiment_score,
        ai_tags=payload.ai_tags,
        ai_suggested_action=payload.ai_suggested_action,
        processing_status=payload.processing_status or "pending",
        owner_id=auth.user.id,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.get("", response_model=EvaluationListResponse)
def list_evaluations(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthenticatedUser = Depends(get_current_user),
):
    cursor_id = _decode_cursor(cursor)
    query = db.query(Evaluation)
    if not _is_admin(auth):
        query = query.filter(Evaluation.owner_id == auth.user.id)
    if cursor_id is not None:
        query = query.filter(Evaluation.id > cursor_id)

    evaluations = query.order_by(Evaluation.id).limit(limit + 1).all()
    has_more = len(evaluations) > limit
    items = evaluations[:limit]
    next_cursor = _encode_cursor(items[-1].id) if has_more else None

    return EvaluationListResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get("/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    auth: AuthenticatedUser = Depends(get_current_user),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    if not _is_admin(auth) and evaluation.owner_id != auth.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return evaluation


@router.put("/{evaluation_id}", response_model=EvaluationRead)
def update_evaluation(
    evaluation_id: int,
    payload: EvaluationUpdate,
    db: Session = Depends(get_db),
    auth: AuthenticatedUser = Depends(get_current_user),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    if not _is_admin(auth) and evaluation.owner_id != auth.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    auth: AuthenticatedUser = Depends(require_admin),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    db.delete(evaluation)
    db.commit()
    return None
