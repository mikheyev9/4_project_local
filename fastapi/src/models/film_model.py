from typing import List, Optional
from pydantic import BaseModel, Field


class Person(BaseModel):
    """Модель персоны (актёра, режиссёра, сценариста)."""
    uuid: str = Field(alias="id")
    full_name: str = Field(alias="name")

class Genre(BaseModel):
    """Модель жанра фильма."""
    uuid: str = Field(alias="id")
    name: str


class FilmResponseModel(BaseModel):
    """Модель ответа API для фильма."""
    uuid: str = Field(alias="id")
    title: str
    imdb_rating: Optional[float]
    description: Optional[str]
    genre: List[Genre]
    actors: List[Person]
    writers: List[Person]
    directors: List[Person]
    
    
class FilmSearchResponseModel(BaseModel):
    uuid: str
    title: str
    imdb_rating: Optional[float]
