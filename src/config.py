from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: str
    database_url: str = "sqlite+aiosqlite:///./data/fano3.db"
    redis_url: str | None = None
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "DEBUG"
    ai_api_url: str = "https://text.pollinations.ai"
    owner_id: int | None = None

    # Paths
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")

    # Moderation defaults
    max_warnings: int = 3
    mute_duration_seconds: int = 3600
    auto_activity_interval: int = 2700
    max_message_length: int = 1000
    max_repeated_chars: int = 10
    max_mentions_per_message: int = 5
    antiflood_window: int = 5
    antiflood_max_messages: int = 4
    new_account_days: int = 7

    # Economy defaults
    daily_reward: int = 50
    weekly_reward: int = 200
    starting_balance: int = 100
    message_coins: int = 1
    coin_transfer_tax: float = 0.05

    # Gamification
    xp_per_message: int = 10
    xp_per_game: int = 25
    xp_per_streak_day: int = 50
    level_multiplier: int = 100


settings = Settings()
