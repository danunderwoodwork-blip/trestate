"""Эвристика дубликатов: один объект от владельца и двух агентств."""
import asyncio

from sqlalchemy import select

from app.ingestion.pipeline import sync_source
from app.models import Listing, Source
from app.services.dedup import find_duplicates, group_duplicates, similarity
from tests.fake_source import FakeSource, make_record


def test_same_flat_from_owner_and_agencies_grouped(db):
    src = Source(code="fake", name="Fake", adapter="tests.fake_source:FakeSource")
    db.add(src)
    db.commit()

    records = {
        "owner": make_record("owner", price="5650000", title="Mahmutlar satilik 2+1 havuzlu site"),
        "agency_a": make_record("agency_a", price="5900000", title="Mahmutlar 2+1 havuzlu site daire"),
        "agency_b": make_record("agency_b", price="6100000", title="Satilik 2+1 Mahmutlar havuzlu"),
        "other": make_record("other", price="9500000", rooms="4+1", net_m2="190", gross_m2="210",
                              floor="1", title="Genis aile dairesi deniz manzarali"),
    }
    asyncio.run(sync_source(db, src, adapter=FakeSource(records)))

    owner = db.scalar(select(Listing).where(Listing.external_id == "owner"))
    other = db.scalar(select(Listing).where(Listing.external_id == "other"))

    dups = find_duplicates(db, owner)
    assert {d.external_id for d in dups} == {"agency_a", "agency_b"}
    assert similarity(owner, other) < 0.8

    group_duplicates(db, owner, dups)
    db.commit()
    ids = {
        l.duplicate_group_id
        for l in db.scalars(select(Listing).where(Listing.external_id != "other"))
    }
    assert len(ids) == 1 and None not in ids
    db.refresh(other)
    assert other.duplicate_group_id is None
