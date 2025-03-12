import json
from typing import Optional, List
from functools import lru_cache


from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends, HTTPException, Query

from db.elasticsearch import get_elastic
from models.film_model import (FilmResponseModel,
                               Genre,
                               FilmSearchResponseModel)
from services.abc.abstract_db_service import AbstractDBService

from db.elasticsearch import get_elastic


@lru_cache(maxsize=1)
def get_film_service(elastic: AsyncElasticsearch = Depends(get_elastic)) -> 'FilmService':
    """
    Создает и возвращает экземпляр FilmService.
    """
    return FilmService(elastic)

ALLOWED_SORT_FIELDS = {
    "imdb_rating": "imdb_rating",
    "title": "title.raw",  # Используем `.raw` для keyword
    "description": "description",
    "directors_names": "directors_names",
    "actors_names": "actors_names",
    "writers_names": "writers_names"
}

class FilmService(AbstractDBService[FilmResponseModel, AsyncElasticsearch]):
    film_index = "movies"
    genre_index = "genres"
    
    def __init__(self, db_client: AsyncElasticsearch):
        super().__init__(db_client)

    async def get_by_id(self, film_id: str) -> Optional[FilmResponseModel]:
        """Получает фильм по ID из Elasticsearch."""
        
        try:
            
            doc = await self.db_client.get(index=self.film_index, id=film_id)
            film_data = doc["_source"]
        
            genre_names = film_data.get("genres", [])
            genres = await self.get_genres_by_names(genre_names)

            film_response_data = {**film_data, "genre": genres}
            film_response = FilmResponseModel(**film_response_data)
                
            return film_response
        
        except NotFoundError:
            return None
    
    
    async def search(self, query: str, page_number: int, page_size: int) -> List[FilmSearchResponseModel]:
        """Поиск фильмов по запросу."""
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "description"],
                    "type": "best_fields"
                }
            },
            "from": (page_number - 1) * page_size,
            "size": page_size
        }
        res = await self.db_client.search(index=self.film_index, body=body)
        return [
            FilmSearchResponseModel(
                uuid=hit["_id"],
                title=hit["_source"]["title"],
                imdb_rating=hit["_source"].get("imdb_rating")
            )
            for hit in res["hits"]["hits"]
        ]
        
    async def get_similar_films(self, film_id: str, page_number: int, page_size: int) -> List[FilmSearchResponseModel]:
        """Поиск похожих фильмов с более гибкими критериями."""
        film = await self.get_by_id(film_id)
        if not film:
            return []

        should_conditions = []

        # 🔹 Поиск по жанрам (ключевое слово)
        if film.genre:
            genre_names = [genre.name.lower() for genre in film.genre]  # Elasticsearch чувствителен к регистру!
            should_conditions.append({"terms": {"genres": genre_names}})

        # 🔹 Поиск по актёрам (nested-запрос)
        if film.actors:
            should_conditions.append({
                "nested": {
                    "path": "actors",
                    "query": {
                        "terms": {"actors.name": [actor.full_name for actor in film.actors]}
                    }
                }
            })

        # 🔹 Поиск по режиссёрам (nested-запрос)
        if film.directors:
            should_conditions.append({
                "nested": {
                    "path": "directors",
                    "query": {
                        "terms": {"directors.name": [director.full_name for director in film.directors]}
                    }
                }
            })

        # 🔹 Поиск по сценаристам (nested-запрос)
        if film.writers:
            should_conditions.append({
                "nested": {
                    "path": "writers",
                    "query": {
                        "terms": {"writers.name": [writer.full_name for writer in film.writers]}
                    }
                }
            })

        # 🔹 Поиск по названию (full-text search)
        if film.title:
            should_conditions.append({"match": {"title": {"query": film.title, "fuzziness": "AUTO"}}})

        # 🔹 Поиск по описанию (full-text search)
        if film.description:
            should_conditions.append({"match": {"description": {"query": film.description, "fuzziness": "AUTO"}}})

        body = {
            "query": {
                "bool": {
                    "should": should_conditions,  # 🔥 Теперь ищем по любому совпадению
                    "minimum_should_match": 1,   # 🔥 Достаточно ОДНОГО совпадения
                    "must_not": {"term": {"_id": film_id}}  # Исключаем текущий фильм
                }
            },
            "sort": [{"imdb_rating": {"order": "desc"}}],  # Сортируем по рейтингу
            "from": (page_number - 1) * page_size,
            "size": page_size
        }

        print("ES запрос:", body)  # Лог для отладки

        res = await self.db_client.search(index=self.film_index, body=body)
        return [
            FilmSearchResponseModel(
                uuid=hit["_id"],
                title=hit["_source"]["title"],
                imdb_rating=hit["_source"].get("imdb_rating")
            )
            for hit in res["hits"]["hits"]
        ]

    async def get_films_list(
        self, sort: str, genre: Optional[str], page_number: int, page_size: int
    ) -> List[FilmSearchResponseModel]:
        """Получает список фильмов с фильтрацией по жанру и сортировкой по рейтингу."""
        
        sort_field = "imdb_rating"
        sort_order = "desc" if sort == "-imdb_rating" else "asc"

        query_conditions = {"match_all": {}}  # Базовый запрос (все фильмы)

        if genre:
            genre_name = await self.get_genre_name_by_id(genre)
            if genre_name:
                query_conditions = {"term": {"genres": genre_name}}  # Теперь genre — название, а не UUID
            else:
                return []  # Жанр не найден

        body = {
            "query": query_conditions,
            "sort": [{sort_field: {"order": sort_order}}],
            "from": (page_number - 1) * page_size,
            "size": page_size
        }

        res = await self.db_client.search(index=self.film_index, body=body)
        print(res)
        return [
            FilmSearchResponseModel(
                uuid=hit["_id"],
                title=hit["_source"]["title"],
                imdb_rating=hit["_source"].get("imdb_rating")
            )
            for hit in res["hits"]["hits"]
        ]
    
    
    async def get_genre_name_by_id(self, genre_id: str) -> Optional[str]:
        """Получает название жанра по его UUID."""
        try:
            doc = await self.db_client.get(index="genres", id=genre_id)
            return doc["_source"]["name"]
        except NotFoundError:
            return None    
        
    async def get_genres_by_names(self, genre_names: List[str]) -> List[str]:
        """Получает названия жанров по их ID из индекса жанров."""
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
        print("Elasticsearch query: %s", json.dumps(body, indent=2))
        res = await self.db_client.search(index=self.genre_index, body=body)
        return [Genre(id=hit["_id"], name=hit["_source"]["name"]) for hit in res["hits"]["hits"]]


    
