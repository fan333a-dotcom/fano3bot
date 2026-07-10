from __future__ import annotations

import random

import httpx
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from src.config import settings


async def ask_ai(question_text: str) -> str:
    try:
        prompt = (
            f"أنت بوت تلغرام اسمك 'فنوع'. أنت فرفوش، محبوب، ومضحك "
            f"وتتحدث بالعامية العربية الطريفة جداً. رد باختصار وبطرافة على هذا السؤال: {question_text}"
        )
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.ai_api_url}/{prompt}")
            if response.status_code == 200:
                return response.text
            return "والله يا صاحبي مخي معلق هالدقيقة، اسألني بعد شوي! 🧠🤖"
    except:
        return "سيرفرات الذكاء الاصطناعي نايمة حالياً، خلنا نلعب أفضل! 😴"


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    question = text.replace("يا فنوع", "").replace("فنوع", "").strip()
    if not question:
        await update.message.reply_text(
            "لبيه! ناديتني؟ اسألني أي شيء وبجاوبك، مثلاً: (يا فنوع عطني نصيحة مضحكة) 🤖"
        )
        return

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    ai_reply = await ask_ai(question)
    await update.message.reply_text(ai_reply)


def get_ai_handlers() -> list:
    return [
        MessageHandler(filters.Regex(r"^(يا فنوع |فنوع )"), ai_chat),
    ]
