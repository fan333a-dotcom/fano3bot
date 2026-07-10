from __future__ import annotations

import re
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from src.config import settings

BAD_WORDS = [
    "كلب", "حمار", "غبي", "تفه", "منحط", "يا كلب", "يا حمار", "تيس", "يا تيس",
    "حيوان", "يا حيوان", "كلاب", "الحمار", "الكلب", "تفو", "قليل حيا",
]


class ProtectionService:
    def __init__(self):
        self._flood_count: dict[str, list[float]] = {}

    async def check_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        if not update.message or not update.message.text:
            return True

        text = update.message.text
        user = update.effective_user
        chat = update.effective_chat

        if not user or not chat:
            return True

        try:
            member = await chat.get_member(user.id)
            if member.status in ("administrator", "creator"):
                return True
        except:
            pass

        checks = [
            self._check_links,
            self._check_bad_words,
            self._check_flood,
            self._check_repeated_chars,
            self._check_max_length,
            self._check_spam_mentions,
        ]

        for check in checks:
            result = await check(update, context, text)
            if result is False:
                return False

        return True

    async def _check_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
        link_patterns = [r"http[s]?://", r"t\.me/", r"www\."]
        for pattern in link_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                try:
                    await update.message.delete()
                    await context.bot.send_message(
                        update.effective_chat.id,
                        f"⚠️ عذراً يا {update.effective_user.first_name}، الروابط ممنوعة هنا للحماية من الإعلانات! ⛔",
                    )
                    return False
                except:
                    pass
        return True

    async def _check_bad_words(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
        for word in BAD_WORDS:
            if word in text:
                try:
                    await update.message.delete()
                    await context.bot.send_message(
                        update.effective_chat.id,
                        f"🤫 أستغفر الله! يا {update.effective_user.first_name} جروبنا محترم وما نبي كلام يزعل الأعضاء! 🥛",
                    )
                    return False
                except:
                    pass
        return True

    async def _check_flood(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        key = f"{chat_id}:{user_id}"
        now = datetime.utcnow().timestamp()

        if key not in self._flood_count:
            self._flood_count[key] = []

        times = self._flood_count[key]
        times.append(now)
        times[:] = [t for t in times if now - t < settings.antiflood_window]

        if len(times) > settings.antiflood_max_messages:
            try:
                await update.message.delete()
            except:
                pass
            return False
        return True

    async def _check_repeated_chars(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
        for char in text:
            if char.isalpha() and char * settings.max_repeated_chars in text:
                try:
                    await update.message.delete()
                    return False
                except:
                    pass
        return True

    async def _check_max_length(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
        if len(text) > settings.max_message_length:
            try:
                await update.message.delete()
                return False
            except:
                pass
        return True

    async def _check_spam_mentions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
        mention_count = text.count("@")
        if mention_count > settings.max_mentions_per_message:
            try:
                await update.message.delete()
                return False
            except:
                pass
        return True


protection_service = ProtectionService()
