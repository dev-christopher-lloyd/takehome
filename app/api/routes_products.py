from typing import Generator, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse

router = APIRouter()


def get_db() -> Generator[Session, None, None]:
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
) -> List[ProductResponse]:
  products = db.query(Product).all()
  return [product for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductResponse:
  product = db.query(Product).filter(Product.id == product_id).first()
  if not product:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product {product_id} not found",
    )
  return product
