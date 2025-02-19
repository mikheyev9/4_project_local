from pathlib import Path
import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Config(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Project
    PROJECT_NAME: str = "movies"

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0 
    REDIS_PASSWORD: str | None = None

    # Elasticsearch
    ELASTIC_SCHEMA: str = "http://"
    ELASTIC_HOST: str = "127.0.0.1"
    ELASTIC_PORT: int = 9200
    ELASTIC_MAXSIZE: int = 5
    ELASTIC_TIMEOUT: int = 10
    ELASTIC_RETRIES: int = 3

    # Environment
    ENV: str = "dev"
    LOG_LEVEL: str = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Uvicorn
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000
    UVICORN_RELOAD: bool = True

config = Config()
