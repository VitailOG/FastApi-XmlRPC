from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    API_VERSION_PREFIX: str = "/v1"


@lru_cache()
def cached_settings():
    return Settings()


settings = cached_settings()
