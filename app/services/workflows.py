from __future__ import annotations
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.asset import Asset, AssetType, AssetSource
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.campaign_product import CampaignProduct
from app.models.product import Product
from app.models.workflow import Workflow, WorkflowStatus
from app.services.storage import upload_bytes, get_object_key
from app.services.image_generator import get_image_generator
from app.services.text_generator import TextGenerator, get_text_generator

logger = logging.getLogger(__name__)

# hardcode some requirements here for now
REQUIRED_ASPECT_RATIOS = ["1:1", "9:16", "16:9"]

# hardcode this here for now
TARGET_REGION_LANGUAGE_MAP = {
  "FR": "french",
}


def _build_campaign_message_localization_prompt(brand, campaign, language) -> str:
  brand_tone_of_voice = getattr(brand, "tone_of_voice", "")
  campaign_message = getattr(campaign, "campaign_message", "")
  campaign_target_audience = getattr(campaign, "target_audience", "")

  return f"""
    Instruction:
    You will receive:
      - A short caption written in English.
      - A description of the brand's tone of voice.
      - Information about the target audience.
      - The target language for localization.

    Task:
    Rewrite (localize) the caption into the target language so that:
      - The meaning is preserved, not translated word-for-word.
      - The brand tone is fully maintained (e.g., playful, premium, minimal, energetic, friendly, luxury, etc.).
      - The phrasing feels natural and culturally appropriate for the target audience.
      - The result reads like a native-quality marketing caption, not a direct translation.
      - Keep it short, punchy, and suitable for social media.

    Output:
      - Only output the final localized caption — no explanations.

    Inputs:
      - Original caption: {campaign_message}
      - Brand tone: {brand_tone_of_voice}
      - Target audience: {campaign_target_audience}
      - Target language: {language}
  """

def _build_image_prompt(
    brand: Brand,
    campaign: Campaign,
    product: Product,
) -> str:
  primary = getattr(brand, "primary_color_hex", "#FFFFFF")
  secondary = getattr(brand, "secondary_color_hex", "#000000")
  brand_tone_of_voice = getattr(brand, "tone_of_voice", "")
  campaign_message = getattr(campaign, "campaign_message", "")
  campaign_region = getattr(campaign, "region", "")
  campaign_target_audience = getattr(campaign, "target_audience", "")
  product_description = getattr(product, "description")

  prompt = f"""
  You are an expert creative strategist and ad designer.
  Your task is to write a visual prompt for an image-generation model.

  The resulting image will be used as a social-media **photo advertisement**, 
  so the prompt MUST follow the rules below.

  ---------------------------------------------------------
  SOCIAL-MEDIA AD REQUIREMENTS
  ---------------------------------------------------------
  The image must look like a **real, high-quality commercial photograph**, 
    not artwork, not illustration, not abstract rendering.

  Style must match the standards of Instagram, TikTok, and Facebook ads:
    - clean, modern, premium
    - crisp lighting and professional composition
    - visually engaging and brand-safe

  Avoid all meta references ("this ad", "this prompt", "image generation"). 
    Describe only the photograph.

  ---------------------------------------------------------
  BRANDING CONSTRAINTS
  ---------------------------------------------------------
  Follow these brand constraints:
    - **Brand Identity:** Maintain a look and feel aligned with the brand's 
      personality (e.g., bold, minimalistic, luxurious, playful, earthy).
    - **Color Palette:** Use only colors that align with the brand's palette 
      if provided. If not provided, choose a palette consistent with 
      the brand personality.
    - **Tone & Mood:** Match the brand's emotional tone 
      (e.g., energetic, calming, innovative, aspirational).
    - **Brand Context:** Include brand-appropriate environments, props, 
      and lifestyle cues that fit the target audience.
    - **Brand Safety:** No political, sexual, violent, or controversial imagery.
    - **Logo Usage:** If a logo or label is mentioned, describe it generically 
      (e.g., “subtle branded label”) and never replicate real trademarks.

  ---------------------------------------------------------
  COMPOSITION REQUIREMENTS
  ---------------------------------------------------------
  The prompt must:
    - Clearly highlight the product as the hero.
    - Describe environment, lighting, mood, and camera style.
    - Fit a **social-media ad ratio** (1:1 square or 4:5 portrait), unless specified.
    - Stay within 2-6 vivid, concise sentences.

  ---------------------------------------------------------
  HARD CONSTRAINTS(MUST OBEY, EVEN IF THE BRIEF CONFLICTS)
  ---------------------------------------------------------
    - Do not give any reference to "ads", "image generation", "prompts", or any meta-language. Just describe the photo.
    - Do not include any text on the product
    - Do not include any text in the background
    - Do not include any illicit images or themes
    - Do not include any people

  ---------------------------------------------------------
  OUTPUT FORMAT
  ---------------------------------------------------------
  - Provide ONLY the final prompt. No explanations, no bullet points.
  - The prompt must be a natural photo description aligned with the brand.

  ---------------------------------------------------------

  Create the prompt for:
    Brand primary color: {primary}
    Brand secondary color: {secondary}
    Brand tone of voice: {brand_tone_of_voice}
    Campaign brief: {campaign_message}
    Campaign region: {campaign_region}
    Campaign target audience: {campaign_target_audience}
    Product description: {product_description}
  """

  return prompt

