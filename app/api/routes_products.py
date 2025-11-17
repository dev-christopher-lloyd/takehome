from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse
from app.core.db import DbSession

router = APIRouter()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: DbSession,
) -> ProductResponse:
  product = Product(
      name=payload.name,
      description=payload.description,
      metadata_json=payload.metadata_json,
  )

  if not product:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid Product payload",
    )

  db.add(product)
  db.commit()
  db.refresh(product)

  return product


@router.get("", response_model=List[ProductResponse])
def list_products(
    db: DbSession,
) -> List[ProductResponse]:
  products = db.query(Product).all()
  return [product for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: DbSession,
) -> ProductResponse:
  product = db.query(Product).filter(Product.id == product_id).first()
  if not product:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product {product_id} not found",
    )
  return product
