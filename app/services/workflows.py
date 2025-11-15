from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models.asset import Asset, AssetType, AssetSource
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.campaign_product import CampaignProduct
from app.models.product import Product
from app.models.workflow import WorkflowRun, WorkflowStatus
from app.models.check import Check, CheckResult, CheckType
from app.services.storage import upload_bytes
from app.services.image_generator import get_image_generator

logger = logging.getLogger(__name__)

# hardcode some requirements here for now
REQUIRED_ASPECT_RATIOS = ["1:1", "9:16", "16:9"]

# hardcode the seed here for testing
SEED = 42

@dataclass
class WorkflowGenerationResult:
    workflow_run_id: int
    assets: List[Asset]
    errors: List[str] | None = None

# hardcode the gemini prompt for now
# for prompt engineering, build this out
def _build_prompt(
    brand: Brand,
    campaign: Campaign,
    product: Product,
) -> str:
    primary = getattr(brand, "primary_color_hex", "#FFFFFF")
    secondary = getattr(brand, "secondary_color_hex", "#000000")

    background_description = "professional ice arena packed with fans"

    return (
        f"A high-resolution, studio-lit product photograph of a {product.description} in a {background_description}. "
        f"Ultra-realistic, clean, modern, consistent with brand colors {primary}, {secondary}. "
        f"Target audience: {campaign.target_audience}. "
        f"Region: {campaign.target_region}. "
        f"Suggestive of: {campaign.campaign_message}. "
        f"Avoid: overly cluttered design, off-brand colors, showing lights."
    )

# requirements:
#   - each product has assets for each aspect ratio
#       - required aspect ratios hardcoded as REQUIRED_ASPECT_RATIOS above
def _determine_generation_tasks(
    db: Session,
    campaign: Campaign
) -> List[tuple[Product, str]]:
    tasks: List[tuple[Product, str]] = []

    products = (
        db.query(Product)
        .join(CampaignProduct, CampaignProduct.product_id == Product.id)
        .filter(CampaignProduct.campaign_id == campaign.id)
        .all()
    )

    for product in products:
        for ratio in REQUIRED_ASPECT_RATIOS:
            existing = (
                db.query(Asset)
                .filter(
                    Asset.campaign_id == campaign.id,
                    Asset.product_id == product.id,
                    Asset.aspect_ratio == ratio,
                    Asset.type == AssetType.CREATIVE,
                )
                .first()
            )
            if not existing:
                tasks.append((product, ratio))

    return tasks

def run_campaign_generation(
    db: Session,
    campaign_id: int,
) -> WorkflowGenerationResult:
    """
    Synchronous orchestration of a creative generation workflow for a campaign.

    Steps (POC-level):
      1. Create workflow_run row (status=RUNNING)
      2. Determine missing assets for each product/aspect ratio
      3. For each task:
           - build prompt with brand & campaign context
           - call image generator
           - upload image to S3
           - create Asset row
           - create simple PASS checks (brand & legal) as placeholders
      4. Mark workflow_run COMPLETE / FAILED
      5. Return WorkflowGenerationResult
    """
    campaign: Campaign | None = (
        db.query(Campaign).filter(Campaign.id == campaign_id).first()
    )
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    brand: Brand | None = db.query(Brand).filter(Brand.id == campaign.brand_id).first()
    if not brand:
        raise ValueError(f"Brand {campaign.brand_id} not found for campaign {campaign_id}")

    # 1. Create workflow_run
    workflow_run = WorkflowRun(
        campaign_id=campaign.id,
        status=WorkflowStatus.RUNNING,
    )
    db.add(workflow_run)
    db.flush()  # to get workflow_run.id

    generator = get_image_generator()
    generated_assets: List[Asset] = []
    errors: List[str] = []

    try:
        # 2. Determine tasks
        # hardcode the required aspect ratios here for now
        tasks = _determine_generation_tasks(db=db, campaign=campaign)
        if not tasks:
            logger.info(
                "No new assets to generate for campaign_id=%s (all variants exist).",
                campaign_id,
            )

        # 3. Generate creatives
        for product, ratio in tasks:
            prompt = _build_prompt(brand=brand, campaign=campaign, product=product)

            logger.info(
                "Generating creative: campaign_id=%s product_id=%s ratio=%s",
                campaign.id,
                product.id,
                ratio,
            )
            img_result = generator.generate(prompt=prompt, aspect_ratio=ratio, seed=SEED)

            # Build S3 key hierarchy for traceability
            safe_ratio = ratio.replace(":", "x")
            timestamp = int(datetime.utcnow().timestamp())
            key = (
                f"campaign_{campaign.id}/product_{product.id}/"
                f"{safe_ratio}/creative_{timestamp}.png"
            )

            # Upload image bytes
            upload_bytes(
                data=img_result.content,
                key=key,
                content_type="image/png",
            )

            # Create Asset row
            asset = Asset(
                campaign_id=campaign.id,
                product_id=product.id,
                type=AssetType.CREATIVE,
                aspect_ratio=ratio,
                width=img_result.width,
                height=img_result.height,
                s3_key=key,
                source=AssetSource.GENERATED,
                gen_metadata_json={
                    "prompt": prompt,
                    "model_name": img_result.model_name,
                    "seed": img_result.seed,
                    "generated_at": datetime.utcnow().isoformat(),
                },
            )
            db.add(asset)
            db.flush()  # asset.id

            generated_assets.append(asset)

            # Simple placeholder checks: you can replace this with real logic later
            # brand_check = Check(
            #     workflow_run_id=workflow_run.id,
            #     asset_id=asset.id,
            #     check_type=CheckType.BRAND,
            #     result=CheckResult.PASS,
            #     details_json={
            #         "reason": "Generated via controlled pipeline; logo/colors assumed in template.",
            #     },
            # )
            # legal_check = Check(
            #     workflow_run_id=workflow_run.id,
            #     asset_id=asset.id,
            #     check_type=CheckType.LEGAL,
            #     result=CheckResult.PASS,
            #     details_json={
            #         "reason": "Campaign message scanned via basic rule set (POC placeholder).",
            #     },
            # )
            # db.add(brand_check)
            # db.add(legal_check)

        # 4. Mark workflow_run COMPLETE
        workflow_run.status = WorkflowStatus.COMPLETE
        workflow_run.finished_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        logger.exception(
            "Error during campaign generation for campaign_id=%s: %s",
            campaign_id,
            exc,
        )
        workflow_run.status = WorkflowStatus.FAILED 
        workflow_run.finished_at = datetime.utcnow()
        workflow_run.error_message = str(exc)
        db.commit()
        errors.append(str(exc))

    return WorkflowGenerationResult(
        workflow_run_id=workflow_run.id,
        assets=generated_assets,
        errors=errors or None,
    )
