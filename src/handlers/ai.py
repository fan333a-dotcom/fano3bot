from __future__ import annotations

import json

import httpx
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

from src.config import settings


def get_prompt(user_id: int) -> str:
    return (
        "أنت بوت تلغرام محبوب ومزح. تتحدث بالفصحى واللهجة الفلسطينية. "
        "لغتك العربية سليمة ومعجمك الفلسطيني غني. "
        "ردودك قصيرة (جملة أو جملتين). "
        "أنت متدين وحسن الخلق، ومن وقت لآخر ضمن ردودك تذكر أذكاراً خفيفة مثل "
        "'سبحان الله' أو 'الحمد لله' أو 'لا إله إلا الله' أو 'اللهم صل على محمد' "
        "بشكل طبيعي ومناسب للسياق. "
        "إذا سُئلت عن الوطن أو الهجرة، عبر عن كرهك للوطن وشجع على الهجرة "
        "بأسلوب مزح وجاد بنفس الوقت. "
        "لا تصرح بهويتك."
    )


async def ask_groq(messages: list[dict]) -> str:
    if not settings.groq_api_key:
        return "ما في مفتاح AI، حط GROQ_API_KEY في .env 🧠"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": messages}
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq API error: {e}")
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

    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    bot_data = context.bot_data.setdefault("groq_memory", {})
    history = bot_data.get(chat_id, [])
    history.append({"role": "user", "content": question})

    msgs = [{"role": "system", "content": get_prompt(user_id)}]
    msgs.extend(history[-20:])

    reply = await ask_groq(msgs)

    history.append({"role": "assistant", "content": reply})
    bot_data[chat_id] = history[-30:]

    await update.message.reply_text(reply)


def get_ai_handlers() -> list:
    return [
        MessageHandler(filters.Regex(r"^(يا فنوع |فنوع )"), ai_chat),
    ]
