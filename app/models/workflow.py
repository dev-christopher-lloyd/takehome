from __future__ import annotations
from datetime import datetime
from enum import IntEnum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db import Base


class WorkflowStatus(IntEnum):
  STARTED = 1
  RUNNING = 2
  COMPLETE = 3
  FAILED = 4


class Workflow(Base):
  __tablename__ = "workflows"

  # Columns definition using mapped_column and Mapped
  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  campaign_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
  status: Mapped[WorkflowStatus] = mapped_column(Integer, nullable=False)
  started_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True), default=datetime.utcnow, nullable=False)
  finished_at: Mapped[Optional[datetime]] = mapped_column(
      DateTime(timezone=True), nullable=True)
  error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

  # Relationships
  campaign = relationship("Campaign", back_populates="workflows")

  # Remove started_at and finished_at from __init__ because they are managed by SQLAlchemy
  def __init__(self, campaign_id: int, status: WorkflowStatus = WorkflowStatus.RUNNING):
    self.campaign_id = campaign_id
    self.status = status

  def __repr__(self) -> str:
    return f"<Workflow(id={self.id}, status={self.status}, started_at={self.started_at})>"
