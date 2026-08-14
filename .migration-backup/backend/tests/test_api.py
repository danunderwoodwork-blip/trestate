"""Тесты REST API: поиск/фильтры, карточка, история, избранное."""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.ingestion.pipeline import sync_source
from app.main import app
from app.models import Source
from tests.fake_source import FakeSource, make_record


@pytest.fixture
def client(db):
    src = Source(code="fake", name="Fake", adapter="tests.fake_source:FakeSource")
    db.add(src)
    db.commit()
    records = {
        "1": make_record("1"),  # Mahmutlar 2+1, 5.5M
        "2": make_record("2", price="8900000", rooms="3+1", neighbourhood="Oba",
                          title="Oba 3+1 deniz manzarali"),
        "3": make_record("3", price="3200000", rooms="1+1", neighbourhood="Kestel",
                          transaction_type="Kiralık", title="Kestel kiralik 1+1"),
    }
    asyncio.run(sync_source(db, src, adapter=FakeSource(records)))
    # снижение цены для объявления '1'
    records["1"] = make_record("1", price="5200000")
    asyncio.run(sync_source(db, src, adapter=FakeSource(records)))
    return TestClient(app)


def test_search_filters(client):
    resp = client.get("/api/listings", params={"province": "antalya", "rooms": ["2+1"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["rooms"] == "2+1"
    assert data["items"][0]["neighbourhood"]["name"] == "Mahmutlar"

    resp = client.get("/api/listings", params={"transaction_type": "rent_long"})
    assert resp.json()["total"] == 1

    resp = client.get("/api/listings", params={"max_price": 4000000})
    assert resp.json()["total"] == 1

    resp = client.get("/api/listings", params={"only_price_drops": "true"})
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["id"] is not None

    resp = client.get("/api/listings", params={"q": "deniz manzarali"})
    assert resp.json()["total"] == 1


def test_detail_with_price_info_and_freshness(client):
    listing_id = client.get("/api/listings", params={"rooms": ["2+1"]}).json()["items"][0]["id"]
    resp = client.get(f"/api/listings/{listing_id}")
    assert resp.status_code == 200
    d = resp.json()
    assert d["source_code"] == "fake"
    assert d["price_info"]["initial_price"] == 5500000
    assert d["price_info"]["current_price"] == 5200000
    assert d["price_info"]["change_pct"] == -5.45
    assert d["price_info"]["price_changes_count"] == 1
    assert d["freshness"]["status"] == "active"
    assert d["freshness"]["last_checked_at"] is not None
    assert d["price_per_gross_m2"] is not None


def test_history_endpoint(client):
    listing_id = client.get("/api/listings", params={"rooms": ["2+1"]}).json()["items"][0]["id"]
    resp = client.get(f"/api/listings/{listing_id}/history")
    prices = [h["price"] for h in resp.json()]
    assert prices == [5500000, 5200000]


def test_map_endpoint(client):
    resp = client.get("/api/map", params={"min_lat": 36, "max_lat": 37})
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_favorites_flow(client):
    listing_id = client.get("/api/listings").json()["items"][0]["id"]
    headers = {"X-Device-Id": "test-device-1"}

    assert client.post("/api/favorites", json={"listing_id": listing_id}, headers=headers).status_code == 201
    favs = client.get("/api/favorites", headers=headers).json()
    assert [f["id"] for f in favs] == [listing_id]

    assert client.delete(f"/api/favorites/{listing_id}", headers=headers).status_code == 204
    assert client.get("/api/favorites", headers=headers).json() == []

    # без X-Device-Id — 401
    assert client.get("/api/favorites").status_code == 401


def test_locations_and_meta(client):
    tree = client.get("/api/locations").json()
    assert tree[0]["name"] == "Turkey"
    provinces = tree[0]["children"]
    assert provinces[0]["name"] == "Antalya"
    assert provinces[0]["children"][0]["name"] == "Alanya"

    meta = client.get("/api/meta").json()
    assert "sale" in meta["transaction_types"]
