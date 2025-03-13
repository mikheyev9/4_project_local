from typing import Optional, List
from functools import lru_cache

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elasticsearch import get_elastic
from models.genre_model import Genre
from services.abc.abstract_db_service import AbstractDBService


@lru_cache(maxsize=1)
def get_genre_service(elastic: AsyncElasticsearch = Depends(get_elastic)) -> 'GenreService':
    return GenreService(elastic)


class GenreService(AbstractDBService[Genre, AsyncElasticsearch]):
    genre_index = "genres"
    
    def __init__(self, db_client: AsyncElasticsearch):
        super().__init__(db_client)

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        """Получает жанр по ID из Elasticsearch."""
        try:
            doc = await self.db_client.get(index=self.genre_index, id=genre_id)
            genre_data = doc["_source"]
            return Genre(**genre_data)
        except NotFoundError:
            return None
        
    async def search(self, query: str, page_number: int, page_size: int) -> List[Genre]:
        """Поиск жанров по названию (с учетом опечаток)."""
        body = {
            "query": {
                "match": {
                    "name": {
                        "query": query,
                        "fuzziness": "AUTO"  # Разрешает небольшие опечатки
                    }
                }
            },
            "from": (page_number - 1) * page_size,
            "size": page_size
        }

        try:
            res = await self.db_client.search(index=self.genre_index, body=body)
            return [Genre(id=hit["_id"], name=hit["_source"]["name"]) for hit in res["hits"]["hits"]]
        except Exception:
            return []

    async def get_genres_list(
        self,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Genre]:
        """Получает список жанров с пагинацией."""
        query = {
            "from": (page_number - 1) * page_size,
            "size": page_size
        }
        try:
            response = await self.db_client.search(index=self.genre_index, body=query)
            genres = [Genre(**hit["_source"]) for hit in response["hits"]["hits"]]
            return genres
        except NotFoundError:
            return []
        
    async def get_genre_name_by_id(self, genre_id: str) -> Optional[str]:
        """Получает название жанра по его UUID."""
        try:
            doc = await self.db_client.get(index="genres", id=genre_id)
            return doc["_source"]["name"]
        except NotFoundError:
            return None    
        
    async def get_genres_by_names(self, genre_names: List[str]) -> List[str]:
        """Получает названия жанров по их названиям из индекса жанров."""
        if not genre_names:
            return []
        
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"name": name}} for name in genre_names
                    ]
                }
            }
        }
        res = await self.db_client.search(index=self.genre_index, body=body)
        return [Genre(id=hit["_id"], name=hit["_source"]["name"]) for hit in res["hits"]["hits"]]
