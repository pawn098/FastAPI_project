from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from sqlalchemy import insert, select, delete
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.schemas import CreateCategory
from app.models.category import Category
from app.models.products import Product


router = APIRouter(prefix='/categories', tags=['Категории товаров'])

@router.get('/', summary='Получение всех категорий')
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await db.scalars(select(Category).where(Category.is_active == True))
    return categories.all()


@router.post('/', summary='Создание категории')
async def create_category(db: Annotated[AsyncSession, Depends(get_db)], create_category: CreateCategory):
    await db.execute(insert(Category).values(name=create_category.name,
                                             parent_id=create_category.parent_id,
                                             slug=slugify(create_category.name)))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.put('/{category_slug}', summary='Изменение категории')
async def update_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str, update_category: CreateCategory):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )

    category.name = update_category.name
    category.slug = slugify(update_category.name)
    category.parent_id = update_category.parent_id

    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Category update is successful'
    }

@router.delete('/{category_slug}', summary='сделать категорию неактивной')
async def delete_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    category.is_active = False
    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Category delete is successful'
    }

