from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------- Enums ----------


class UserRole(str, enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    MODERATOR = "moderator"
    HELPER = "helper"
    VIP = "vip"
    TRUSTED = "trusted"
    MEMBER = "member"
    MUTED = "muted"
    BLACKLISTED = "blacklisted"


class InfractionType(str, enum.Enum):
    WARNING = "warning"
    MUTE = "mute"
    BAN = "ban"
    KICK = "kick"


class TransactionType(str, enum.Enum):
    REWARD = "reward"
    TRANSFER = "transfer"
    PURCHASE = "purchase"
    STEAL = "steal"
    INVESTMENT = "investment"
    SALARY = "salary"
    TAX = "tax"
    BET = "bet"
    WHEEL = "wheel"


class AchievementType(str, enum.Enum):
    FIRST_MESSAGE = "first_message"
    TALKATIVE = "talkative"
    HELPER = "helper"
    STREAK_7 = "streak_7"
    STREAK_30 = "streak_30"
    GAMER = "gamer"
    RICH = "rich"
    SOCIAL = "social"
    SURVIVOR = "survivor"
    LEGENDARY = "legendary"


# ---------- Users & Chats ----------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(128), default="")
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    memberships: Mapped[list[ChatMember]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list[UserAchievement]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    type: Mapped[str] = mapped_column(String(32), default="supergroup")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    protection_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    games_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    economy_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    welcome_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list[ChatMember]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )
    infractions: Mapped[list[Infraction]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )
    knowledge_entries: Mapped[list[KnowledgeEntry]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )
    scheduled_jobs: Mapped[list[ScheduledJob]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMember(Base):
    __tablename__ = "chat_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.MEMBER
    )

    # Points & XP
    points: Mapped[int] = mapped_column(Integer, default=0)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    coins: Mapped[int] = mapped_column(Integer, default=100)

    # Reputation
    reputation: Mapped[float] = mapped_column(Float, default=0.0)
    thanks_received: Mapped[int] = mapped_column(Integer, default=0)
    times_helped: Mapped[int] = mapped_column(Integer, default=0)

    # Streak
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )

    # Warnings
    warnings: Mapped[int] = mapped_column(Integer, default=0)

    # Stats
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_links: Mapped[int] = mapped_column(Integer, default=0)
    total_media: Mapped[int] = mapped_column(Integer, default=0)
    total_games_played: Mapped[int] = mapped_column(Integer, default=0)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", name="uq_user_chat"),
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    chat: Mapped[Chat] = relationship(back_populates="members")


# ---------- Economy ----------


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount: Mapped[int] = mapped_column(Integer, default=0)
    balance_after: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="transactions")


# ---------- Achievements ----------


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[AchievementType] = mapped_column(
        Enum(AchievementType), unique=True
    )
    name_ar: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    description_ar: Mapped[str] = mapped_column(String(256))
    description_en: Mapped[str] = mapped_column(String(256))
    icon: Mapped[str] = mapped_column(String(8), default="🏆")
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    coin_reward: Mapped[int] = mapped_column(Integer, default=0)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    achievement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("achievements.id")
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="achievements")


# ---------- Moderation ----------


class Infraction(Base):
    __tablename__ = "infractions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    moderator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[InfractionType] = mapped_column(Enum(InfractionType))
    reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    chat: Mapped[Chat] = relationship(back_populates="infractions")


# ---------- Protection Filters ----------


class Filter(Base):
    __tablename__ = "filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pattern: Mapped[str] = mapped_column(String(512))
    filter_type: Mapped[str] = mapped_column(
        String(32), default="word"
    )  # word, regex, link, spam
    action: Mapped[str] = mapped_column(
        String(32), default="delete"
    )  # delete, warn, mute, ban
    warn_count: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------- Knowledge Base ----------


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    topic: Mapped[str] = mapped_column(String(256), index=True)
    content: Mapped[str] = mapped_column(Text)
    message_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chat: Mapped[Chat] = relationship(back_populates="knowledge_entries")


# ---------- Scheduled Jobs ----------


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"))
    job_type: Mapped[str] = mapped_column(
        String(32)
    )  # activity, riddle, quiz, reminder, summary
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chat: Mapped[Chat] = relationship(back_populates="scheduled_jobs")


# ---------- Analytics ----------


class MessageLog(Base):
    __tablename__ = "message_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), default="text")
    content_length: Mapped[int] = mapped_column(Integer, default=0)
    has_link: Mapped[bool] = mapped_column(Boolean, default=False)
    has_media: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_new_members: Mapped[int] = mapped_column(Integer, default=0)
    total_left_members: Mapped[int] = mapped_column(Integer, default=0)
    total_bans: Mapped[int] = mapped_column(Integer, default=0)
    total_warnings: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("chat_id", "date", name="uq_chat_date"),
    )
