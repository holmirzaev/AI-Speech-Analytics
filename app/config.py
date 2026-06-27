from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    REDIS_URL: str

    # Новые переменные для ИИ-сервисов
    YANDEX_IAM_TOKEN: str = "placeholder_token"
    YANDEX_FOLDER_ID: str = "placeholder_folder"

    # Автоматически собираем строку для SQLAlchemy, чтобы не дублировать её в .env
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:5432/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()