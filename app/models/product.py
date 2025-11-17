from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
  from app.models.campaign_product import CampaignProduct
  from app.models.asset import Asset


class Product(Base):
  __tablename__ = "products"

  id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      index=True,
  )

  name: Mapped[str] = mapped_column(
      String(255),
      nullable=False,
  )

  description: Mapped[str | None] = mapped_column(
      Text,
      nullable=True,
  )

  metadata_json: Mapped[dict | None] = mapped_column(
      JSONB,
      nullable=True,
  )

  created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      server_default=func.now(),
      nullable=False,
  )

  updated_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      server_default=func.now(),
      onupdate=func.now(),
      nullable=False,
  )

  campaign_products: Mapped[List["CampaignProduct"]] = relationship(
      "CampaignProduct",
      back_populates="product",
      cascade="all, delete-orphan",
  )

  assets: Mapped[List["Asset"]] = relationship(
      "Asset",
      back_populates="product",
      cascade="all, delete-orphan",
  )
