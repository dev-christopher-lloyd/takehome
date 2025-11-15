from typing import List, Generator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.brand import Brand
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_product import CampaignProduct
from app.models.asset import Asset
from app.models.product import Product
from app.schemas.campaign import (
    CampaignBrief,
    CampaignResponse,
    GenerateResponse,
    AssetMetadata,
    CampaignDetail,
    CampaignProductResponse
)
from app.services.storage import generate_presigned_url
from app.services.workflows import run_campaign_generation

router = APIRouter()

def get_db() -> Generator[Session, None, None]:
    """
    Simple DB session dependency for this router.
    Defined here to avoid circular imports with app.main.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignBrief,
    db: Session = Depends(get_db),
) -> CampaignResponse:
    """
    Ingest a campaign brief, validate brand existence, and persist the campaign.
    """
    brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand {payload.brand_id} does not exist",
        )

    # Persist campaign
    campaign = Campaign(
        brand_id=payload.brand_id,
        name=payload.name,
        target_region=payload.target_region,
        target_audience=payload.target_audience,
        campaign_message=payload.campaign_message,
        status=CampaignStatus.DRAFT.value,
    )
    db.add(campaign)
    db.flush()  # obtain campaign.id

    # Create new products and link them via campaign_products
    for product_payload in payload.products:
        new_product = Product(
            name=product_payload.name,
            description=product_payload.description,
            metadata_json=product_payload.metadata_json,
            # NOTE: 'sku' intentionally not used here
        )
        db.add(new_product)
        db.flush()  # obtain new_product.id

        cp = CampaignProduct(
            campaign_id=campaign.id,
            product_id=new_product.id,
        )
        db.add(cp)

    db.commit()
    db.refresh(campaign)

    return CampaignResponse(id=campaign.id, status=CampaignStatus(campaign.status).name)

@router.post("/{campaign_id}/generate", response_model=GenerateResponse)
def generate_campaign_assets(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> GenerateResponse:
    """
    Trigger the creative generation workflow for the given campaign.

    For the POC, this is synchronous:
      - determines missing assets for requested aspect ratios
      - generates / post-processes images
      - uploads to S3
      - runs brand & legal checks
      - persists everything and returns asset metadata
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    # Delegate orchestration to the workflow service
    workflow_result = run_campaign_generation(
        db=db,
        campaign_id=campaign_id,
    )

    assets_metadata: List[AssetMetadata] = []
    for asset in workflow_result.assets:
        s3_url = generate_presigned_url(asset.s3_key)
        assets_metadata.append(
            AssetMetadata(
                id=asset.id,
                product_id=asset.product_id,
                aspect_ratio=asset.aspect_ratio,
                s3_url=s3_url,
                checks=[],  # optional: populate here or via /assets/{id}
            )
        )

    return GenerateResponse(
        workflow_run_id=workflow_result.workflow_run_id,
        assets=assets_metadata,
        errors=workflow_result.errors,
    )

@router.get("/{campaign_id}", response_model=CampaignDetail)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> CampaignDetail:
    """
    Fetch a campaign and its associated assets and products.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    # Fetch assets for this campaign
    assets: List[Asset] = (
        db.query(Asset)
        .filter(Asset.campaign_id == campaign_id)
        .all()
    )

    asset_items: List[AssetMetadata] = []
    for asset in assets:
        asset_items.append(
            AssetMetadata(
                id=asset.id,
                product_id=asset.product_id,
                aspect_ratio=asset.aspect_ratio,
                s3_url=generate_presigned_url(asset.s3_key),
                checks=[],  # or populate from checks table if desired
            )
        )

    # Fetch products linked to this campaign
    products: List[Product] = (
        db.query(Product)
        .join(CampaignProduct, CampaignProduct.product_id == Product.id)
        .filter(CampaignProduct.campaign_id == campaign_id)
        .all()
    )

    product_items: List[CampaignProductResponse] = [
        CampaignProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            metadata_json=p.metadata_json,
        )
        for p in products
    ]

    return CampaignDetail(
        id=campaign.id,
        brand_id=campaign.brand_id,
        name=campaign.name,
        target_region=campaign.target_region,
        target_audience=campaign.target_audience,
        campaign_message=campaign.campaign_message,
        status=CampaignStatus(campaign.status).name,
        assets=asset_items,
        products=product_items,
    )