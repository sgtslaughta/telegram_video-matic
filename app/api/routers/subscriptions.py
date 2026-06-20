"""Subscriptions router: CRUD + duplicate detection + scan."""
import re

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.api.deps import get_db, require_app_auth
from app.api.schemas import SubscriptionRead, SubscriptionCreateRequest, SubscriptionUpdateRequest
from app.db import repositories as repo_module

router = APIRouter(
    prefix="/api/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(require_app_auth)],
)


@router.get("")
async def list_subscriptions(db: AsyncSession = Depends(get_db)):
    """GET /api/subscriptions — list all subscriptions."""
    subs = await repo_module.subscriptions.list(db)
    return [SubscriptionRead.model_validate(s) for s in subs]


def _validate_regex(pattern):
    """Reject an invalid filter regex with HTTP 400 (plan-specified code)."""
    if pattern:
        try:
            re.compile(pattern)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid filter_regex: {e}")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    req: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """POST /api/subscriptions — create subscription."""
    _validate_regex(req.filter_regex)
    existing = await repo_module.subscriptions.get_by_channel_topic(
        db, req.channel_id, req.topic_id
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Subscription already exists for this channel/topic",
        )

    try:
        sub = await repo_module.subscriptions.create(
            db,
            channel_id=req.channel_id,
            topic_id=req.topic_id,
            enabled=req.enabled,
            mode=req.mode,
            filter_regex=req.filter_regex,
            filter_mode=req.filter_mode,
            min_size_mb=req.min_size_mb,
            max_size_mb=req.max_size_mb,
            storage_path=req.storage_path,
            rename_template=req.rename_template,
            season_detection=req.season_detection,
            retention_days=req.retention_days,
            retention_disk_pct=req.retention_disk_pct,
        )
        return SubscriptionRead.model_validate(sub)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Subscription already exists for this channel/topic",
        )


@router.get("/{sub_id}")
async def get_subscription(sub_id: int, db: AsyncSession = Depends(get_db)):
    """GET /api/subscriptions/{id} — get single subscription."""
    sub = await repo_module.subscriptions.get(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return SubscriptionRead.model_validate(sub)


@router.patch("/{sub_id}")
async def update_subscription(
    sub_id: int,
    req: SubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """PATCH /api/subscriptions/{id} — update subscription."""
    sub = await repo_module.subscriptions.get(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = req.model_dump(exclude_unset=True)
    if "filter_regex" in update_data:
        _validate_regex(update_data["filter_regex"])
    updated = await repo_module.subscriptions.update(db, sub_id, **update_data)
    return SubscriptionRead.model_validate(updated)


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(sub_id: int, db: AsyncSession = Depends(get_db)):
    """DELETE /api/subscriptions/{id} — delete subscription."""
    await repo_module.subscriptions.delete(db, sub_id)


@router.post("/{sub_id}/scan")
async def scan_subscription(sub_id: int, db: AsyncSession = Depends(get_db)):
    """POST /api/subscriptions/{id}/scan — force manual poll."""
    sub = await repo_module.subscriptions.get(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {"status": "scanning"}
