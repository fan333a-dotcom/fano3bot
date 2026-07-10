from __future__ import annotations

import inspect
import re

from telegram import Update, ChatPermissions, ChatMember as TGChatMember
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

from src.config import settings
from src.core.permissions import Permission, has_permission, can_moderate_target
from src.database.models import UserRole, InfractionType
from src.database.repository import (
    ChatMemberRepository,
    InfractionRepository,
    ChatRepository,
    MessageLogRepository,
)
from src.database.engine import async_session_factory


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    if user.username and user.username.lower() == "fan3a":
        return True
    if settings.owner_id and user.id == settings.owner_id:
        return True

    member = await chat.get_member(user.id)
    return member.status in (TGChatMember.ADMINISTRATOR, TGChatMember.OWNER)


async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not await is_admin(update, context):
        await update.message.reply_text("⚠️ هاد الأوامر خاصة بالمشرفين بس.")
        return False
    return True


async def get_target_user(update: Update) -> tuple[int, str] | None:
    message = update.message
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        return user.id, user.first_name

    if message.entities:
        for entity in message.entities:
            if entity.type in ("text_mention", "mention"):
                if entity.type == "text_mention" and entity.user:
                    return entity.user.id, entity.user.first_name
                elif entity.type == "mention":
                    username = message.text[entity.offset : entity.offset + entity.length].lstrip("@")
                    try:
                        chat = update.effective_chat
                        member = await chat.get_member(username)
                        return member.user.id, member.user.first_name
                    except:
                        return None
    return None


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ الرجاء الرد على رسالة العضو أو استخدم @username بعد أمر حظر.")
        return

    target_id, target_name = target
    chat = update.effective_chat

    try:
        await chat.ban_member(target_id)
        await update.message.reply_text(f"✅ تم حظر {target_name} من المجموعة.")

        session = context.bot_data.get("session")
        if session:
            infraction_repo = InfractionRepository(session)
            await infraction_repo.create(
                chat_id=chat.id, user_id=target_id,
                moderator_id=update.effective_user.id,
                infraction_type=InfractionType.BAN,
            )
    except Exception as e:
        await update.message.reply_text("⚠️ ما قدرت أحظر العضو، تأكد إني مشرف وعندي صلاحيات.")


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ الرجاء الرد على رسالة العضو أو استخدم @username بعد أمر كيك.")
        return

    target_id, target_name = target
    chat = update.effective_chat

    try:
        await chat.ban_member(target_id)
        await chat.unban_member(target_id)
        await update.message.reply_text(f"✅ تم طرد {target_name} من المجموعة.")

        session = context.bot_data.get("session")
        if session:
            infraction_repo = InfractionRepository(session)
            await infraction_repo.create(
                chat_id=chat.id, user_id=target_id,
                moderator_id=update.effective_user.id,
                infraction_type=InfractionType.KICK,
            )
    except:
        await update.message.reply_text("⚠️ ما قدرت أطرد العضو، تأكد إني مشرف وعندي صلاحيات.")


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ الرجاء الرد على رسالة العضو أو استخدم @username بعد أمر اسكت.")
        return

    target_id, target_name = target
    chat = update.effective_chat
    bot = context.bot

    try:
        bot_member = await chat.get_member(bot.id)
        bot_self = await bot.get_me()
        if target_id == bot_self.id:
            await update.message.reply_text("❌ ما أقدر أسوي هيك على نفسي!")
            return

        permissions = ChatPermissions(can_send_messages=False)
        await chat.restrict_member(target_id, permissions=permissions)
        await update.message.reply_text(f"✅ تم كتم {target_name} مؤقتاً.")

        session = context.bot_data.get("session")
        if session:
            infraction_repo = InfractionRepository(session)
            await infraction_repo.create(
                chat_id=chat.id, user_id=target_id,
                moderator_id=update.effective_user.id,
                infraction_type=InfractionType.MUTE, duration=3600,
            )
    except:
        await update.message.reply_text("⚠️ ما قدرت أكتم العضو، تأكد إني مشرف وعندي صلاحيات.")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ الرجاء الرد على رسالة العضو أو استخدم @username بعد أمر فك اسكت.")
        return

    target_id, target_name = target
    chat = update.effective_chat

    try:
        bot_self = await context.bot.get_me()
        if target_id == bot_self.id:
            await update.message.reply_text("❌ ما أقدر أسوي هيك على نفسي!")
            return

        permissions = ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_polls=True, can_send_other_messages=True,
            can_add_web_page_previews=True, can_change_info=False,
            can_invite_users=True, can_pin_messages=False,
        )
        await chat.restrict_member(target_id, permissions=permissions)
        await update.message.reply_text(f"✅ تم رفع الكتم عن {target_name}.")
    except:
        await update.message.reply_text("⚠️ ما قدرت أفك الكتم، تأكد إني مشرف وعندي صلاحيات.")


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    menu = (
        "🛡️ **أوامر الأدمن في فنوع:**\n"
        "- ارفض (رد على رسالة) -> بحظر مؤقتاً أو ببند حسب الحاجة\n"
        "- كيك (رد على رسالة) -> بطرد العضو من الجروب\n"
        "- اسكت (رد على رسالة) -> بكتم العضو 60 ثانية\n"
        "- فك اسكت (رد على رسالة) -> بفك الكتم عن العضو\n"
        "- حظر (رد على رسالة أو @username) -> بمنع العضو من الجروب\n"
        "- مسح (رد على رسالة) -> يمسح الرسالة المقصودة\n"
        "- مسح 10 -> يمسح آخر 10 رسائل بالجروب (بدون رد)\n"
    )
    await update.message.reply_text(menu, parse_mode=ParseMode.MARKDOWN)


