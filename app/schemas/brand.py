from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from .asset import AssetMetadata


class BrandCreate(BaseModel):
  """
  Incoming payload for creating (or updating) a brand.

  Example:
  {
      "name": "Northern Blades Hockey Co.",
      "primary_color_hex": "#0033cc",
      "secondary_color_hex": "#ffffff",
      "tone_of_voice": "Bold, competitive, team-driven",
      "font_family": "Roboto Slab"
  }
  """

  name: str = Field(..., description="Human-readable brand name")
  primary_color_hex: str = Field(
      ...,
      description="Primary brand color in hex format, e.g. '#0e9fd6'",
      pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
  )
  secondary_color_hex: Optional[str] = Field(
      None,
      description="Optional secondary brand color in hex format, e.g. '#ff9900'",
      pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
  )
  tone_of_voice: Optional[str] = Field(
      None,
      description="Free-form description of the brand's tone of voice "
      "(e.g. 'fun, quirky, outgoing')",
  )
  font_family: Optional[str] = Field(
      None,
      description="Preferred brand font family name (e.g. 'Inter', 'Helvetica Neue')",
  )


class BrandResponse(BaseModel):
  id: int
  name: str
  primary_color_hex: str
  secondary_color_hex: Optional[str] = None
  tone_of_voice: Optional[str] = None
  font_family: Optional[str] = None
  assets: List[AssetMetadata]

  model_config = ConfigDict(from_attributes=True)
