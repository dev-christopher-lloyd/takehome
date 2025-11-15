from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from .asset import AssetMetadata
from .product import ProductCreate

class CampaignBrief(BaseModel):
    """
    Incoming campaign brief payload.

    Example:
    {
      "brand_id": 1,
      "name": "Winter Classic 2025",
      "products": [
        {
          "name": "Pro-Series Hockey Stick",
          "description": "Elite carbon-fiber stick for fast shots",
          "metadata_json": { "curve": "P92", "flex": 85 }
        },
        {
          "name": "Team Hoodie",
          "description": "Warm performance hoodie for cold arenas",
          "metadata_json": { "size": "L", "color": "navy" }
        }
      ],
      "target_region": "US",
      "target_audience": "Hockey players and fans ages 16-30",
      "campaign_message": "Gear up for the ice — dominate every shift!"
    }
    """

    brand_id: int
    name: str
    products: List[ProductCreate]
    target_region: str
    target_audience: str
    campaign_message: str


class CampaignResponse(BaseModel):
    """
    Simple response after creating a campaign.
    """

    id: int
    status: str


class GenerateRequest(BaseModel):
    """
    Request body for POST /campaigns/{campaign_id}/generate.
    """
    pass


class GenerateResponse(BaseModel):
    """
    Response for a synchronous generation run.

    Contains a workflow_run_id for traceability, the generated asset metadata
    (with S3 URLs), and any non-fatal errors/warnings.
    """

    workflow_run_id: int
    assets: List[AssetMetadata]
    errors: Optional[List[str]] = None

class CampaignProductResponse(BaseModel):
    """
    Lightweight product view attached to a campaign.
    """

    id: int
    name: str
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class CampaignDetail(BaseModel):
    """
    Detailed view of a single campaign including assets and products.
    """

    id: int
    brand_id: int
    name: str
    target_region: str
    target_audience: str
    campaign_message: str
    status: str
    assets: List[AssetMetadata]
    products: List[CampaignProductResponse]