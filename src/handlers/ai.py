from __future__ import annotations

import json

import httpx
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

from src.config import settings

SYSTEM_PROMPT = (
    "أنت بوت تلغرام اسمك 'فنوع'. تتحدث باللهجة الفلسطينية العامية. "
    "أنت فرفوش، محبوب، مضحك، وطبطاب. ردودك قصيرة ومختصرة (جملة أو جملتين)"
)


async def ask_gemini(history: list[dict]) -> str:
    if not settings.gemini_api_key:
        return "ما في مفتاح AI، حط GEMINI_API_KEY في .env 🧠"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={settings.gemini_api_key}"
    )
    payload = {"contents": history}
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.post(url, json=payload)
            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            return text or "مخي طفى هالدقيقة، اسألني بعد شوي 🧠🤖"
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            return "سيرفر الذكاء نايم حالياً، خلنا نلعب أحسن 😴"


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    question = text.replace("يا فنوع", "").replace("فنوع", "").strip()
    if not question:
        await update.message.reply_text(
            "لبيه! ناديتني؟ اسألني أي شيء وبجاوبك، مثلاً: (يا فنوع عطني نصيحة مضحكة) 🤖"
        )
        return

    await context.bot.send_chat_action(update.effective_chat.id, "typing")

    chat_id = str(update.effective_chat.id)
    bot_data = context.bot_data.setdefault("gemini_memory", {})
    history = bot_data.get(chat_id, [])
    history.append({"role": "user", "parts": [{"text": question}]})

    full_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
    full_history.extend(history[-20:])

    reply = await ask_gemini(full_history)

    history.append({"role": "model", "parts": [{"text": reply}]})
    bot_data[chat_id] = history[-30:]

    await update.message.reply_text(reply)


def get_ai_handlers() -> list:
    return [
        MessageHandler(filters.Regex(r"^(يا فنوع |فنوع )"), ai_chat),
    ]
