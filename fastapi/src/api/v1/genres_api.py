from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from http import HTTPStatus

from services.genre_service import GenreService, get_genre_service
from models.genre_model import Genre

router = APIRouter()

@router.get("/", response_model=List[Genre])
async def get_genres_list(
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    genre_service: GenreService = Depends(get_genre_service)
) -> List[Genre]:
    """
    Получает список жанров с пагинацией.
    """
    return await genre_service.get_genres_list(page_number, page_size)


@router.get("/search", response_model=List[Genre])
async def search_genres(
    query: str = Query(..., description="Поисковый запрос"),
    page_number: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    genre_service: GenreService = Depends(get_genre_service)
) -> List[Genre]:
    """
    Поиск жанров по названию с учетом опечаток.
    """
    return await genre_service.search(query, page_number, page_size)


@router.get("/{genre_id}", response_model=Genre)
async def get_genre_by_id(
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    """
    Получает жанр по его UUID.
    """
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Genre not found")
    return genre
