from pydantic import BaseModel

class Genre(BaseModel):
    """Модель жанра фильма."""
    id: str
    name: str