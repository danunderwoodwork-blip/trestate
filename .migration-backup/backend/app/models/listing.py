from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONVariant


class ListingStatus:
    ACTIVE = "active"
    POSSIBLY_INACTIVE = "possibly_inactive"
    INACTIVE = "inactive"


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        sa.UniqueConstraint("source_id", "external_id", name="uq_listing_source_external"),
        sa.Index("ix_listings_search", "status", "transaction_type", "property_type"),
        sa.Index("ix_listings_geo", "province_id", "district_id", "neighbourhood_id"),
        sa.Index("ix_listings_price", "price"),
        sa.Index("ix_listings_next_check", "next_check_at"),
    )

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)

    # --- происхождение ---
    source_id: Mapped[int] = mapped_column(sa.ForeignKey("sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(sa.String(128))
    original_url: Mapped[str | None] = mapped_column(sa.String(1024))  # только метаданные происхождения

    # --- классификация ---
    transaction_type: Mapped[str] = mapped_column(sa.String(16))  # sale|rent_long|rent_short
    property_type: Mapped[str] = mapped_column(sa.String(24))     # apartment|house|villa|commercial|land

    # --- контент ---
    title: Mapped[str | None] = mapped_column(sa.String(512))
    description: Mapped[str | None] = mapped_column(sa.Text)

    # --- цена ---
    price: Mapped[float | None] = mapped_column(sa.Numeric(14, 2))
    currency: Mapped[str] = mapped_column(sa.String(3), default="TRY")
    price_per_gross_m2: Mapped[float | None] = mapped_column(sa.Numeric(14, 2))
    price_per_net_m2: Mapped[float | None] = mapped_column(sa.Numeric(14, 2))

    # --- параметры объекта ---
    gross_area_m2: Mapped[float | None] = mapped_column(sa.Numeric(8, 1))
    net_area_m2: Mapped[float | None] = mapped_column(sa.Numeric(8, 1))
    rooms: Mapped[str | None] = mapped_column(sa.String(8))  # "2+1"
    bedrooms: Mapped[int | None] = mapped_column()
    bathrooms: Mapped[int | None] = mapped_column()
    building_age: Mapped[int | None] = mapped_column()
    floor: Mapped[int | None] = mapped_column()
    total_floors: Mapped[int | None] = mapped_column()
    heating: Mapped[str | None] = mapped_column(sa.String(32))
    furnished: Mapped[bool | None] = mapped_column()
    balcony: Mapped[bool | None] = mapped_column()
    elevator: Mapped[bool | None] = mapped_column()
    parking: Mapped[bool | None] = mapped_column()
    pool: Mapped[bool | None] = mapped_column()
    residential_complex: Mapped[str | None] = mapped_column(sa.String(255))
    deed_status: Mapped[str | None] = mapped_column(sa.String(64))
    distance_to_sea_m: Mapped[int | None] = mapped_column()

    # --- география ---
    province_id: Mapped[int | None] = mapped_column(sa.ForeignKey("locations.id"))
    district_id: Mapped[int | None] = mapped_column(sa.ForeignKey("locations.id"))
    neighbourhood_id: Mapped[int | None] = mapped_column(sa.ForeignKey("locations.id"))
    address_text: Mapped[str | None] = mapped_column(sa.String(512))
    latitude: Mapped[float | None] = mapped_column()
    longitude: Mapped[float | None] = mapped_column()

    # --- продавец ---
    seller_type: Mapped[str | None] = mapped_column(sa.String(16))  # owner|agency|developer
    agency_name: Mapped[str | None] = mapped_column(sa.String(255))

    # --- временные метки / lifecycle ---
    publication_date: Mapped[date | None] = mapped_column()
    source_updated_at: Mapped[datetime | None] = mapped_column()
    first_seen_at: Mapped[datetime] = mapped_column()
    last_seen_at: Mapped[datetime] = mapped_column()
    last_checked_at: Mapped[datetime] = mapped_column()
    next_check_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(sa.String(20), default=ListingStatus.ACTIVE)
    miss_count: Mapped[int] = mapped_column(default=0)

    # hash ключевых полей нормализованной записи — быстрый detect изменений
    fingerprint: Mapped[str | None] = mapped_column(sa.String(64))

    duplicate_group_id: Mapped[int | None] = mapped_column(sa.ForeignKey("duplicate_groups.id"), index=True)

    raw_data: Mapped[dict | None] = mapped_column(JSONVariant)

    source: Mapped["Source"] = relationship()  # noqa: F821
    province: Mapped["Location | None"] = relationship(foreign_keys=[province_id])  # noqa: F821
    district: Mapped["Location | None"] = relationship(foreign_keys=[district_id])  # noqa: F821
    neighbourhood: Mapped["Location | None"] = relationship(foreign_keys=[neighbourhood_id])  # noqa: F821
    history: Mapped[list["ListingHistory"]] = relationship(
        back_populates="listing", order_by="ListingHistory.observed_at", cascade="all, delete-orphan"
    )
    images: Mapped[list["ListingImage"]] = relationship(
        back_populates="listing", order_by="ListingImage.position", cascade="all, delete-orphan"
    )
    features: Mapped[list["ListingFeature"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )


class ListingHistory(Base):
    """Наблюдения ключевых полей во времени. Пишется при появлении и при каждом изменении."""

    __tablename__ = "listing_history"

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        sa.ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    observed_at: Mapped[datetime] = mapped_column(index=True)
    price: Mapped[float | None] = mapped_column(sa.Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(sa.String(3))
    status: Mapped[str | None] = mapped_column(sa.String(20))
    gross_area_m2: Mapped[float | None] = mapped_column(sa.Numeric(8, 1))
    net_area_m2: Mapped[float | None] = mapped_column(sa.Numeric(8, 1))
    changed_fields: Mapped[dict | None] = mapped_column(JSONVariant)

    listing: Mapped[Listing] = relationship(back_populates="history")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        sa.ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(default=0)
    storage: Mapped[str] = mapped_column(sa.String(16), default="remote_url")  # local_s3|remote_url|feed
    url: Mapped[str] = mapped_column(sa.String(1024))  # URL либо ключ в object storage
    phash: Mapped[str | None] = mapped_column(sa.String(64))  # perceptual hash (для дедупликации, позже)
    meta: Mapped[dict | None] = mapped_column(JSONVariant)

    listing: Mapped[Listing] = relationship(back_populates="images")


class ListingFeature(Base):
    """Произвольные характеристики, не попавшие в нормализованные колонки."""

    __tablename__ = "listing_features"
    __table_args__ = (sa.UniqueConstraint("listing_id", "name"),)

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        sa.ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(sa.String(64))
    value: Mapped[str | None] = mapped_column(sa.String(255))

    listing: Mapped[Listing] = relationship(back_populates="features")


class DuplicateGroup(Base):
    """Группа объявлений, предположительно описывающих один физический объект."""

    __tablename__ = "duplicate_groups"

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column()
    match_basis: Mapped[str] = mapped_column(sa.String(64), default="geo+area+rooms+price")
