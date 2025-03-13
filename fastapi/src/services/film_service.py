from typing import Optional, List
from functools import lru_cache


from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elasticsearch import get_elastic
from models.film_model import (FilmResponseModel,
                               FilmSearchResponseModel)
from services.abc.abstract_db_service import AbstractDBService
from db.elasticsearch import get_elastic
from services.genre_service import GenreService, get_genre_service


@lru_cache(maxsize=1)
def get_film_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
    genre_service: GenreService = Depends(get_genre_service)
) -> "FilmService":
    return FilmService(elastic, genre_service)

class FilmService(AbstractDBService[FilmResponseModel, AsyncElasticsearch]):
    film_index = "movies"
    
    def __init__(self, db_client: AsyncElasticsearch, genre_service: GenreService):
        super().__init__(db_client)
        self.genre_service = genre_service

    async def get_by_id(self, film_id: str) -> Optional[FilmResponseModel]:
        """Получает фильм по ID из Elasticsearch."""
        
        try:
            doc = await self.db_client.get(index=self.film_index, id=film_id)
            film_data = doc["_source"]
            genre_names = film_data.get("genres", [])
            genres = await self.genre_service.get_genres_by_names(genre_names)
            film_response_data = {
                **film_data,
                "genre": [{"id": genre.id, "name": genre.name} for genre in genres]
            }
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
        if film.genre:
            genre_names = [genre.name.lower() for genre in film.genre]  # Elasticsearch чувствителен к регистру!
            should_conditions.append({"terms": {"genres": genre_names}})
        if film.actors:
            should_conditions.append({
                "nested": {
                    "path": "actors",
                    "query": {
                        "terms": {"actors.name": [actor.full_name for actor in film.actors]}
                    }
                }
            })
        if film.directors:
            should_conditions.append({
                "nested": {
                    "path": "directors",
                    "query": {
                        "terms": {"directors.name": [director.full_name for director in film.directors]}
                    }
                }
            })
        if film.writers:
            should_conditions.append({
                "nested": {
                    "path": "writers",
                    "query": {
                        "terms": {"writers.name": [writer.full_name for writer in film.writers]}
                    }
                }
            })
        if film.title:
            should_conditions.append({"match": {"title": {"query": film.title, "fuzziness": "AUTO"}}})
        if film.description:
            should_conditions.append({"match": {"description": {"query": film.description, "fuzziness": "AUTO"}}})
        body = {
            "query": {
                "bool": {
                    "should": should_conditions,
                    "minimum_should_match": 1,
                    "must_not": {"term": {"_id": film_id}}
                }
            },
            "sort": [{"imdb_rating": {"order": "desc"}}],
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


    async def get_films_list(
        self, sort: str, genre: Optional[str], page_number: int, page_size: int
    ) -> List[FilmSearchResponseModel]:
        """Получает список фильмов с фильтрацией по жанру и сортировкой по рейтингу."""
        
        sort_field = "imdb_rating"
        sort_order = "desc" if sort == "-imdb_rating" else "asc"
        query_conditions = {"match_all": {}}
        if genre:
            genre_name = await self.genre_service.get_genre_name_by_id(genre)
            if genre_name:
                query_conditions = {"term": {"genres": genre_name}}
            else:
                return []
        body = {
            "query": query_conditions,
            "sort": [{sort_field: {"order": sort_order}}],
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
    
