from enum import IntEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class LegalRuleType(IntEnum):
    BANNED_PHRASE = 1
    MANDATORY_PHRASE = 2


class LegalRuleSeverity(IntEnum):
    WARN = 1
    BLOCK = 2


class LegalRule(Base):
    __tablename__ = "legal_rules"

    id = Column(Integer, primary_key=True, index=True)

    # NULL => global rule (applies to all brands)
    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Stored as Integer in DB, use LegalRuleType IntEnum in code
    rule_type = Column(Integer, nullable=False, index=True)

    # String / regex pattern
    pattern = Column(Text, nullable=False)

    description = Column(Text, nullable=True)

    # Stored as Integer in DB, use LegalRuleSeverity IntEnum in code
    severity = Column(Integer, nullable=False)

    # Relationships
    brand = relationship("Brand", backref="legal_rules")

    # ---- Convenience enum accessors (optional but nice) ----

    @property
    def rule_type_enum(self) -> LegalRuleType:
        return LegalRuleType(self.rule_type)

    @rule_type_enum.setter
    def rule_type_enum(self, value: LegalRuleType) -> None:
        self.rule_type = int(value)

    @property
    def severity_enum(self) -> LegalRuleSeverity:
        return LegalRuleSeverity(self.severity)

    @severity_enum.setter
    def severity_enum(self, value: LegalRuleSeverity) -> None:
        self.severity = int(value)
