"""Priya CLI & Scout Runner.

A standalone runner for scheduled execution (cron / systemd timers)
without requiring Celery or Redis.
"""

import argparse
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.enums import ProcessingStatus, PromotionStatus
from app.database.models.promotion import Promotion
from app.database.models.source import DiscoveredItem, Source
from app.database.session import SessionLocal
from app.discovery.orchestrator import DiscoveryOrchestrator
from app.discovery.scheduler import DiscoveryScheduler, utc_now
from app.intelligence.engine import IntelligenceEngine
from app.notifications.dispatcher import NotificationDispatcher
from app.processing.pipeline import ProcessingPipeline

logger = setup_logging()


async def run_discovery_and_pipeline(force_all_sources: bool = False) -> dict:
    """Run discovery across all due sources, process raw items, verify promotions, and dispatch alerts."""
    results = {
        "sources_checked": 0,
        "sources_scraped": 0,
        "new_items_discovered": 0,
        "items_processed": 0,
        "promotions_created_or_updated": 0,
        "promotions_verified": 0,
        "alerts_dispatched": 0,
    }

    with SessionLocal() as db:
        # 1. Discovery phase
        sources = db.query(Source).filter(Source.is_active == True).all()  # noqa: E712
        results["sources_checked"] = len(sources)

        orchestrator = DiscoveryOrchestrator()
        scheduler = DiscoveryScheduler()
        now = utc_now()
        for source in sources:
            if force_all_sources or scheduler.is_source_due(source, now):
                logger.info(f"Running scraper for source: {source.name} ({source.source_type.value})")
                stats = await orchestrator.collect_source(db, source)
                results["sources_scraped"] += 1
                results["new_items_discovered"] += stats.new_items_saved

        # 2. Processing & Extraction phase
        pipeline = ProcessingPipeline()
        intelligence = IntelligenceEngine()
        dispatcher = NotificationDispatcher()

        pipe_stats = pipeline.process_pending_items(db, limit=100)
        results["items_processed"] = pipe_stats.items_processed
        results["promotions_created_or_updated"] = pipe_stats.promotions_created + pipe_stats.promotions_corroborated

        # 3. Network verification for unverified promotions
        unverified_promos = (
            db.query(Promotion)
            .filter(Promotion.status.in_([PromotionStatus.PENDING, PromotionStatus.UNVERIFIED]))
            .all()
        )
        for promo in unverified_promos:
            intelligence.evaluate_promotion(db, promo, perform_network_check=True)
            results["promotions_verified"] += 1

            # Dispatch real-time alert if verified and not yet notified
            notif = dispatcher.dispatch_promotion_alert(db, promo)
            if notif is not None:
                results["alerts_dispatched"] += 1

        db.commit()

    return results


def check_expiring_deals() -> int:
    """Scan and dispatch alerts for promotions expiring within 48 hours."""
    with SessionLocal() as db:
        dispatcher = NotificationDispatcher()
        count = dispatcher.dispatch_expiring_promotions(db, hours_ahead=48)
        logger.info(f"Dispatched {count} expiring promotion alerts.")
        return count


def print_stats() -> None:
    """Print high-level database stats."""
    with SessionLocal() as db:
        total_sources = db.query(Source).count()
        total_items = db.query(DiscoveredItem).count()
        total_promotions = db.query(Promotion).count()
        active_promotions = (
            db.query(Promotion)
            .filter(Promotion.status.in_([PromotionStatus.VERIFIED, PromotionStatus.LIKELY_VALID]))
            .count()
        )

        print("\n================ Priya Engine Stats ================")
        print(f"Total Sources Monitored: {total_sources}")
        print(f"Total Raw Items Discovered: {total_items}")
        print(f"Total Promotions Extracted: {total_promotions}")
        print(f"Active & Verified Deals:    {active_promotions}")
        print("===================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Priya - AI Subscription Deal Finder CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'run' command
    run_parser = subparsers.add_parser("run", help="Run full discovery, processing, and alerting pipeline")
    run_parser.add_argument(
        "--force", action="store_true", help="Force scrape all sources regardless of last scrape time"
    )

    # 'expiring' command
    subparsers.add_parser("expiring", help="Scan and alert on deals expiring within 48 hours")

    # 'stats' command
    subparsers.add_parser("stats", help="Display current engine metrics")

    args = parser.parse_args()

    if not args.command or args.command == "run":
        force = getattr(args, "force", False)
        print("Starting Priya scout run...")
        results = asyncio.run(run_discovery_and_pipeline(force_all_sources=force))
        print("Scout run completed successfully.")
        for k, v in results.items():
            print(f"  {k}: {v}")
    elif args.command == "expiring":
        count = check_expiring_deals()
        print(f"Processed expiring deals. Sent {count} alerts.")
    elif args.command == "stats":
        print_stats()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
