from typing import List, Optional

from pydantic import BaseModel, Field

from models.genre_model import Genre
from models.person_model import Person

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
