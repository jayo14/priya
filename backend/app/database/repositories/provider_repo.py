"""Provider and Subscription Plan repository."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.provider import Plan, Provider


class ProviderRepository:
    """Explicit database access for AI Providers and Plans."""

    @staticmethod
    def get_by_id(db: Session, provider_id: int) -> Optional[Provider]:
        return db.get(Provider, provider_id)

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Provider]:
        stmt = select(Provider).where(Provider.slug == slug)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_active(db: Session, skip: int = 0, limit: int = 100) -> List[Provider]:
        stmt = (
            select(Provider)
            .where(Provider.is_active.is_(True))
            .order_by(Provider.name)
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_plan_by_id(db: Session, plan_id: int) -> Optional[Plan]:
        return db.get(Plan, plan_id)

    @staticmethod
    def get_plan_by_slug(db: Session, provider_id: int, slug: str) -> Optional[Plan]:
        stmt = select(Plan).where(Plan.provider_id == provider_id, Plan.slug == slug)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_plans_by_provider(db: Session, provider_id: int) -> List[Plan]:
        stmt = (
            select(Plan)
            .where(Plan.provider_id == provider_id, Plan.is_active.is_(True))
            .order_by(Plan.name)
        )
        return list(db.execute(stmt).scalars().all())
