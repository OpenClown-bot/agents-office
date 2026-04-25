from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel


class AppConfig(BaseModel):
    db_path: Path
    log_level: str
    telegram_bot_token: str
    telegram_publish_chat_id: str
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_secret: str
    threads_access_token: str
    instagram_access_token: str
    llm_api_key: str
    llm_provider: str
    po_telegram_user_id: str


def load_config() -> AppConfig:
    return AppConfig(
        db_path=Path(os.environ.get("SMM_DB_PATH", "data/smm.db")),
        log_level=os.environ.get("SMM_LOG_LEVEL", "INFO"),
        telegram_bot_token=os.environ.get("SMM_TELEGRAM_BOT_TOKEN", ""),
        telegram_publish_chat_id=os.environ.get("SMM_TELEGRAM_PUBLISH_CHAT_ID", ""),
        x_api_key=os.environ.get("SMM_X_API_KEY", ""),
        x_api_secret=os.environ.get("SMM_X_API_SECRET", ""),
        x_access_token=os.environ.get("SMM_X_ACCESS_TOKEN", ""),
        x_access_secret=os.environ.get("SMM_X_ACCESS_SECRET", ""),
        threads_access_token=os.environ.get("SMM_THREADS_ACCESS_TOKEN", ""),
        instagram_access_token=os.environ.get("SMM_INSTAGRAM_ACCESS_TOKEN", ""),
        llm_api_key=os.environ.get("SMM_LLM_API_KEY", ""),
        llm_provider=os.environ.get("SMM_LLM_PROVIDER", "glm-4-flash"),
        po_telegram_user_id=os.environ.get("SMM_PO_TELEGRAM_USER_ID", ""),
    )
