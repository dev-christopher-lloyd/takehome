# app/models/brand_rule.py

from enum import IntEnum

from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.db import Base


class BrandRuleType(IntEnum):
    LOGO_REQUIRED = 1
    COLOR_REQUIRED = 2


class BrandRuleSeverity(IntEnum):
    WARN = 1
    BLOCK = 2


class BrandRule(Base):
    __tablename__ = "brand_rules"

    id = Column(Integer, primary_key=True, index=True)

    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stored as Integer in DB, mapped via BrandRuleType IntEnum
    rule_type = Column(Integer, nullable=False, index=True)

    # Arbitrary configuration for the rule
    config_json = Column(JSONB, nullable=True)

    # Stored as Integer in DB, mapped via BrandRuleSeverity IntEnum
    severity = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    brand = relationship("Brand", back_populates="rules")

    # Convenience properties (optional, but handy)

    @property
    def rule_type_enum(self) -> BrandRuleType:
        return BrandRuleType(self.rule_type)

    @rule_type_enum.setter
    def rule_type_enum(self, value: BrandRuleType) -> None:
        self.rule_type = int(value)

    @property
    def severity_enum(self) -> BrandRuleSeverity:
        return BrandRuleSeverity(self.severity)

    @severity_enum.setter
    def severity_enum(self, value: BrandRuleSeverity) -> None:
        self.severity = int(value)
