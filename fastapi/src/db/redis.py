from fastapi import Request
from redis.asyncio import Redis, ConnectionPool

from core.config import config


async def init_redis() -> Redis:
    """Создаёт подключение к Redis с логином и паролем."""
    
    pool = ConnectionPool.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}",
                                   max_connections=10,
                                   password=config.REDIS_PASSWORD or None,)
    return Redis(connection_pool=pool)


async def get_redis(request: Request) -> Redis:
    """
    Получает подключение к Redis из состояния приложения.

    Args:
        request (Request): Текущий запрос FastAPI.

    Returns:
        Redis: Подключение к Redis.
    """
    
    return request.app.state.redis