from __future__ import annotations

from typing import Any, Callable, Awaitable

from telegram import Update
from telegram.ext import ContextTypes

from src.database.repository import (
    ChatMemberRepository,
    ChatRepository,
    MessageLogRepository,
    UserRepository,
)


class MiddlewareChain:
    def __init__(self):
        self._middlewares: list[Callable[[Update, ContextTypes.DEFAULT_TYPE, Callable], Awaitable[None]]] = []

    def add(self, middleware: Callable[[Update, ContextTypes.DEFAULT_TYPE, Callable], Awaitable[None]]):
        self._middlewares.append(middleware)

    async def run(self, update: Update, context: ContextTypes.DEFAULT_TYPE, handler: Callable):
        async def final():
            await handler(update, context)

        chain = final
        for middleware in reversed(self._middlewares):
            prev = chain
            chain = (lambda mw, nxt: lambda u, c: mw(u, c, nxt))(middleware, prev)
        await chain(update, context)


class DatabaseMiddleware:
    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        next_handler: Callable,
    ):
        if not update.effective_user or not update.effective_chat:
            return await next_handler(update, context)

        from src.database.engine import async_session_factory

        async with async_session_factory() as session:
            context.bot_data.setdefault("session", session)
            user_repo = UserRepository(session)
            chat_repo = ChatRepository(session)
            member_repo = ChatMemberRepository(session)
            msg_log_repo = MessageLogRepository(session)

            user = update.effective_user
            chat = update.effective_chat

            await user_repo.get_or_create(
                user.id, user.first_name, user.last_name, user.username
            )
            await chat_repo.get_or_create(chat.id, chat.title, chat.type)

            context.user_data["user_repo"] = user_repo
            context.chat_data["chat_repo"] = chat_repo
            context.user_data["member_repo"] = member_repo
            context.user_data["msg_log_repo"] = msg_log_repo

            await next_handler(update, context)


class AntiFloodMiddleware:
    def __init__(self):
        self._user_message_times: dict[int, list[float]] = {}

    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        next_handler: Callable,
    ):
        if not update.effective_user or not update.message:
            return await next_handler(update, context)

        from src.config import settings

        user_id = update.effective_user.id
        now = update.message.date.timestamp()

        if user_id not in self._user_message_times:
            self._user_message_times[user_id] = []

        times = self._user_message_times[user_id]
        times.append(now)
        times[:] = [t for t in times if now - t < settings.antiflood_window]

        if len(times) > settings.antiflood_max_messages:
            await update.message.delete()
            return

        await next_handler(update, context)
