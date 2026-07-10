from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.database.engine import async_session_factory
from src.database.repository import (
    ChatRepository,
    ChatMemberRepository,
    DailyStatsRepository,
    UserRepository,
)

app = FastAPI(title="Fanou3 Bot API", version="1.0.0")


class ChatSettingsUpdate(BaseModel):
    welcome_enabled: bool | None = None
    protection_enabled: bool | None = None
    ai_enabled: bool | None = None
    games_enabled: bool | None = None
    economy_enabled: bool | None = None
    rules: str | None = None
    welcome_message: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "bot": "fanou3"}


@app.get("/api/chats/{chat_id}/stats")
async def get_chat_stats(chat_id: int):
    async with async_session_factory() as session:
        stats_repo = DailyStatsRepository(session)
        stats = await stats_repo.get_range(chat_id, days=7)
        return {
            "chat_id": chat_id,
            "daily_stats": [
                {
                    "date": s.date,
                    "messages": s.total_messages,
                    "new_members": s.total_new_members,
                    "active_users": s.active_users,
                }
                for s in stats
            ],
        }


@app.get("/api/chats/{chat_id}/leaderboard")
async def get_leaderboard(chat_id: int, sort_by: str = "points", limit: int = 10):
    async with async_session_factory() as session:
        member_repo = ChatMemberRepository(session)
        members = await member_repo.get_leaderboard(chat_id, sort_by, limit)
        return {
            "chat_id": chat_id,
            "sort_by": sort_by,
            "leaderboard": [
                {
                    "user_id": m.user_id,
                    "points": m.points,
                    "xp": m.xp,
                    "level": m.level,
                    "coins": m.coins,
                    "reputation": m.reputation,
                    "streak_days": m.streak_days,
                    "total_messages": m.total_messages,
                }
                for m in members
            ],
        }


@app.get("/api/chats/{chat_id}/settings")
async def get_chat_settings(chat_id: int):
    async with async_session_factory() as session:
        chat_repo = ChatRepository(session)
        chat = await chat_repo.get_or_create(chat_id)
        return {
            "chat_id": chat.id,
            "title": chat.title,
            "welcome_enabled": chat.welcome_enabled,
            "protection_enabled": chat.protection_enabled,
            "ai_enabled": chat.ai_enabled,
            "games_enabled": chat.games_enabled,
            "economy_enabled": chat.economy_enabled,
            "rules": chat.rules,
            "welcome_message": chat.welcome_message,
        }


@app.put("/api/chats/{chat_id}/settings")
async def update_chat_settings(chat_id: int, settings: ChatSettingsUpdate):
    async with async_session_factory() as session:
        chat_repo = ChatRepository(session)
        chat = await chat_repo.update_setting(
            chat_id,
            **settings.model_dump(exclude_none=True),
        )
        return {"status": "updated", "chat_id": chat_id}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(user_id)
        return {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "created_at": str(user.created_at),
        }


def start_api():
    import uvicorn
    from src.config import settings

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )
