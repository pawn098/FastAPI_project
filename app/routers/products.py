from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated, List
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from sqlalchemy import select, insert, update, delete
from app.schemas import CreateProduct
from app.models import *
from app.routers.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Товары"])

@router.get('/', summary='Получение всех товаров')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.is_active == True,
                                                      Product.stock > 0))
    if products is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Нет продукта'
        )
    return products.all()

@router.post('/', status_code=status.HTTP_201_CREATED, summary='Создание товара')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], create_product: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
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
                                                slug=slugify(create_product.name),
                                                supplier_id=get_user.get('id')))
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='У вас недостаточно прав для этого действия'
        )


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
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str, updata_product: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        product = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found"
            )
        if get_user.get('id') == updata_product.supplier_id or get_user.get('is_admin'):
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
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='У вас недостаточно прав для этого действия'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='У вас недостаточно прав для этого действия'
        )

@router.delete('/{product_slug}', summary='Сделать товар неактивным')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str, get_user: Annotated[dict, Depends(get_current_user)]):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        if get_user.get('id') == product.supplier_id or get_user.get('is_admin'):
            product.is_active = False
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product delete is successful'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have not enough permission for this action'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='У вас недостаточно прав для этого действия'
        )

