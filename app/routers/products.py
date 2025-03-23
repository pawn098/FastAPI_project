from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from sqlalchemy import select, insert, update, delete
from app.schemas import CreateProduct
from app.models import *

router = APIRouter(prefix="/products", tags=["Товары"])

@router.get('/', summary='Получение всех товаров')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.is_active == True,
                                                      Product.stock > 0))
    if products is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    return products.all()

@router.post('/', status_code=status.HTTP_201_CREATED, summary='Создание товара')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], create_product: CreateProduct):
    category = await db.scalar(select(Category).where(Category.id == create_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    await db.execute(insert(Product).values(name=create_product.name,
                                            description=create_product.description,
                                            price=create_product.price,
                                            image_url=create_product.image_url,
                                            stock=create_product.stock,
                                            category_id=create_product.category,
                                            rating=0.0,
                                            slug=slugify(create_product.name)))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/{category_slug}', summary='Получение товаров по категории')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id))
    categories_and_subcategories = [category.id] + [i.id for i in subcategories.all()]
    products_category = await db.scalars(
        select(Product).where(Product.category_id.in_(categories_and_subcategories), Product.is_active == True,
                              Product.stock > 0))
    return products_category.all()




@router.get("/detail/{product_slug}", summary='Получение товара')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.is_active == True,
                                                    Product.stock > 0))
    if product is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    return product

@router.put('/{product_slug}', summary='Изменение товара')
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str, updata_product: CreateProduct):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    category = await db.scalar(select(Category).where(Category.id == updata_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    product.name = updata_product.name
    product.description = updata_product.description
    product.price = updata_product.price
    product.image_url = updata_product.image_url
    product.stock = updata_product.stock
    product.category_id = updata_product.category
    product.slug = slugify(updata_product.name)

    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }

@router.delete('/{product_slug}', summary='Сделать товар неактивным')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    product.is_active = False
    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }

