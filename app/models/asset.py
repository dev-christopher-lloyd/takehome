from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    # Only imported for type checking; avoids circular imports at runtime
    from app.models.campaign import Campaign
    from app.models.product import Product


class AssetType(IntEnum):
    LOGO = 1
    PRODUCT = 2
    CREATIVE = 3
    # add more types as needed (keep integer values stable)


class AssetSource(IntEnum):
    UPLOADED = 1
    GENERATED = 2
    # extend as needed, keep integer mapping stable


class Asset(Base):
    __tablename__ = "assets"

    # --- Columns -------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    campaign_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Stored as Integer in DB; use AssetType in code via helpers below
    type: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    aspect_ratio: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,  # e.g. "1:1", "9:16", "16:9"
    )

    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    s3_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Stored as Integer in DB; use AssetSource in code via helpers below
    source: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    gen_metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,  # prompt, model, seed, etc.
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships -------------------------------------------------------

    campaign: Mapped[Optional["Campaign"]] = relationship(
        back_populates="assets",
    )

    product: Mapped[Optional["Product"]] = relationship(
        back_populates="assets",
    )

    # --- Convenience enum accessors -----------------------------------------

    @property
    def type_enum(self) -> AssetType:
        return AssetType(self.type)

    @type_enum.setter
    def type_enum(self, value: AssetType) -> None:
        self.type = int(value)

    @property
    def source_enum(self) -> AssetSource:
        return AssetSource(self.source)

    @source_enum.setter
    def source_enum(self, value: AssetSource) -> None:
        self.source = int(value)