def _determine_image_generation_tasks(
    db: Session,
    campaign: Campaign
) -> List[tuple[Product, str]]:
  '''
  Tasks determination:
    - each product has assets for each aspect ratio
    - required aspect ratios hardcoded as REQUIRED_ASPECT_RATIOS above
  '''
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

def _localize_campaign_message(
    db: Session,
    text_generator: TextGenerator,
    brand: Brand,
    campaign: Campaign
) -> None:
    target_region = campaign.target_region
    if target_region == "US":
      return

    localization_result = ""
    language = TARGET_REGION_LANGUAGE_MAP.get(target_region, None)

    if language is not None:
      localization_prompt = _build_campaign_message_localization_prompt(brand, campaign, language)

      logger.info(
          "Generating text prompt to localize campaign message: brand_id=%s campaign_id=%s prompt=%s",
          brand.id,
          campaign.id,
          localization_prompt,
      )

      localization_result = text_generator.generate(prompt=localization_prompt)

    # add localized message to campaign
    if localization_result and localization_result.content:
      campaign.localized_campaign_message = localization_result.content


def run_campaign_generation(
    workflow_run_id: int,
    campaign_id: int,
) -> None:
  '''
    Synchronous orchestration of a creative generation workflow for a campaign.
    Started in route handler as its own thread.

    Steps:
      1. Create workflow_run row (status=RUNNING)
      2. Run legal checks (todo)
      3. Localize campaign message
      4. Determine tasks, i.e. which assets to generate for missing product/aspect ratio
      5. Generate image assets
        - For each task:
          - prompt llm for creative input prompt for generating images
          - prompt image generator for product image
          - run brand checks (todo)
          - upload image to S3
          - create Asset
      6. Mark workflow_run COMPLETE
  '''
  db: Session = SessionLocal()

  try:
    # 1. set workflow to running
    workflow = db.get(Workflow, workflow_run_id)
    if not workflow:
      return
    workflow.status = WorkflowStatus.RUNNING
    db.commit()

    campaign: Campaign | None = (
        db.query(Campaign).filter(Campaign.id == campaign_id).first()
    )
    if not campaign:
      raise ValueError(f"Campaign {campaign_id} not found")

    brand: Brand | None = db.query(Brand).filter(
        Brand.id == campaign.brand_id).first()
    if not brand:
      raise ValueError(
          f"Brand {campaign.brand_id} not found for campaign {campaign_id}")

    # 2. Run legal checks
    # legal check code here

    image_generator = get_image_generator()
    text_generator = get_text_generator()

    # 3. Localize campaign message
    _localize_campaign_message(db, text_generator, brand, campaign)

    # 4. Determine image generation tasks
    image_tasks = _determine_image_generation_tasks(db=db, campaign=campaign)

    if not image_tasks:
      logger.info(
          "No new assets to generate for campaign_id=%s (all variants exist).",
          campaign_id,
      )

    # 5. Generate image assets
    for product, ratio in image_tasks:
      # 5.1. prompt llm for creative input prompt for generating images
      text_prompt = _build_image_prompt(brand, campaign, product)

      logger.info(
          "Generating text prompt to generate images: brand_id=%s campaign_id=%s product_id=%s prompt=%s",
          brand.id,
          campaign.id,
          product.id,
          text_prompt,
      )

      text_result = text_generator.generate(prompt=text_prompt)

      # 5.2. prompt image generator for product image
      final_image_result = image_generator.generate(
          prompt=text_result.content, aspect_ratio=ratio)
      
      # 5.3. Run brand checks
      # brand check code here
      
      key = get_object_key(campaign.id, product.id, ratio)

      # 5.4 Upload image bytes
      upload_bytes(
          data=final_image_result.content,
          key=key,
          content_type="image/png",
      )

      # 5.5 Create Asset row
      asset = Asset(
          campaign_id=campaign.id,
          product_id=product.id,
          type=AssetType.CREATIVE,
          aspect_ratio=ratio,
          width=final_image_result.width,
          height=final_image_result.height,
          s3_key=key,
          source=AssetSource.GENERATED,
          gen_metadata_json={
              "prompt": text_result.content,
              "model_name": final_image_result.model_name,
              "generated_at": datetime.utcnow().isoformat(),
          },
      )
      db.add(asset)

    # 6. Mark workflow_run COMPLETE
    workflow.status = WorkflowStatus.COMPLETE
    workflow.finished_at = datetime.utcnow()
    db.commit()
  except Exception as e:
    # on error, mark workflow as FAILED
    workflow = db.get(Workflow, workflow_run_id)
    if workflow:
      workflow.status = WorkflowStatus.FAILED
      workflow.finished_at = datetime.utcnow()
      workflow.error_message = str(e)
      db.commit()
    raise
  finally:
    db.close()
