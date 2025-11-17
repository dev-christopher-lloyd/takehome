import base64
import binascii
from fastapi import APIRouter, HTTPException, status
from app.models.asset import Asset, AssetSource, AssetType
from app.schemas.asset import AssetMetadata, AssetUploadRequest
from app.services.storage import generate_presigned_url, upload_bytes, get_object_key
from app.core.db import DbSession

router = APIRouter()


@router.post("", response_model=AssetMetadata, status_code=status.HTTP_201_CREATED)
def upload_asset(
    payload: AssetUploadRequest,
    db: DbSession,
) -> AssetMetadata:
  base64_str = payload.image_base64

  # Support optional data URL prefix ("data:image/png;base64,...")
  if "," in base64_str:
    base64_str = base64_str.split(",", 1)[1]

  try:
    image_bytes = base64.b64decode(base64_str, validate=True)
  except (binascii.Error, ValueError):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid base64 image data",
    )

  # throw an error if the image data is empty
  if not image_bytes:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Image data is empty (0 bytes after base64 decode)",
    )

  # s3 object key
  # note, this method assumes .png
  key = get_object_key(payload.campaign_id, payload.product_id, payload.aspect_ratio)

  try:
    uploaded_key = upload_bytes(
        data=image_bytes,
        key=key,
        content_type=payload.content_type or "application/octet-stream",
    )
  except Exception as exc:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Failed to upload asset to storage: {exc}",
    )

  asset = Asset(
      campaign_id=payload.campaign_id,
      product_id=payload.product_id,
      type=int(AssetType.CREATIVE),
      aspect_ratio=payload.aspect_ratio,
      width=None,
      height=None,
      s3_key=uploaded_key,
      source=int(AssetSource.UPLOADED),
      gen_metadata_json=None,
  )

  db.add(asset)
  db.commit()
  db.refresh(asset)

  s3_url = generate_presigned_url(str(asset.s3_key))

  return AssetMetadata(
      id=asset.id,
      aspect_ratio=asset.aspect_ratio,
      s3_url=s3_url,
  )


@router.get("/{asset_id}", response_model=AssetMetadata)
def get_asset(
    asset_id: int,
    db: DbSession,
) -> AssetMetadata:
  asset: Asset | None = db.query(Asset).filter(Asset.id == asset_id).first()
  if not asset:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Asset {asset_id} not found",
    )

  s3_url = generate_presigned_url(str(asset.s3_key))

  return AssetMetadata(
      id=asset.id,
      aspect_ratio=asset.aspect_ratio,
      s3_url=s3_url,
  )
