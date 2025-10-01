from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    ECHO: bool = False


    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}"
            f":{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}"
            f":{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".dev.env")


settings = Settings()
# print(settings.database_url)