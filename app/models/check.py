from enum import IntEnum

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.db import Base


class CheckType(IntEnum):
    BRAND = 1
    LEGAL = 2
    # extend as needed, keep integer mappings stable


class CheckResult(IntEnum):
    PASS = 1
    FAIL = 2
    WARN = 3
    # extend as needed, keep integer mappings stable


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)

    workflow_run_id = Column(
        Integer,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asset_id = Column(
        Integer,
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stored as Integer in DB; use CheckType in code
    check_type = Column(Integer, nullable=False, index=True)

    # Stored as Integer in DB; use CheckResult in code
    result = Column(Integer, nullable=False, index=True)

    details_json = Column(JSONB, nullable=True)  # e.g. what rule failed

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    workflow_run = relationship("WorkflowRun", backref="checks")
    asset = relationship("Asset", backref="checks")

    # --- Convenience enum accessors ---

    @property
    def check_type_enum(self) -> CheckType:
        return CheckType(self.check_type)

    @check_type_enum.setter
    def check_type_enum(self, value: CheckType) -> None:
        self.check_type = int(value)

    @property
    def result_enum(self) -> CheckResult:
        return CheckResult(self.result)

    @result_enum.setter
    def result_enum(self, value: CheckResult) -> None:
        self.result = int(value)
