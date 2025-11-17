from __future__ import annotations
import logging
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def _generate_single_asset(
    workflow_run_id: int,
    campaign_id: int,
    product_id: int,
    aspect_ratio: str,
) -> None:
  """
  Generate one asset: prompt text, generate image, upload to S3, create Asset row.
  Runs in its own thread with its own DB session.
  """
  with SessionLocal() as db:
    try:
      campaign = db.get(Campaign, campaign_id)
      if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

      brand = db.get(Brand, campaign.brand_id)
      if not brand:
        raise ValueError(
          f"Brand {campaign.brand_id} not found for campaign {campaign_id}"
        )

      product = db.get(Product, product_id)
      if not product:
        raise ValueError(f"Product {product_id} not found")

      # thread safe generators
      text_generator = get_text_generator()
      image_generator = get_image_generator()

      # prompt llm for creative input prompt
      text_prompt = _build_image_prompt(brand, campaign, product)

      logger.info(
        "Generating text prompt: workflow_id=%s campaign_id=%s product_id=%s ratio=%s prompt=%s",
        workflow_run_id,
        campaign.id,
        product.id,
        aspect_ratio,
        text_prompt,
      )

      text_result = text_generator.generate(prompt=text_prompt)
      if not text_result or not getattr(text_result, "content", None):
        raise RuntimeError("Text generator failed to return content.")

      # generate image
      final_image_result = image_generator.generate(
        prompt=text_result.content,
        aspect_ratio=aspect_ratio,
      )
      if not final_image_result or final_image_result.content is None:
        raise RuntimeError("Image generator returned no content.")

      key = get_object_key(campaign.id, product.id, aspect_ratio)

      # upload to s3
      upload_bytes(
        data=final_image_result.content,
        key=key,
        content_type="image/png",
      )

      # write to db
      asset = Asset(
        campaign_id=campaign.id,
        product_id=product.id,
        type=AssetType.CREATIVE,
        aspect_ratio=aspect_ratio,
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
      db.commit()

    except Exception:
      logger.exception(
        "Error generating asset for workflow_id=%s campaign_id=%s product_id=%s ratio=%s",
        workflow_run_id,
        campaign_id,
        product_id,
        aspect_ratio,
      )
      db.rollback()
      # let the exception bubble up
      raise


def run_campaign_generation(
    workflow_run_id: int,
    campaign_id: int,
) -> None:
  '''
    Orchestration of a creative generation workflow for a campaign.
    Asset generation is spawned out to threads.
  '''
  with SessionLocal() as db:
    try:
      # 1. set workflow to running
      workflow = db.get(Workflow, workflow_run_id)
      if not workflow:
        logger.error("Workflow %s not found; aborting generation.", workflow_run_id)
        return
      workflow.status = WorkflowStatus.RUNNING
      workflow.started_at = datetime.utcnow()
      db.commit()

      campaign = db.get(Campaign, campaign_id)
      if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

      brand = db.get(Brand, campaign.brand_id)
      if not brand:
        raise ValueError(
            f"Brand {campaign.brand_id} not found for campaign {campaign_id}")

      # localize campaign message
      # TODO: add this as a spawned thread task
      text_generator = get_text_generator()
      _localize_campaign_message(db, text_generator, brand, campaign)

      # 4. Determine image generation tasks
      image_tasks = _determine_image_generation_tasks(db=db, campaign=campaign)

      if not image_tasks:
        logger.info(
            "No new assets to generate for campaign_id=%s (all variants exist).",
            campaign_id,
        )
        workflow.status = WorkflowStatus.COMPLETE
        workflow.finished_at = datetime.utcnow()
        db.commit()
        return
    except Exception as e:
      # error before threads are spawned
      logger.exception("Error preparing workflow %s", workflow_run_id)
      try:
        db.rollback()
        workflow = db.get(Workflow, workflow_run_id)
        if workflow:
          workflow.status = WorkflowStatus.FAILED
          workflow.finished_at = datetime.utcnow()
          workflow.error_message = str(e)
          db.commit()
      except Exception:
        db.rollback()
      raise

  # spawn threads for each asset
  errors: list[Exception] = []

  max_workers = min(len(image_tasks), 6)

  with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = []
    for product, ratio in image_tasks:
      futures.append(
        executor.submit(
          _generate_single_asset,
          workflow_run_id=workflow_run_id,
          campaign_id=campaign_id,
          product_id=product.id,
          aspect_ratio=ratio,
        )
      )

    for future in as_completed(futures):
      try:
        future.result()
      except Exception as e:
        errors.append(e)

  with SessionLocal() as db:
    workflow = db.get(Workflow, workflow_run_id)
    if not workflow:
      logger.error("Workflow %s not found when finalizing.", workflow_run_id)
      return

    if errors:
      logger.error(
        "Workflow %s completed with %d asset errors; marking FAILED.",
        workflow_run_id,
        len(errors),
      )
      workflow.status = WorkflowStatus.FAILED
      workflow.error_message = str(errors[0])  # or aggregate
    else:
      workflow.status = WorkflowStatus.COMPLETE

    workflow.finished_at = datetime.utcnow()
    db.commit()
    
  # should we raise an error here if there are errors?
  if errors:
    raise RuntimeError(f"Workflow {workflow_run_id} failed; {len(errors)} asset errors")