from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandResponse
from app.core.db import DbSession

router = APIRouter()

@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(
    payload: BrandCreate,
    db: DbSession,
) -> BrandResponse:
  brand = Brand(name=payload.name,
                primary_color_hex=payload.primary_color_hex,
                secondary_color_hex=payload.secondary_color_hex,
                tone_of_voice=payload.tone_of_voice,
                font_family=payload.font_family)

  if not brand:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid Brand payload",
    )

  db.add(brand)
  db.commit()
  db.refresh(brand)

  return brand


@router.get("", response_model=List[BrandResponse])
def list_brands(
    db: DbSession,
) -> List[BrandResponse]:
  brands = db.query(Brand).all()
  return [brand for brand in brands]


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(
    brand_id: int,
    db: DbSession,
) -> BrandResponse:
  brand = db.query(Brand).filter(Brand.id == brand_id).first()
  if not brand:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Brand {brand_id} not found",
    )
  return brand
