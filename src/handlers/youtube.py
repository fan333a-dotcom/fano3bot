from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from src.config import settings


async def download_audio(query: str) -> str | None:
    output_dir = settings.data_dir / "youtube"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())[:8]
    output_template = str(output_dir / f"%(title)s_{file_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "noplaylist": True,
        "max_downloads": 1,
        "extract_flat": False,
        "ignoreerrors": True,
    }

    loop = asyncio.get_event_loop()

    def _sync_download():
        import io
        import sys as _sys
        old_stderr = _sys.stderr
        _sys.stderr = io.StringIO()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
        except Exception:
            return None
        finally:
            _sys.stderr = old_stderr

        if not info:
            return None
        if "entries" in info:
            if not info["entries"]:
                return None
            info = info["entries"][0]
        if not info:
            return None

        title = info.get("title", "Unknown")
        ext = info.get("ext", "m4a")

        expected = output_dir / f"{title}_{file_id}.{ext}"
        if expected.exists():
            return str(expected)

        for f in output_dir.glob(f"*{file_id}*"):
            if f.is_file():
                return str(f)

        actual_ext = info.get("requested_downloads", [{}])[0].get("ext", ext)
        for f in output_dir.glob(f"*{file_id}*"):
            if f.is_file():
                return str(f)

        return None

    try:
        filepath = await loop.run_in_executor(None, _sync_download)
        if filepath and os.path.exists(filepath):
            return filepath
        return None
    except Exception:
        return None


async def يوتيوب(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    query = text[3:].strip()

    if not query:
        await update.message.reply_text(
            "❌ اكتب اسم المقطع بعد الأمر يوت.\n"
            "مثال: `يوت سورة الفاتحة`",
            parse_mode="Markdown",
        )
        return

    msg = await update.message.reply_text(
        f"🔍 **جاري البحث عن:** `{query}`\n"
        f"⏳ يتم التحميل...",
        parse_mode="Markdown",
    )

    audio_path = await download_audio(query)

    if not audio_path or not os.path.exists(audio_path):
        await msg.edit_text(
            "❌ ما لقيت المقطع أو صار خطأ بالتحميل.\n"
            "تأكد من الاسم وحاول مرة ثانية.\n\n"
            "💡 بديل: ارسل رابط اليوتيوب مباشرة."
        )
        return

    try:
        title = Path(audio_path).stem.rsplit("_", 1)[0][:60] or "مقطع صوتي"
        with open(audio_path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title,
                performer="🎵 فنوع",
            )
        await msg.delete()
    except Exception:
        await msg.edit_text(
            "❌ صار خطأ أثناء رفع الملف. حاول مقطع أقصر."
        )
    finally:
        try:
            os.remove(audio_path)
        except Exception:
            pass


def get_youtube_handlers() -> list:
    return [
        MessageHandler(filters.Regex(r"^يوت\s"), يوتيوب),
    ]
