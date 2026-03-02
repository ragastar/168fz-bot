import os

from pydantic_settings import BaseSettings

_default_db = "/data/bot.db" if os.path.isdir("/data") else "data/bot.db"


class Settings(BaseSettings):
    bot_token: str
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4"
    admin_chat_id: int = 0
    db_path: str = _default_db
    rate_limit_per_minute: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
