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
  from app.models.campaign import Campaign
  from app.models.product import Product
  from app.models.brand import Brand


class AssetType(IntEnum):
  LOGO = 1
  PRODUCT = 2
  CREATIVE = 3


class AssetSource(IntEnum):
  UPLOADED = 1
  GENERATED = 2


class Asset(Base):
  __tablename__ = "assets"

  id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      index=True,
  )

  brand_id: Mapped[Optional[int]] = mapped_column(
      Integer,
      ForeignKey("brands.id", ondelete="CASCADE"),
      nullable=True,
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

  source: Mapped[int] = mapped_column(
      Integer,
      nullable=False,
      index=True,
  )

  gen_metadata_json: Mapped[Optional[dict]] = mapped_column(
      JSONB,
      nullable=True,
  )

  created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      server_default=func.now(),
      nullable=False,
  )

  brand: Mapped[Optional["Brand"]] = relationship(
      back_populates="assets",
  )

  campaign: Mapped[Optional["Campaign"]] = relationship(
      back_populates="assets",
  )

  product: Mapped[Optional["Product"]] = relationship(
      back_populates="assets",
  )

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
