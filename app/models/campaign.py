from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
  from app.models.brand import Brand
  from app.models.asset import Asset
  from app.models.campaign_product import CampaignProduct
  from app.models.workflow import Workflow


class CampaignStatus(IntEnum):
  DRAFT = 1
  GENERATED = 2
  FAILED = 3


class Campaign(Base):
  __tablename__ = "campaigns"

  id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      index=True,
  )

  brand_id: Mapped[int] = mapped_column(
      Integer,
      ForeignKey("brands.id", ondelete="CASCADE"),
      index=True,
      nullable=False,
  )

  name: Mapped[str] = mapped_column(
      String(255),
      nullable=False,
  )

  target_region: Mapped[str] = mapped_column(
      String(64),
      nullable=False,
  )

  target_audience: Mapped[str] = mapped_column(
      String(255),
      nullable=False,
  )

  campaign_message: Mapped[str] = mapped_column(
      Text,
      nullable=False,
  )

  localized_campaign_message: Mapped[str] = mapped_column(
      Text,
      nullable=True,
  )

  status: Mapped[str] = mapped_column(
      Integer,
      nullable=False,
      default=CampaignStatus.DRAFT.value,
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

  brand: Mapped["Brand"] = relationship(
      "Brand",
      back_populates="campaigns",
  )

  assets: Mapped[List["Asset"]] = relationship(
      "Asset",
      back_populates="campaign",
      cascade="all, delete-orphan",
  )

  campaign_products: Mapped[List["CampaignProduct"]] = relationship(
      "CampaignProduct",
      back_populates="campaign",
      cascade="all, delete-orphan",
  )

  workflows: Mapped[List["Workflow"]] = relationship(
      "Workflow",
      back_populates="campaign",
      cascade="all, delete-orphan",
  )
