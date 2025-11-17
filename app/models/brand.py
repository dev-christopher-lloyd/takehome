from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
  from app.models.campaign import Campaign
  from app.models.asset import Asset


class Brand(Base):
  __tablename__ = "brands"

  id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      index=True,
  )

  name: Mapped[str] = mapped_column(
      String(255),
      nullable=False,
  )

  primary_color_hex: Mapped[str] = mapped_column(
      String(7),
      nullable=False,
  )

  secondary_color_hex: Mapped[str | None] = mapped_column(
      String(7),
      nullable=True,
  )

  tone_of_voice: Mapped[str | None] = mapped_column(
      Text,
      nullable=True,
  )

  font_family: Mapped[str | None] = mapped_column(
      String(128),
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

  campaigns: Mapped[List["Campaign"]] = relationship(
      "Campaign",
      back_populates="brand",
      cascade="all, delete-orphan",
      passive_deletes=True,
  )

  assets: Mapped[List["Asset"]] = relationship(
      "Asset",
      back_populates="brand",
      cascade="all, delete-orphan",
  )
