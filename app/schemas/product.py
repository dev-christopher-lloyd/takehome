from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
  """
  Incoming payload for creating (or updating) a product.

  Example:
  {
    "name": "Pro-Series Hockey Stick",
    "description": "Lightweight carbon-fiber stick designed for elite puck handling and powerful slapshots.",
    "metadata_json": {
      "sku": "HKY-STK-PRO",
      "category": "equipment",
      "curve": "P92",
      "flex": 85,
      "position": "forward"
    }
  }
  """

  name: str = Field(
      ...,
      description="Human-readable product name",
  )

  description: Optional[str] = Field(
      None,
      description="Optional human-readable description of the product",
  )

  metadata_json: Optional[Dict[str, Any]] = Field(
      None,
      description="Optional free-form JSON metadata associated with the product",
  )


class ProductResponse(BaseModel):
  id: int
  name: str
  description: Optional[str] = None
  metadata_json: Optional[Dict[str, Any]] = None
  created_at: datetime
  updated_at: datetime

  model_config = ConfigDict(from_attributes=True)
