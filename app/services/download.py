from io import BytesIO
from typing import List
from zipfile import ZipFile, ZIP_DEFLATED
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.services.storage import download_fileobj

def create_zip(campaign: Campaign, assets: List[Asset]) -> BytesIO:
  # Determine content for post.txt
  if getattr(campaign, "target_region", None) == "US":
      post_content = campaign.campaign_message or ""
  else:
      # Prefer localized message, fall back to original if missing
      post_content = (
          getattr(campaign, "localized_campaign_message", None)
          or campaign.campaign_message
          or ""
      )

  # Derive the "campaign_" folder name from the first asset's key
  # e.g. "campaign_123/product_1/1x1.png" -> "campaign_123"
  first_key = assets[0].s3_key
  if "/" in first_key:
      campaign_folder = first_key.split("/", 1)[0]
  else:
      # Fallback if keys are flat
      campaign_folder = f"campaign_{campaign.id}"

  post_txt_zip_path = f"{campaign_folder}/post.txt"

  # Create in-memory ZIP
  zip_buffer = BytesIO()
  with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zipf:
    manifest_lines = [
        f"Campaign ID: {campaign.id}",
        f"Campaign Name: {campaign.name}",
        f"Brand ID: {campaign.brand_id}",
        "",
        "Assets:",
    ]

    for asset in assets:
      # Download from S3
      file_obj = download_fileobj(asset.s3_key)
      if file_obj is None:
        # Skip missing objects but note them in the manifest
        manifest_lines.append(
            f"- asset_id={asset.id}, product_id={asset.product_id}, "
            f"aspect_ratio={asset.aspect_ratio}, s3_key={asset.s3_key} (MISSING)"
        )
        continue

      # Write image bytes into the ZIP
      zipf.writestr(asset.s3_key, file_obj.getvalue())

      # Record in manifest
      manifest_lines.append(
          f"- asset_id={asset.id}, product_id={asset.product_id}, "
          f"aspect_ratio={asset.aspect_ratio}, s3_key={asset.s3_key}, "
          f"zip_path={asset.s3_key}"
      )

    # Add a text file with campaign + asset info
    manifest_content = "\n".join(manifest_lines) + "\n"
    zipf.writestr("campaign.txt", manifest_content)

    # add post content
    zipf.writestr(post_txt_zip_path, post_content)

  zip_buffer.seek(0)

  return zip_buffer