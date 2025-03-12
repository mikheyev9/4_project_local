from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from services.film_service import FilmService, get_film_service
from models.film_model import FilmResponseModel, FilmSearchResponseModel

router = APIRouter()

@router.get("/", response_model=List[FilmSearchResponseModel])
async def get_films_list(
    sort: str = Query("-imdb_rating", description="Sort order"),
    genre: Optional[str] = Query(None, description="Filter by genre UUID"),
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    film_service: FilmService = Depends(get_film_service)
) -> List[FilmSearchResponseModel]:
    """
    Получает список фильмов с возможностью сортировки по рейтингу и фильтрации по жанру.
    """
    return await film_service.get_films_list(sort, genre, page_number, page_size)


@router.get('/films', response_model=List[FilmSearchResponseModel])
async def get_films(
    sort: Optional[List[str]] = Query(None, description="Sorting fields, e.g. '-imdb_rating'"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    film_service: FilmService = Depends(get_film_service)
) -> List[FilmSearchResponseModel]:
    """
    Получить список фильмов с фильтрацией и множественной сортировкой.

    - `sort`: список полей для сортировки. Пример: `["-imdb_rating", "title"]`
    - `genre`: фильтрация по жанру (название жанра)
    - `page_number`: номер страницы
    - `page_size`: количество записей на странице
    """
    return await film_service.get_films_list(sort, genre, page_number, page_size)


@router.get('/{film_id}', response_model=FilmResponseModel)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service)
) -> FilmResponseModel:
    
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")
    return film


@router.get("/{film_id}/similar", response_model=List[FilmSearchResponseModel])
async def similar_films(
    film_id: str,
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Page size"),
    film_service: FilmService = Depends(get_film_service)
) -> List[FilmSearchResponseModel]:
    """
    Возвращает список похожих фильмов по жанрам, актёрам, режиссёрам, сценаристам, названию и описанию.
    """
    return await film_service.get_similar_films(film_id, page_number, page_size)