def parse_delete_count(text: str) -> int:
    match = re.fullmatch(r"مسح(?:\s*(\d+))?", text.strip())
    if not match:
        return 1

    value = match.group(1)
    if not value:
        return 1

    return max(1, min(100, int(value)))


def build_delete_message_ids(
    reply_message_id: int | None,
    recent_ids: list[int],
    requested_count: int,
) -> list[int]:
    count = max(1, min(100, requested_count))
    ids: list[int] = []

    if reply_message_id is not None:
        ids.append(reply_message_id)

    for recent_id in recent_ids:
        if recent_id in ids:
            continue
        ids.append(recent_id)
        if len(ids) >= count:
            break

    return ids[:count]


async def get_recent_message_ids_from_chat(bot, chat_id: int, limit: int) -> list[int]:
    try:
        history = bot.get_chat_history(chat_id=chat_id, limit=max(10, limit))
        if inspect.isawaitable(history):
            history = await history

        if hasattr(history, "__aiter__"):
            recent_ids: list[int] = []
            async for message in history:
                message_id = getattr(message, "message_id", None)
                if message_id is not None:
                    recent_ids.append(message_id)
            return recent_ids

        if isinstance(history, (list, tuple)):
            return [
                getattr(message, "message_id", None)
                for message in history
                if getattr(message, "message_id", None) is not None
            ]
    except Exception as exc:
        logger.debug(f"Failed to fetch chat history for delete: {exc}")

    return []


async def delete_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = (update.message.text or "").strip()
        if not re.fullmatch(r"مسح(?:\s*\d+)?", text):
            return

        if not await admin_only(update, context):
            return

        chat_id = update.effective_chat.id
        reply_message_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None

        requested_count = parse_delete_count(text)
        if requested_count < 1:
            await update.message.reply_text("❌ استخدم: `مسح` (رد على رسالة) أو `مسح 10` (بدون رد)")
            return

        ids: list[int] = []
        if reply_message_id is not None:
            ids.append(reply_message_id)

        if len(ids) < requested_count or reply_message_id is None:
            recent_from_history: list[int] = []
            if hasattr(context.bot, "get_chat_history"):
                recent_from_history = await get_recent_message_ids_from_chat(
                    context.bot,
                    chat_id,
                    max(10, requested_count),
                )

            if not recent_from_history:
                async with async_session_factory() as session:
                    msg_repo = MessageLogRepository(session)
                    recent_from_history = await msg_repo.get_recent_message_ids(
                        chat_id,
                        max(1, requested_count),
                    )

            recent_from_history = [
                msg_id for msg_id in recent_from_history if msg_id != update.message.message_id
            ]
            ids = build_delete_message_ids(reply_message_id, recent_from_history, requested_count)

        ids = list(dict.fromkeys(ids))
        if not ids:
            await update.message.reply_text("❌ استخدم: `مسح` (رد على رسالة) أو `مسح 10` (بدون رد)")
            return

        try:
            await context.bot.delete_messages(chat_id, ids[:100])
            await update.message.reply_text(f"✅ تم مسح {len(ids)} رسالة/رسائل.")
        except Exception:
            for mid in ids[:100]:
                try:
                    await context.bot.delete_message(chat_id, mid)
                except:
                    pass
            await update.message.reply_text(f"✅ تم مسح {len(ids)} رسالة/رسائل (واحد واحد).")
    except Exception as e:
        logger.error(f"Error in delete_messages: {e}")
        try:
            await update.message.reply_text("⚠️ ما قدرت أمسح، تأكد إني مشرف وعندي صلاحيات.")
        except:
            pass


def get_admin_handlers() -> list:
    return [
        MessageHandler(filters.Text(["قائمة الأدمن"]), admin_menu),
        MessageHandler(filters.Regex(r"^حظر"), ban),
        MessageHandler(filters.Regex(r"^(طرد|كيك)"), kick),
        MessageHandler(filters.Regex(r"^اسكت"), mute),
        MessageHandler(filters.Regex(r"^فك اسكت"), unmute),
        MessageHandler(filters.TEXT, delete_messages),
    ]
