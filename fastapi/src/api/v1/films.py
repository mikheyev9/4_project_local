from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from typing import List

from services.film_service import FilmService, get_film_service
from models.film_model import FilmResponseModel, FilmSearchResponseModel

router = APIRouter()


@router.get('/search/', response_model=List[FilmSearchResponseModel])
async def search_films(
    query: str = Query(..., description="Search query"),
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    film_service: FilmService = Depends(get_film_service)
) -> List[FilmSearchResponseModel]:
        
    return await film_service.search(query, page_number, page_size)


@router.get('/{film_id}', response_model=FilmResponseModel)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service)
) -> FilmResponseModel:
    
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")
    return film
