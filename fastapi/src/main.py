import logging
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from core.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

from core.config import config
from db.elasticsearch import init_elastic
from db.redis import init_redis
from api.v1 import films_api
logger.debug(f"Config ENV: {config.dict()}")


async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    """Контекстный менеджер для управления ресурсами."""
    
    redis = await init_redis()
    es = await init_elastic()

    app.state.redis = redis
    app.state.es = es

    yield  # Передаём управление FastAPI

    await redis.close()
    await es.close()



app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url='/api/openapi' if config.ENV == 'dev' else None,
    openapi_url='/api/openapi.json' if config.ENV == 'dev' else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(films_api.router, prefix='/api/v1/films', tags=['films']) 


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.UVICORN_HOST,
        port=config.UVICORN_PORT,
        log_config=LOGGING,
        log_level=config.LOG_LEVEL.lower(),
        reload=config.UVICORN_RELOAD,
    )