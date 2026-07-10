from __future__ import annotations

from telegram import Update, ChatPermissions, ChatMember as TGChatMember
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, MessageHandler, filters

from src.core.permissions import Permission, has_permission, can_moderate_target
from src.database.models import UserRole, InfractionType
from src.database.repository import (
    ChatMemberRepository,
    InfractionRepository,
    ChatRepository,
)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    member = await chat.get_member(user.id)
    return member.status in (TGChatMember.ADMINISTRATOR, TGChatMember.OWNER)


async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not await is_admin(update, context):
        await update.message.reply_text("⚠️ هذه الأوامر خاصة بالمشرفين فقط.")
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
        await update.message.reply_text("❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر حظر.")
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
        await update.message.reply_text("⚠️ ما قدرت أحظر العضو، تأكد أني مشرف وعندي صلاحيات.")


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر كيك.")
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
        await update.message.reply_text("⚠️ ما قدرت أطرد العضو، تأكد أني مشرف وعندي صلاحيات.")


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر اسكت.")
        return

    target_id, target_name = target
    chat = update.effective_chat
    bot = context.bot

    try:
        bot_member = await chat.get_member(bot.id)
        bot_self = await bot.get_me()
        if target_id == bot_self.id:
            await update.message.reply_text("❌ ما أقدر أسوي كذا على نفسي!")
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
        await update.message.reply_text("⚠️ ما قدرت أكتم العضو، تأكد أني مشرف وعندي صلاحيات.")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    target = await get_target_user(update)
    if not target:
        await update.message.reply_text("❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر فك اسكت.")
        return

    target_id, target_name = target
    chat = update.effective_chat

    try:
        bot_self = await context.bot.get_me()
        if target_id == bot_self.id:
            await update.message.reply_text("❌ ما أقدر أسوي كذا على نفسي!")
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
        await update.message.reply_text("⚠️ ما قدرت أفك الكتم، تأكد أني مشرف وعندي صلاحيات.")


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update, context):
        return
    menu = (
        "🛡️ **أوامر الأدمن في فنوع:**\n"
        "- ارفض (رد على رسالة) -> يحظر مؤقتاً أو يبند حسب الحاجة\n"
        "- كيك (رد على رسالة) -> يطرد العضو من الجروب\n"
        "- اسكت (رد على رسالة) -> يكتم العضو 60 ثانية\n"
        "- فك اسكت (رد على رسالة) -> يفك الكتم عن العضو\n"
        "- حظر (رد على رسالة أو @username) -> يمنع العضو من الجروب\n"
        "- رفع صوتي -> يرفع صوت البوت ويشير إنه شغال\n"
        "- تنزيل صوتي -> يوقف صوت البوت ويشير إنه هادي\n"
    )
    await update.message.reply_text(menu, parse_mode=ParseMode.MARKDOWN)


async def رفع_صوتي(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await admin_only(update, context):
        await update.message.reply_text("🔊 تم تفعيل وضع الزعلان، البوت جاهز وأعلى صوت!")


async def تنزيل_صوتي(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await admin_only(update, context):
        await update.message.reply_text("🤫 تم تفعيل وضع الهدوء، البوت سيصبح خفيف وهادي.")


def get_admin_handlers() -> list:
    return [
        MessageHandler(filters.Text("قائمة الأدمن"), admin_menu),
        MessageHandler(filters.Regex(r"^حظر"), ban),
        MessageHandler(filters.Regex(r"^(طرد|كيك)"), kick),
        MessageHandler(filters.Regex(r"^اسكت"), mute),
        MessageHandler(filters.Regex(r"^فك اسكت"), unmute),
        MessageHandler(filters.Text(["رفع صوتي"]), رفع_صوتي),
        MessageHandler(filters.Text(["تنزيل صوتي"]), تنزيل_صوتي),
    ]
