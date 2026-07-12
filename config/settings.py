from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/mokovaya"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
