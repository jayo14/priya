"""Idempotent seed data for initial AI providers and subscription plans."""

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.provider import Plan, Provider
from app.database.session import SessionLocal

logger = setup_logging()

SEED_CATALOGUE: List[Dict[str, Any]] = [
    {
        "name": "Anthropic",
        "slug": "anthropic",
        "website_url": "https://www.anthropic.com",
        "description": "AI research and safety company behind the Claude family of models.",
        "aliases": ["claude", "anthropic ai"],
        "plans": [
            {
                "name": "Claude Pro",
                "slug": "claude-pro",
                "description": "5x more usage than Free tier, access to Claude 3.5 Sonnet and Opus.",
                "aliases": ["pro", "claude-3-pro"],
            },
            {
                "name": "Claude Max",
                "slug": "claude-max",
                "description": "High-volume tier for power users and developers.",
                "aliases": ["max", "claude-team"],
            },
        ],
    },
    {
        "name": "OpenAI",
        "slug": "openai",
        "website_url": "https://openai.com",
        "description": "AI research laboratory creator of ChatGPT, GPT-4, and reasoning models.",
        "aliases": ["chatgpt", "openai inc"],
        "plans": [
            {
                "name": "ChatGPT Go",
                "slug": "chatgpt-go",
                "description": "Entry-tier mobile or lightweight ChatGPT subscription.",
                "aliases": ["go"],
            },
            {
                "name": "ChatGPT Plus",
                "slug": "chatgpt-plus",
                "description": "Access to GPT-4o, reasoning models, custom GPTs, and priority capacity.",
                "aliases": ["plus", "gpt-plus"],
            },
            {
                "name": "ChatGPT Pro",
                "slug": "chatgpt-pro",
                "description": "Unlimited access to OpenAI reasoning models and advanced voice mode.",
                "aliases": ["pro", "gpt-pro"],
            },
        ],
    },
    {
        "name": "xAI",
        "slug": "xai",
        "website_url": "https://x.ai",
        "description": "AI startup founded by Elon Musk developing Grok and Colossus supercluster.",
        "aliases": ["grok", "x-ai"],
        "plans": [
            {
                "name": "Grok Premium",
                "slug": "grok-premium",
                "description": "Standard Grok tier bundled with X Premium or standalone.",
                "aliases": ["premium", "x-premium"],
            },
            {
                "name": "SuperGrok",
                "slug": "supergrok",
                "description": "Heavy compute tier with extended context and early feature access.",
                "aliases": ["grok-pro", "super-grok"],
            },
        ],
    },
    {
        "name": "Google",
        "slug": "google",
        "website_url": "https://gemini.google.com",
        "description": "Google AI suite including Gemini, Gemini Advanced, and workspace integration.",
        "aliases": ["gemini", "google deepmind"],
        "plans": [
            {
                "name": "Google AI Pro",
                "slug": "google-ai-pro",
                "description": "Professional tier with Gemini 1.5 Pro and 2M token context window.",
                "aliases": ["ai-pro", "gemini-pro"],
            },
            {
                "name": "Google One AI Premium",
                "slug": "google-one-ai-premium",
                "description": "Gemini Advanced bundled with 2TB cloud storage in Google One.",
                "aliases": ["gemini-advanced", "ai-premium"],
            },
        ],
    },
    {
        "name": "Perplexity",
        "slug": "perplexity",
        "website_url": "https://www.perplexity.ai",
        "description": "Conversational answer engine with multi-source search and reasoning.",
        "aliases": ["perplexity ai", "pplx"],
        "plans": [
            {
                "name": "Perplexity Pro",
                "slug": "perplexity-pro",
                "description": "Unlimited Pro searches, choice of top models (Claude, GPT, Sonar), and file uploads.",
                "aliases": ["pro", "pplx-pro"],
            },
        ],
    },
    {
        "name": "Cursor",
        "slug": "cursor",
        "website_url": "https://www.cursor.com",
        "description": "AI-first code editor built as an intelligent fork of VS Code.",
        "aliases": ["anysphere", "cursor editor"],
        "plans": [
            {
                "name": "Cursor Pro",
                "slug": "cursor-pro",
                "description": "Unlimited fast Claude/GPT completions, background indexing, and Composer access.",
                "aliases": ["pro", "cursor-subscription"],
            },
        ],
    },
    {
        "name": "GitHub",
        "slug": "github",
        "website_url": "https://github.com",
        "description": "World's leading developer platform, providing GitHub Copilot and Copilot Chat.",
        "aliases": ["copilot", "github copilot"],
        "plans": [
            {
                "name": "GitHub Copilot Pro",
                "slug": "github-copilot-pro",
                "description": "Individual developer subscription for Copilot completions, chat, and multi-model support.",
                "aliases": ["copilot-individual", "copilot-pro"],
            },
        ],
    },
]


def seed_database(db: Session) -> Dict[str, int]:
    """
    Seed initial AI providers and plans idempotently.
    Preserves existing records without duplicating.
    """
    providers_created = 0
    plans_created = 0

    for prov_data in SEED_CATALOGUE:
        # Check if provider exists by unique slug
        stmt = select(Provider).where(Provider.slug == prov_data["slug"])
        provider = db.execute(stmt).scalar_one_or_none()

        if not provider:
            provider = Provider(
                name=prov_data["name"],
                slug=prov_data["slug"],
                website_url=prov_data["website_url"],
                description=prov_data["description"],
                aliases=prov_data["aliases"],
                is_active=True,
            )
            db.add(provider)
            db.flush()
            providers_created += 1
            logger.info(f"Created provider: {provider.name} ({provider.slug})")

        # Seed plans for this provider
        for plan_data in prov_data.get("plans", []):
            plan_stmt = select(Plan).where(
                Plan.provider_id == provider.id,
                Plan.slug == plan_data["slug"],
            )
            plan = db.execute(plan_stmt).scalar_one_or_none()

            if not plan:
                plan = Plan(
                    provider_id=provider.id,
                    name=plan_data["name"],
                    slug=plan_data["slug"],
                    description=plan_data["description"],
                    aliases=plan_data["aliases"],
                    is_active=True,
                )
                db.add(plan)
                plans_created += 1
                logger.info(f"Created plan: {plan.name} for {provider.name}")

    db.commit()
    logger.info(
        f"Seeding completed. Providers created: {providers_created}, Plans created: {plans_created}"
    )
    return {
        "providers_created": providers_created,
        "plans_created": plans_created,
    }


def main():
    """CLI entrypoint for running seed script directly."""
    db = SessionLocal()
    try:
        result = seed_database(db)
        print(f"Seed finished: {result}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
