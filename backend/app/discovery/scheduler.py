"""Lightweight background collection scheduler for discovery tasks."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import setup_logging
from app.database.models.source import Source
from app.database.repositories.source_repo import SourceRepository
from app.database.session import SessionLocal
from app.discovery.orchestrator import DiscoveryOrchestrator

logger = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DiscoveryScheduler:
    """
    Background worker that runs periodic discovery checks without Celery or Redis.
    Uses asyncio sleep loops with interval checking per source.
    """

    def __init__(self, check_frequency_seconds: float = 60.0):
        self.check_frequency_seconds = check_frequency_seconds
        self.orchestrator = DiscoveryOrchestrator()
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

    def is_source_due(self, source: Source, now: datetime) -> bool:
        """Determine if a source has exceeded its collection_interval_seconds."""
        if not source.is_active:
            return False
        if not source.last_collected_at:
            return True

        elapsed = (now - source.last_collected_at).total_seconds()
        return elapsed >= source.collection_interval_seconds

    async def _run_loop(self):
        """Continuous execution loop checking due sources."""
        logger.info(
            f"Discovery scheduler loop started (check frequency: {self.check_frequency_seconds}s)"
        )
        while self._running:
            try:
                now = utc_now()
                with SessionLocal() as db:
                    active_sources = SourceRepository.list_active(db)
                    due_sources = [s for s in active_sources if self.is_source_due(s, now)]

                    if due_sources:
                        logger.info(
                            f"Scheduler: {len(due_sources)} sources due for collection"
                        )
                        for source in due_sources:
                            if not self._running:
                                break
                            try:
                                await self.orchestrator.collect_source(db, source)
                            except Exception as exc:
                                logger.error(
                                    f"Error running scheduled collection for {source.name}: {exc}"
                                )

            except asyncio.CancelledError:
                logger.info("Discovery scheduler task cancelled")
                break
            except Exception as exc:
                logger.error(f"Unexpected error in scheduler loop: {exc}", exc_info=True)

            try:
                await asyncio.sleep(self.check_frequency_seconds)
            except asyncio.CancelledError:
                break

    def start(self):
        """Start the background scheduler task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Discovery background scheduler task launched")

    def stop(self):
        """Gracefully stop the background scheduler task."""
        if not self._running:
            return
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Discovery background scheduler stopped")


# Global scheduler instance
scheduler = DiscoveryScheduler()
