from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from sqlalchemy import insert, select, update, delete
from slugify import slugify

from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from app.models.products import Product
from app.models.category import Category

router = APIRouter(prefix="/products", tags=["Товары"])

@router.get('/', description="Данный запрос предоставляет весь список товаров")
async def all_products(db: Annotated[Session, Depends(get_db)]):
    products = db.scalars(select(Product).join(Category).where(Product.is_active == True,
                                                               Category.is_active == True,
                                                               Product.stock > 0)).all()
    if products is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    return products
@router.post('/', status_code=status.HTTP_201_CREATED, description="Запрос для создания товара")
async def create_product(db: Annotated[Session, Depends(get_db)], create_product: CreateProduct):
    category = db.scalar(select(Category).where(Category.id == create_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    db.execute(insert(Product).values(name=create_product.name,
                                      description=create_product.description,
                                      price=create_product.price,
                                      image_url=create_product.image_url,
                                      stock=create_product.stock,
                                      category_id=create_product.category,
                                      rating=0.0,
                                      slug=slugify(create_product.name)))
    db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[Session, Depends(get_db)], category_slug: str):
    category = db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    subcategories = db.scalars(select(Category).where(Category.parent_id == category.id)).all()
    categories_and_subcategories = [category.id] + [i.id for i in subcategories]
    products_category = db.scalars(
        select(Product).where(Product.category_id.in_(categories_and_subcategories), Product.is_active == True,
                              Product.stock > 0)).all()
    return products_category




@router.get("/detail/{product_slug}")
async def product_detail(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalar(select(Product).where(Product.slug == product_slug,
                                              Product.is_active == True,
                                              Product.stock > 0))
    if not product:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    return product

@router.put('/{product_slug}')
async def update_product(db: Annotated[Session, Depends(get_db)], product_slug: str, updata_product: CreateProduct):
    product = db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    category = db.scalar(select(Category).where(Category.id == updata_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    db.execute(update(Product).where(Product.slug == product_slug).values(name=updata_product.name,
                                                                          description=updata_product.description,
                                                                          price=updata_product.price,
                                                                          image_url=updata_product.image_url,
                                                                          stock=updata_product.stock,
                                                                          category_id=updata_product.category,
                                                                          slug=slugify(updata_product.name)))
    db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }

@router.delete('/{product_slug}')
async def delete_product(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    db.execute(update(Product).where(Product.slug == product_slug).values(is_active=False))
    db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }

@router.delete("/")
async def delete_table(db: Annotated[Session, Depends(get_db)]):
    db.execute(delete(Product))
    db.commit()
    return "Yes"