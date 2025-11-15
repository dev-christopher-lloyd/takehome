from typing import Any, Dict, List, Generator
import base64
import binascii
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.asset import Asset, AssetSource, AssetType
from app.models.check import Check
from app.schemas.asset import AssetMetadata, AssetUploadRequest
from app.services.storage import generate_presigned_url, upload_bytes

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

@router.post("", response_model=AssetMetadata, status_code=status.HTTP_201_CREATED)
def upload_asset(
    payload: AssetUploadRequest,
    db: Session = Depends(get_db),
) -> AssetMetadata:
    """
    Upload a base64-encoded image to S3 and create an Asset record.

    The Asset is only written to the database if the S3 upload succeeds.
    """
    # --- Decode base64 image -------------------------------------------------
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

    # --- Upload to S3 --------------------------------------------------------
    # Generate a simple key; you can customize the path as needed.
    file_extension = "png"
    if payload.content_type and "jpeg" in payload.content_type:
        file_extension = "jpg"
    elif payload.content_type and "jpg" in payload.content_type:
        file_extension = "jpg"
    elif payload.content_type and "webp" in payload.content_type:
        file_extension = "webp"

    s3_key = (
        f"campaigns/{payload.campaign_id}/products/"
        f"{payload.product_id}/assets/{uuid.uuid4()}.{file_extension}"
    )

    try:
        uploaded_key = upload_bytes(
            data=image_bytes,
            key=s3_key,
            content_type=payload.content_type or "application/octet-stream",
        )
    except Exception as exc:
        # Log in real app; for now just return a 500
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload asset to storage: {exc}",
        )

    # --- Persist Asset only after successful upload -------------------------
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
        product_id=asset.product_id,
        aspect_ratio=asset.aspect_ratio,
        s3_url=s3_url,
        checks=[],  # Newly uploaded assets will not have checks yet
    )


@router.get("/{asset_id}", response_model=AssetMetadata)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
) -> AssetMetadata:
    """
    Return metadata and S3 URL for a single asset, including any checks.
    """
    asset: Asset | None = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found",
        )

    # Collect checks for this asset (brand + legal, etc.)
    checks: List[Check] = (
        db.query(Check)
        .filter(Check.asset_id == asset_id)
        .order_by(Check.created_at.asc())
        .all()
    )

    checks_payload: List[Dict[str, Any]] = [
        {
            "id": check.id,
            "check_type": check.check_type,
            "result": check.result,
            "details": check.details_json or {},
            "created_at": check.created_at,
        }
        for check in checks
    ]

    s3_url = generate_presigned_url(str(asset.s3_key))

    return AssetMetadata(
        id=asset.id,
        product_id=asset.product_id,
        aspect_ratio=asset.aspect_ratio,
        s3_url=s3_url,
        checks=checks_payload,
    )
