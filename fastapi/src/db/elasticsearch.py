from elasticsearch import AsyncElasticsearch
from fastapi import Request

from core.config import config


async def init_elastic() -> AsyncElasticsearch:
    """Создаёт подключение к Elasticsearch."""
    
    return AsyncElasticsearch(
        hosts=[f"{config.ELASTIC_SCHEMA}{config.ELASTIC_HOST}:{config.ELASTIC_PORT}"],
        maxsize=config.ELASTIC_MAXSIZE,
        timeout=config.ELASTIC_TIMEOUT,
        retry_on_timeout=True,
        max_retries=config.ELASTIC_RETRIES,
    )
    
    
def get_elastic(request: Request) -> AsyncElasticsearch:
    """
    Получает подключение к Elasticsearch из состояния приложения.

    Args:
        request (Request): Текущий запрос FastAPI.

    Returns:
        AsyncElasticsearch: Подключение к Elasticsearch.
    """
    
    return request.app.state.es
    