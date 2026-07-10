from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram.ext import Application, ApplicationBuilder, MessageHandler, filters
from loguru import logger
from fastapi import FastAPI  # استيراد FastAPI المدمج لديك
import uvicorn

from src.config import settings
from src.utils.logger import setup_logger
from src.database.engine import init_db
from src.handlers.games import get_game_handlers
from src.handlers.admin import get_admin_handlers
from src.handlers.misc import get_misc_handlers
from src.handlers.ai import get_ai_handlers
from src.handlers.welcome import get_welcome_handlers
from src.handlers.azkar import get_azkar_handlers
# from src.handlers.youtube import get_youtube_handlers
from src.protection.anti_spam import protection_service
from src.analytics.tracker import analytics_tracker
from src.scheduler.tasks import scheduler_service
from src.database.repository import ChatMemberRepository, MessageLogRepository


# --- إعداد تطبيق FastAPI من أجل Render ---
web_app = FastAPI()

@web_app.get("/")
async def home():
    return {"status": "Fanou3 Bot is alive and running via FastAPI!"}
# ------------------------------------------

async def protection_middleware(update, context):
    if not update.message or not update.message.text:
        return True
    result = await protection_service.check_message(update, context)
    if not result:
        if update.message:
            try:
                await update.message.delete()
            except:
                pass
        return False
    return True


async def handle_message(update, context):
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text.strip() if update.message.text else ""

    from src.database.engine import async_session_factory
    from src.database.repository import UserRepository, ChatRepository

    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        chat_repo = ChatRepository(session)
        member_repo = ChatMemberRepository(session)
        msg_repo = MessageLogRepository(session)

        await user_repo.get_or_create(user.id, user.first_name, user.last_name, user.username)
        await chat_repo.get_or_create(chat.id, chat.title, chat.type)

        content_type = "text"
        if update.message.photo:
            content_type = "photo"
        elif update.message.video:
            content_type = "video"
        elif update.message.animation:
            content_type = "animation"
        elif update.message.document:
            content_type = "document"
        elif update.message.sticker:
            content_type = "sticker"

        analytics_tracker.track_message(chat.id, user.id, text, content_type)

        try:
            await msg_repo.log(
                chat_id=chat.id, user_id=user.id, message_id=update.message.message_id,
                content_type=content_type, content_length=len(text),
                has_link="http" in text.lower() or "t.me/" in text.lower(),
                has_media=content_type != "text",
            )
        except Exception as e:
            logger.debug(f"Failed to log message: {e}")
            await session.rollback()

        if text and not text.startswith("/"):
            member = await member_repo.add_points(user.id, chat.id)
            milestones = {15: "🌟", 50: "🎤", 150: "🔥", 300: "👑", 500: "💎", 1000: "🏆"}
            rank_names = {
                15: "بطل الجروب الناشئ", 50: "سفير المرح", 150: "نجم الدردشة الأول",
                300: "وزير السوالف", 500: "أسطورة الجروب", 1000: "ملك التحدي 👑",
            }
            if member.points in milestones:
                await update.message.reply_text(
                    f"🎊🎊🎊 **مبروووك {user.first_name} !!!** 🎊🎊🎊\n"
                    f"تخطيت حاجز **{member.points} نقطة** وصار لقبك: **{rank_names.get(member.points, 'عملاق التفاعل 💪')}**\n"
                    f"الجروب كله يفتخر فيك والله! استمر يابطل 🔥🔥🔥",
                    parse_mode="Markdown",
                )


async def error_handler(update, context):
    logger.error(f"Update {update} caused error: {context.error}")


async def post_init(application: Application):
    await init_db()
    scheduler_service.set_bot(application.bot)
    await scheduler_service.start()
    logger.info("Fanou3 Bot initialized successfully")


async def post_stop(application: Application):
    await scheduler_service.stop()
    logger.info("Fanou3 Bot stopped")


def build_application() -> Application:
    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(post_init)
        .post_stop(post_stop)
        .build()
    )

    application.add_error_handler(error_handler)

    async def message_logger(update, context):
        await handle_message(update, context)
        if update.message and update.effective_chat:
            recent = context.bot_data.setdefault("recent_msgs", {}).setdefault(
                update.effective_chat.id, []
            )
            recent.append(update.message.message_id)
            if len(recent) > 200:
                recent[:] = recent[-100:]

    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, message_logger, block=False),
        group=-1,
    )

    other_handlers = []
    other_handlers.extend(get_welcome_handlers())
    other_handlers.extend(get_admin_handlers())
    other_handlers.extend(get_game_handlers())
    other_handlers.extend(get_ai_handlers())
    other_handlers.extend(get_azkar_handlers())
    other_handlers.extend(get_misc_handlers())

    for handler in other_handlers:
        application.add_handler(handler)

    return application


async def main():
    setup_logger()
    logger.info("🚀 Starting Fanou3 Bot...")
    
    application = build_application()

    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=["message", "chat_member", "my_chat_member"],
    )

    logger.info("Bot is running. Setting up FastAPI web server...")

    # تشغيل سيرفر Uvicorn بداخل نفس الـ Event Loop الخاص بـ Asyncio
    # هذا يضمن تشغيل السيرفر وتجاوز فحص Render بنجاح دون التأثير على البوت
    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(app=web_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Shutting down...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())