from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import func, select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Chat,
    ChatMember,
    DailyStats,
    Filter,
    Infraction,
    KnowledgeEntry,
    MessageLog,
    ScheduledJob,
    Transaction,
    User,
    UserAchievement,
    UserRole,
    InfractionType,
    TransactionType,
)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, first_name: str = "", last_name: str | None = None, username: str | None = None) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            user = User(id=user_id, first_name=first_name, last_name=last_name, username=username)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        else:
            changed = False
            if first_name and user.first_name != first_name:
                user.first_name = first_name; changed = True
            if last_name is not None and user.last_name != last_name:
                user.last_name = last_name; changed = True
            if username is not None and user.username != username:
                user.username = username; changed = True
            if changed:
                await self.session.commit()
        return user


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, chat_id: int, title: str = "", chat_type: str = "supergroup") -> Chat:
        chat = await self.session.get(Chat, chat_id)
        if not chat:
            chat = Chat(id=chat_id, title=title, type=chat_type)
            self.session.add(chat)
            await self.session.commit()
            await self.session.refresh(chat)
        else:
            if title and chat.title != title:
                chat.title = title
                await self.session.commit()
        return chat

    async def update_setting(self, chat_id: int, **kwargs) -> Chat:
        chat = await self.session.get(Chat, chat_id)
        if chat:
            for key, value in kwargs.items():
                if hasattr(chat, key):
                    setattr(chat, key, value)
            await self.session.commit()
        return chat


class ChatMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int, chat_id: int) -> ChatMember | None:
        stmt = select(ChatMember).where(
            ChatMember.user_id == user_id, ChatMember.chat_id == chat_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int, chat_id: int) -> ChatMember:
        member = await self.get(user_id, chat_id)
        if not member:
            member = ChatMember(user_id=user_id, chat_id=chat_id)
            self.session.add(member)
            await self.session.commit()
            await self.session.refresh(member)
        return member

    async def add_points(self, user_id: int, chat_id: int, amount: int = 1) -> ChatMember:
        member = await self.get_or_create(user_id, chat_id)
        member.points += amount
        member.total_messages += 1
        member.xp += 10
        member.last_active = datetime.utcnow()
        await self._check_level_up(member)
        await self.session.commit()
        return member

    async def add_coins(self, user_id: int, chat_id: int, amount: int) -> ChatMember:
        member = await self.get_or_create(user_id, chat_id)
        member.coins += amount
        await self.session.commit()
        return member

    async def add_reputation(self, user_id: int, chat_id: int, amount: float) -> ChatMember:
        member = await self.get_or_create(user_id, chat_id)
        member.reputation += amount
        await self.session.commit()
        return member

    async def add_warning(self, user_id: int, chat_id: int) -> ChatMember:
        member = await self.get_or_create(user_id, chat_id)
        member.warnings += 1
        await self.session.commit()
        return member

    async def set_role(self, user_id: int, chat_id: int, role: UserRole) -> ChatMember:
        member = await self.get_or_create(user_id, chat_id)
        member.role = role
        await self.session.commit()
        return member

    async def get_leaderboard(
        self, chat_id: int, sort_by: str = "points", limit: int = 10
    ):
        column = getattr(ChatMember, sort_by, ChatMember.points)
        stmt = (
            select(ChatMember)
            .where(ChatMember.chat_id == chat_id)
            .order_by(column.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_streak(self, user_id: int, chat_id: int) -> ChatMember:
        member = await self.get_or_create(user_id, chat_id)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if member.last_active_date != today:
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            if member.last_active_date == yesterday:
                member.streak_days += 1
            else:
                member.streak_days = 1
            member.last_active_date = today
            await self.session.commit()
        return member

    async def _check_level_up(self, member: ChatMember):
        from src.config import settings
        needed_xp = member.level * settings.level_multiplier
        if member.xp >= needed_xp:
            member.level += 1
            member.xp -= needed_xp
            member.coins += member.level * 10


class InfractionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        chat_id: int,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        reason: str | None = None,
        duration: int | None = None,
    ) -> Infraction:
        infraction = Infraction(
            chat_id=chat_id,
            user_id=user_id,
            moderator_id=moderator_id,
            type=infraction_type,
            reason=reason,
            duration_seconds=duration,
            expires_at=(
                datetime.utcnow() + timedelta(seconds=duration) if duration else None
            ),
        )
        self.session.add(infraction)
        await self.session.commit()
        await self.session.refresh(infraction)
        return infraction

    async def get_active(self, user_id: int, chat_id: int) -> list[Infraction]:
        stmt = select(Infraction).where(
            Infraction.user_id == user_id,
            Infraction.chat_id == chat_id,
            Infraction.is_active == True,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def deactivate_expired(self):
        stmt = select(Infraction).where(
            Infraction.is_active == True,
            Infraction.expires_at < datetime.utcnow(),
        )
        result = await self.session.execute(stmt)
        expired = result.scalars().all()
        for inf in expired:
            inf.is_active = False
        await self.session.commit()
        return expired


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        chat_id: int,
        ttype: TransactionType,
        amount: int,
        balance_after: int = 0,
        description: str | None = None,
    ) -> Transaction:
        tx = Transaction(
            user_id=user_id,
            chat_id=chat_id,
            type=ttype,
            amount=amount,
            balance_after=balance_after,
            description=description,
        )
        self.session.add(tx)
        await self.session.commit()
        return tx


class MessageLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        chat_id: int,
        user_id: int,
        message_id: int,
        content_type: str = "text",
        content_length: int = 0,
        has_link: bool = False,
        has_media: bool = False,
    ):
        try:
            log = MessageLog(
                chat_id=chat_id,
                user_id=user_id,
                message_id=message_id,
                content_type=content_type,
                content_length=content_length,
                has_link=has_link,
                has_media=has_media,
            )
            self.session.add(log)
            await self.session.commit()
        except Exception as exc:
            logger.warning(f"Failed to log message (chat={chat_id}, msg_id={message_id}): {exc}")
            await self.session.rollback()

    async def count_today(self, chat_id: int, user_id: int) -> int:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        stmt = (
            select(func.count(MessageLog.id))
            .where(
                MessageLog.chat_id == chat_id,
                MessageLog.user_id == user_id,
                func.date(MessageLog.created_at) == today,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_recent(
        self, chat_id: int, user_id: int, seconds: int = 5
    ) -> int:
        since = datetime.utcnow() - timedelta(seconds=seconds)
        stmt = (
            select(func.count(MessageLog.id))
            .where(
                MessageLog.chat_id == chat_id,
                MessageLog.user_id == user_id,
                MessageLog.created_at >= since,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_recent_message_ids(self, chat_id: int, limit: int = 10, exclude_ids: set[int] | None = None) -> list[int]:
        stmt = (
            select(MessageLog.message_id)
            .where(MessageLog.chat_id == chat_id)
            .order_by(MessageLog.id.desc())
            .limit(min(limit, 100))
        )
        result = await self.session.execute(stmt)
        ids = [row[0] for row in result.all()]
        if exclude_ids:
            ids = [mid for mid in ids if mid not in exclude_ids]
        return ids

    async def delete_by_message_ids(self, chat_id: int, message_ids: list[int]) -> int:
        stmt = delete(MessageLog).where(
            MessageLog.chat_id == chat_id,
            MessageLog.message_id.in_(message_ids),
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


class FilterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active(self, chat_id: int) -> list[Filter]:
        stmt = select(Filter).where(
            Filter.chat_id == chat_id, Filter.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add(
        self, chat_id: int, pattern: str, filter_type: str = "word", action: str = "delete"
    ) -> Filter:
        f = Filter(chat_id=chat_id, pattern=pattern, filter_type=filter_type, action=action)
        self.session.add(f)
        await self.session.commit()
        return f

    async def remove(self, filter_id: int):
        f = await self.session.get(Filter, filter_id)
        if f:
            f.is_active = False
            await self.session.commit()


class DailyStatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def increment(self, chat_id: int, field: str, amount: int = 1):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        stmt = select(DailyStats).where(
            DailyStats.chat_id == chat_id, DailyStats.date == today
        )
        result = await self.session.execute(stmt)
        stats = result.scalar_one_or_none()
        if not stats:
            stats = DailyStats(chat_id=chat_id, date=today)
            self.session.add(stats)
        if hasattr(stats, field):
            setattr(stats, field, getattr(stats, field) + amount)
        await self.session.commit()

    async def get_range(self, chat_id: int, days: int = 7) -> list[DailyStats]:
        since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        stmt = (
            select(DailyStats)
            .where(DailyStats.chat_id == chat_id, DailyStats.date >= since)
            .order_by(DailyStats.date)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, chat_id: int, user_id: int, message_id: int, topic: str, content: str, message_link: str | None = None, tags: str | None = None) -> KnowledgeEntry:
        entry = KnowledgeEntry(
            chat_id=chat_id, user_id=user_id, message_id=message_id,
            topic=topic, content=content, message_link=message_link, tags=tags,
        )
        self.session.add(entry)
        await self.session.commit()
        return entry

    async def search(self, chat_id: int, query: str) -> list[KnowledgeEntry]:
        stmt = select(KnowledgeEntry).where(
            KnowledgeEntry.chat_id == chat_id,
            KnowledgeEntry.topic.ilike(f"%{query}%"),
        ).order_by(KnowledgeEntry.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ScheduledJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_due(self) -> list[ScheduledJob]:
        stmt = select(ScheduledJob).where(ScheduledJob.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()
