"""Automated integration tests for Phase 5 Backend API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.enums import OfferType, PromotionStatus
from app.database.models.promotion import Promotion
from app.database.models.provider import Provider


def test_dashboard_stats_and_activity(client: TestClient, db_session: Session):
    # 1. Test GET /dashboard/stats
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert "total_discovered_items" in data
    assert "total_promotions" in data
    assert "verified_promotions" in data
    assert "nigeria_eligible_promotions" in data
    assert "providers" in data
    assert isinstance(data["providers"], list)
    assert len(data["providers"]) >= 7  # All 7 seeded providers
    assert "offer_type_distribution" in data
    assert "recent_discoveries" in data

    # 2. Test GET /dashboard/activity
    act_resp = client.get("/api/v1/dashboard/activity?limit=5")
    assert act_resp.status_code == 200
    act_data = act_resp.json()
    assert isinstance(act_data, list)


def test_providers_endpoints(client: TestClient, db_session: Session):
    # 1. Test GET /providers
    resp = client.get("/api/v1/providers")
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 7

    # Check structure of first provider
    first = providers[0]
    assert "id" in first
    assert "name" in first
    assert "slug" in first
    assert "plans" in first
    assert isinstance(first["plans"], list)

    # 2. Test GET /providers/{id}
    prov_id = first["id"]
    single_resp = client.get(f"/api/v1/providers/{prov_id}")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["id"] == prov_id
    assert single_data["slug"] == first["slug"]

    # 3. Test 404 on non-existent provider
    bad_resp = client.get("/api/v1/providers/999999")
    assert bad_resp.status_code == 404


def test_watchlist_workflow(client: TestClient, db_session: Session):
    provider = db_session.query(Provider).first()
    assert provider is not None

    # Create a test promotion
    promo = Promotion(
        provider_id=provider.id,
        title="Test Watchlist Deal",
        offer_type=OfferType.DISCOUNT,
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        account_requirements={},
        confidence_score=85,
        status=PromotionStatus.VERIFIED,
    )
    db_session.add(promo)
    db_session.commit()
    db_session.refresh(promo)

    # 1. Initial watchlist should be clean or valid
    get_resp = client.get("/api/v1/watchlist")
    assert get_resp.status_code == 200
    initial_wl = get_resp.json()
    assert "promotion_ids" in initial_wl

    # 2. Add promotion to watchlist (toggle on)
    toggle_resp = client.post(f"/api/v1/watchlist/promotions/{promo.id}")
    assert toggle_resp.status_code == 200
    wl_after_add = toggle_resp.json()
    assert promo.id in wl_after_add["promotion_ids"]

    # 3. Fetch items in watchlist
    items_resp = client.get("/api/v1/watchlist/items")
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert any(item["id"] == promo.id for item in items)

    # 4. Watch provider
    watch_prov = client.post(f"/api/v1/watchlist/providers/{provider.id}")
    assert watch_prov.status_code == 200
    assert provider.id in watch_prov.json()["provider_ids"]

    # 5. Remove promotion from watchlist
    del_resp = client.delete(f"/api/v1/watchlist/promotions/{promo.id}")
    assert del_resp.status_code == 200
    assert promo.id not in del_resp.json()["promotion_ids"]


def test_settings_endpoints(client: TestClient, db_session: Session):
    # 1. Get settings
    get_resp = client.get("/api/v1/settings")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert "min_confidence_score" in data
    assert "telegram_notifications_enabled" in data
    assert "nigeria_only_filter" in data

    # 2. Patch settings
    patch_resp = client.patch(
        "/api/v1/settings",
        json={
            "min_confidence_score": 80,
            "nigeria_only_filter": True,
            "telegram_notifications_enabled": False,
        },
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["min_confidence_score"] == 80
    assert updated["nigeria_only_filter"] is True
    assert updated["telegram_notifications_enabled"] is False

    # 3. Verify changes persist
    verify_resp = client.get("/api/v1/settings")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["min_confidence_score"] == 80
