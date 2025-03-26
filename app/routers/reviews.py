

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from sqlalchemy import insert, select, delete, func, update
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.schemas import CreateReviews
from app.models.category import Category
from app.models.products import Product
from app.models.reviews import Review
from app.routers.auth import get_current_user


router = APIRouter(prefix='/products/reviews', tags=['Отзывы'])

@router.get('/', summary='Получение всех отзывов')
async def get_all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    comments = await db.scalars(select(Review).where(Review.is_active == True))
    return comments.all()

@router.get('/{product_id}', summary='Получение отзывов о товаре по id')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)], product_id: int):
    comment = await db.scalars(select(Review).where(Review.is_active == True, Review.product_id == product_id))
    return comment.all()


@router.post('/{product_id}', status_code=status.HTTP_201_CREATED, summary='Создание отзыва о товаре по id')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)], product_id: int, create_comment: CreateReviews, get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get('is_customer'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только покупатели могут оставлять отзывы"
        )

    product = await db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Товар не найден'
        )

    await db.execute(insert(Review).values(user_id=get_user.get('id'),
                                           product_id=product_id,
                                           comment=create_comment.comment,
                                           grade=create_comment.grade))

    await db.commit()

    avg_rating = await db.scalar(select(func.avg(Review.grade)).where(Review.product_id == product_id))

    if avg_rating is not None:
        await db.execute(update(Product).where(Product.id == product_id).values(rating=round(avg_rating, 1)))

    await db.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Отзыв создан'
    }

@router.delete('/{product_id}{reviews_id}', summary='Удаление отзыва об определенном товаре  по id')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)], product_id: int, reviews_id: int, get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут удалять отзывы"
        )

    product = await db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Товар не найден'
        )
    comment = await db.scalar(select(Review).where(Review.id == reviews_id))
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Комментарий не найден'
        )
    comment.is_active = False
    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Отзыв успешно удален'
    }



