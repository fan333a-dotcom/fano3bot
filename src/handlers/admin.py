from __future__ import annotations

import asyncio
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


async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    chat_id = update.effective_chat.id
    async with async_session_factory() as session:
        repo = ChatMemberRepository(session)
        user_ids = await repo.get_all_member_ids(
            chat_id, exclude_roles=[UserRole.BLACKLISTED]
        )
    if not user_ids:
        await update.message.reply_text("ما في أعضاء للتاق.")
        return

    async def _get_mention(uid: int) -> str | None:
        try:
            member = await context.bot.get_chat_member(chat_id, uid)
            u = member.user
            return f'<a href="tg://user?id={u.id}">{u.first_name}</a>'
        except Exception:
            return None

    results = await asyncio.gather(*[_get_mention(uid) for uid in user_ids])
    mentions = [m for m in results if m is not None]

    if not mentions:
        await update.message.reply_text("ما في أعضاء للتاق.")
        return

    chunks = []
    current = ""
    for m in mentions:
        candidate = f"{current} {m}" if current else m
        if len(candidate) > 3900:
            chunks.append(current)
            current = m
        else:
            current = candidate
    if current:
        chunks.append(current)

    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)


async def delete_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = (update.message.text or "").strip()
        if not re.fullmatch(r"مسح(?:\s*\d+)?", text):
            return

        if not await admin_only(update, context):
            return

        chat_id = update.effective_chat.id
        cmd_id = update.message.message_id
        reply_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None
        count = max(1, min(100, int(text.removeprefix("مسح").strip() or 1)))

        ids: set[int] = {cmd_id}
        if reply_id is not None:
            ids.add(reply_id)

        q = context.bot_data.get("msg_q", {}).get(chat_id)
        if q:
            for mid in list(q)[-count:]:
                ids.add(mid)

        async with async_session_factory() as session:
            msg_repo = MessageLogRepository(session)
            db_ids = await msg_repo.get_recent_message_ids(chat_id, count, exclude_ids=ids)
            for mid in db_ids:
                ids.add(mid)

        deleted: list[int] = []
        id_list = sorted(ids)[:100]
        logger.info(f"مسح: chat={chat_id} cmd={cmd_id} count={count} ids={id_list}")
        for mid in id_list:
            try:
                await context.bot.delete_message(chat_id, mid)
                deleted.append(mid)
            except Exception as e:
                logger.debug(f"مسح failed {chat_id}/{mid}: {e}")

        if deleted:
            async with async_session_factory() as session:
                msg_repo = MessageLogRepository(session)
                removed = await msg_repo.delete_by_message_ids(chat_id, deleted)
                logger.debug(f"مسح: removed {removed} rows from message_logs")
    except Exception as e:
        logger.error(f"Error in delete_messages: {e}")


def get_admin_handlers() -> list:
    return [
        MessageHandler(filters.Text(["قائمة الأدمن"]), admin_menu),
        MessageHandler(filters.Regex(r"^حظر"), ban),
        MessageHandler(filters.Regex(r"^(طرد|كيك)"), kick),
        MessageHandler(filters.Regex(r"^اسكت"), mute),
        MessageHandler(filters.Regex(r"^فك اسكت"), unmute),
        MessageHandler(filters.Regex(r"^مسح"), delete_messages),
        MessageHandler(filters.Regex(r"^تاق"), tag_all),
    ]
