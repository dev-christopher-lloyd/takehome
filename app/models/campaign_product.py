from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
  from app.models.campaign import Campaign
  from app.models.product import Product


class CampaignProduct(Base):
  __tablename__ = "campaign_products"

  campaign_id: Mapped[int] = mapped_column(
      Integer,
      ForeignKey("campaigns.id", ondelete="CASCADE"),
      primary_key=True,
      index=True,
  )

  product_id: Mapped[int] = mapped_column(
      Integer,
      ForeignKey("products.id", ondelete="CASCADE"),
      primary_key=True,
      index=True,
  )

  campaign: Mapped["Campaign"] = relationship(
      "Campaign",
      back_populates="campaign_products",
  )

  product: Mapped["Product"] = relationship(
      "Product",
      back_populates="campaign_products",
  )
