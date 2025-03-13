from pydantic import BaseModel, Field


class Person(BaseModel):
    """Модель персоны (актёра, режиссёра, сценариста)."""
    uuid: str = Field(alias="id")
    full_name: str = Field(alias="name")