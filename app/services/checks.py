from typing import List
from app.models.asset import Asset
from app.models.brand import Brand
from app.models.campaign import Campaign


class CheckResult:
  def __init__(self, check_type: str, result: str, details: dict = {}):
    self.check_type = check_type
    self.result = result
    self.details = details or {}

  def __repr__(self) -> str:
    return f"CheckResult(check_type={self.check_type}, result={self.result})"


def run_brand_checks(asset: Asset, brand: Brand, img) -> List[CheckResult]:
  checks: List[CheckResult] = []

  # TODO: think of some brand checks

  return checks


def run_legal_checks(campaign: Campaign, brand: Brand) -> List[CheckResult]:
  checks: List[CheckResult] = []

  # TODO: think of some legal checks

  return checks
