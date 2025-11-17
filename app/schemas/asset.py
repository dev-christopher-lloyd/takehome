from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AssetUploadRequest(BaseModel):
  campaign_id: int = Field(
      ...,
      description="ID of the campaign this asset belongs to.",
  )

  product_id: int = Field(
      ...,
      description="ID of the product this asset is associated with.",
  )

  aspect_ratio: str = Field(
      ...,
      description="Aspect ratio of the image, e.g. 1:1, 9:16, 16:9",
  )

  image_base64: str = Field(
      ...,
      description=(
          "Base64-encoded image data. May optionally include a data URL prefix, "
          "e.g. 'data:image/png;base64,<data>'."
      ),
  )

  content_type: Optional[str] = Field(
      "image/png",
      description="MIME type of the uploaded image (e.g. 'image/png', 'image/jpeg').",
  )


class AssetMetadata(BaseModel):
  id: int

  aspect_ratio: Optional[str] = Field(
      None,
      description=(
          'Aspect ratio string such as "1:1", "9:16", "16:9" '
          "(may be null for some asset types)."
      ),
  )

  s3_url: str

  checks: List[Dict[str, Any]] = Field(
      default_factory=list,
      description="List of check results (brand, legal, etc.) for this asset.",
  )
