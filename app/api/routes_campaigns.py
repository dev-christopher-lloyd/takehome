from typing import List
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy.exc import SQLAlchemyError
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.campaign_product import CampaignProduct
from app.models.asset import Asset
from app.models.product import Product
from app.models.workflow import Workflow, WorkflowStatus
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
from app.services.download import create_zip
from app.core.db import DbSession

router = APIRouter()


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignBrief,
    db: DbSession,
) -> CampaignResponse:
  brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
  if not brand:
    raise HTTPException(
        status_code=status.HTTP_404_BAD_REQUEST,
        detail=f"Brand {payload.brand_id} does not exist",
    )
  
  # make this a transaction
  try:
    # Persist campaign
    campaign = Campaign(
        brand_id=payload.brand_id,
        name=payload.name,
        target_region=payload.target_region,
        target_audience=payload.target_audience,
        campaign_message=payload.campaign_message,
    )
    db.add(campaign)
    db.flush()

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
  except SQLAlchemyError:
      db.rollback()
      raise

  db.refresh(campaign)

  return CampaignResponse(id=campaign.id)


@router.post("/{campaign_id}/generate", response_model=GenerateResponse)
def generate_campaign_assets(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> GenerateResponse:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    workflow_run = Workflow(
        campaign_id=campaign.id,
        status=WorkflowStatus.STARTED,
    )

    try:
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
    except Exception:
        db.rollback()
        raise

    background_tasks.add_task(run_campaign_generation, workflow_run.id, campaign_id)

    return GenerateResponse(workflow_run_id=workflow_run.id)


@router.get("/details/{campaign_id}", response_model=CampaignDetail)
def get_campaign_details(
    campaign_id: int,
    db: DbSession,
) -> CampaignDetail:
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
            aspect_ratio=asset.aspect_ratio,
            s3_url=generate_presigned_url(asset.s3_key),
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
      localized_campaign_message=campaign.localized_campaign_message,
      assets=asset_items,
      products=product_items,
  )


@router.get("/download/{campaign_id}")
def download_campaign(campaign_id: int, db: DbSession,) -> StreamingResponse:
  # Ensure the campaign exists
  campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
  if not campaign:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Campaign {campaign_id} not found",
    )

  # Fetch all assets for this campaign
  assets: List[Asset] = (
      db.query(Asset)
      .filter(Asset.campaign_id == campaign_id)
      .all()
  )

  if not assets:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No assets found for campaign {campaign_id}",
    )

  # Create in-memory ZIP
  zip_buffer = create_zip(campaign, assets)

  # Stream the ZIP file back
  filename = f"campaign_{campaign.id}.zip"
  headers = {
      "Content-Disposition": f'attachment; filename="{filename}"'
  }
  return StreamingResponse(
      zip_buffer,
      media_type="application/zip",
      headers=headers,
  )