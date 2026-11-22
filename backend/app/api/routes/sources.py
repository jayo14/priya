"""API endpoints for source management and manual discovery triggering."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.database.models.enums import ProcessingStatus, SourceType
from app.database.models.source import DiscoveredItem, Source
from app.database.repositories.source_repo import SourceRepository
from app.discovery.orchestrator import DiscoveryOrchestrator

router = APIRouter(tags=["Discovery & Sources"])
orchestrator = DiscoveryOrchestrator()


# --- Pydantic Schemas ---


class SourceCreate(BaseModel):
    name: str = Field(..., max_length=150)
    source_type: SourceType
    identifier: str = Field(..., max_length=255)
    url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    collection_interval_seconds: int = Field(default=3600, ge=60)


class SourceResponse(BaseModel):
    id: int
    name: str
    source_type: SourceType
    identifier: str
    url: Optional[str]
    description: Optional[str]
    is_active: bool
    collection_interval_seconds: int
    last_collected_at: Optional[str]
    last_successful_collection_at: Optional[str]
    last_error_at: Optional[str]
    last_error_message: Optional[str]

    model_config = {"from_attributes": True}


class DiscoveredItemResponse(BaseModel):
    id: int
    source_id: int
    external_id: str
    content_type: str
    title: Optional[str]
    content: str
    author: Optional[str]
    original_url: Optional[str]
    discovered_at: str
    processing_status: str

    model_config = {"from_attributes": True}


class TriggerCollectionResponse(BaseModel):
    source_id: int
    source_name: str
    success: bool
    items_count: int
    error_message: Optional[str] = None


class BatchCollectionResponse(BaseModel):
    sources_processed: int
    items_collected: int
    duplicates_skipped: int
    errors: List[str]


# --- Endpoints ---


@router.get("/sources", response_model=List[SourceResponse])
def list_sources(
    source_type: Optional[SourceType] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = DbSession,
):
    """List all registered discovery sources with optional filtering."""
    stmt = select(Source)
    if source_type:
        stmt = stmt.where(Source.source_type == source_type)
    if is_active is not None:
        stmt = stmt.where(Source.is_active == is_active)
    stmt = stmt.order_by(Source.name).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreate,
    db: Session = DbSession,
):
    """Register a new external discovery source."""
    existing = SourceRepository.get_by_identifier(
        db, source_type=payload.source_type, identifier=payload.identifier
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with identifier '{payload.identifier}' already exists for type {payload.source_type.value}.",
        )

    source = SourceRepository.create(
        db=db,
        name=payload.name,
        source_type=payload.source_type,
        identifier=payload.identifier,
        url=payload.url,
        description=payload.description,
        collection_interval_seconds=payload.collection_interval_seconds,
    )
    return source


@router.get("/sources/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    db: Session = DbSession,
):
    """Get single source details by ID."""
    source = SourceRepository.get_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.post("/sources/{source_id}/collect", response_model=TriggerCollectionResponse)
async def trigger_source_collection(
    source_id: int,
    db: Session = DbSession,
):
    """Manually trigger collection on demand for a single source."""
    source = SourceRepository.get_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    result = await orchestrator.collect_source(db, source)
    return TriggerCollectionResponse(
        source_id=source.id,
        source_name=source.name,
        success=result.success,
        items_count=len(result.items),
        error_message=result.error_message,
    )


@router.post("/discovery/collect-all", response_model=BatchCollectionResponse)
async def trigger_all_collection(
    db: Session = DbSession,
):
    """Trigger collection across all active sources."""
    stats = await orchestrator.collect_all_active_sources(db)
    return BatchCollectionResponse(
        sources_processed=stats.sources_processed,
        items_collected=stats.items_collected,
        duplicates_skipped=stats.duplicates_skipped,
        errors=stats.errors,
    )


@router.get("/discovery/items", response_model=List[DiscoveredItemResponse])
def list_discovered_items(
    source_id: Optional[int] = None,
    processing_status: Optional[ProcessingStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = DbSession,
):
    """List raw discovered items collected from external sources."""
    stmt = select(DiscoveredItem)
    if source_id:
        stmt = stmt.where(DiscoveredItem.source_id == source_id)
    if processing_status:
        stmt = stmt.where(DiscoveredItem.processing_status == processing_status)
    stmt = stmt.order_by(DiscoveredItem.discovered_at.desc()).offset(skip).limit(limit)

    items = list(db.execute(stmt).scalars().all())
    # Format discovered_at to ISO string
    return [
        DiscoveredItemResponse(
            id=item.id,
            source_id=item.source_id,
            external_id=item.external_id,
            content_type=item.content_type,
            title=item.title,
            content=item.content,
            author=item.author,
            original_url=item.original_url,
            discovered_at=item.discovered_at.isoformat(),
            processing_status=item.processing_status.value,
        )
        for item in items
    ]
