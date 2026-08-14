"""Сквозной тест ingestion: новые объекты, инкрементальность, история цен, lifecycle."""
import asyncio

from sqlalchemy import select

from app.ingestion.pipeline import sync_source
from app.models import Listing, ListingHistory, Source
from tests.fake_source import FakeSource, make_record


def _make_source(db) -> Source:
    src = Source(code="fake", name="Fake", adapter="tests.fake_source:FakeSource")
    db.add(src)
    db.commit()
    return src


def _sync(db, src, records):
    adapter = FakeSource(records)
    stats = asyncio.run(sync_source(db, src, adapter=adapter))
    return stats, adapter


def test_first_sync_creates_listings_with_history(db):
    src = _make_source(db)
    stats, _ = _sync(db, src, {"1": make_record("1"), "2": make_record("2", price="3200000")})

    assert stats.new == 2
    listings = db.scalars(select(Listing)).all()
    assert len(listings) == 2
    l1 = next(l for l in listings if l.external_id == "1")
    assert l1.status == "active"
    assert float(l1.price) == 5500000
    assert float(l1.price_per_gross_m2) == 45833.33
    assert float(l1.price_per_net_m2) == 52380.95
    assert l1.neighbourhood.name == "Mahmutlar"
    assert l1.district.slug == "antalya-alanya"
    assert len(l1.history) == 1  # первичное наблюдение


def test_incremental_only_fetches_new_and_changed(db):
    src = _make_source(db)
    records = {"1": make_record("1"), "2": make_record("2")}
    _sync(db, src, records)

    # день 2: '1' не менялось, '2' подешевело, '3' новое
    records2 = {
        "1": make_record("1"),
        "2": make_record("2", price="5200000"),
        "3": make_record("3"),
    }
    stats, adapter = _sync(db, src, records2)

    assert stats.new == 1
    assert stats.updated == 1
    assert stats.unchanged == 1
    # полная загрузка была только для нового и изменённого
    assert sorted(adapter.full_fetches) == ["2", "3"]

    l2 = db.scalar(select(Listing).where(Listing.external_id == "2"))
    assert float(l2.price) == 5200000
    history = l2.history
    assert len(history) == 2
    assert [float(h.price) for h in history] == [5500000, 5200000]
    assert "price" in history[-1].changed_fields


def test_disappearance_confirmed_before_inactive(db):
    src = _make_source(db)
    _sync(db, src, {"1": make_record("1"), "2": make_record("2")})

    # '2' исчезло из индекса — ещё не inactive
    stats, _ = _sync(db, src, {"1": make_record("1")})
    l2 = db.scalar(select(Listing).where(Listing.external_id == "2"))
    assert l2.status == "possibly_inactive"
    assert l2.miss_count == 1
    assert stats.status_changes.get("possibly_inactive") == 1

    # исчезло второй раз подряд — подтверждено
    _sync(db, src, {"1": make_record("1")})
    db.refresh(l2)
    assert l2.status == "inactive"

    # объявление вернулось — реактивация
    _sync(db, src, {"1": make_record("1"), "2": make_record("2")})
    db.refresh(l2)
    assert l2.status == "active"
    assert l2.miss_count == 0


def test_price_drop_analytics(db):
    from app.services.listings import build_price_info

    src = _make_source(db)
    _sync(db, src, {"1": make_record("1", price="6200000")})
    _sync(db, src, {"1": make_record("1", price="5950000")})
    _sync(db, src, {"1": make_record("1", price="5550000")})

    l1 = db.scalar(select(Listing).where(Listing.external_id == "1"))
    info = build_price_info(db, l1)
    assert info.initial_price == 6200000
    assert info.current_price == 5550000
    assert info.change_abs == -650000
    assert info.change_pct == -10.48
    assert info.price_changes_count == 2
