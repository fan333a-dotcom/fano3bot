from __future__ import annotations

import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

from src.database.engine import async_session_factory
from src.database.repository import ChatMemberRepository


async def _add_member(user_id: int, chat_id: int):
    try:
        async with async_session_factory() as session:
            repo = ChatMemberRepository(session)
            await repo.get_or_create(user_id, chat_id)
    except Exception as exc:
        logger.warning(f"Failed to add member {user_id} to chat_members: {exc}")


async def on_bot_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for new_user in update.message.new_chat_members:
        bot_self = await context.bot.get_me()

        if new_user.id == bot_self.id:
            chat = update.effective_chat
            bot_member = await chat.get_member(bot_self.id)

            if bot_member.status not in ("administrator", "creator"):
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="اضغط هنا لرفع فنوع مشرف 👑",
                        url=f"https://t.me/{bot_self.username}?startgroup=Commands"
                            f"&admin=ban_users+restrict_members+delete_messages"
                            f"+add_admins+change_info+invite_users+pin_messages",
                    )],
                ])
                warning = (
                    "⚠️ **تنبيه من البوت فنوع:**\n"
                    "ضفت البوت كعضو بالمجموعة! لازم ترفعني مشرف عشان اشتغل وأحميك.\n\n"
                    "اضغط على الزر بالأسفل لترفعني مشرفاً بالصلاحيات المطلوبة 👇"
                )
                await update.message.reply_text(warning, reply_markup=markup, parse_mode="Markdown")
                await chat.leave()
                return
            else:
                await update.message.reply_text(
                    "🥳 كفو! تم تفعيل البوت فنوع بنجاح كمشرف بالجروب! "
                    "اكتب 'الألعاب' وخلنا نفلها! 🔥"
                )
                return
        else:
            await _add_member(new_user.id, update.effective_chat.id)
            await _welcome_user(update, context, new_user)


async def _welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE, new_user) -> None:
    try:
        photos = await context.bot.get_user_profile_photos(new_user.id, limit=1)
        has_photo = photos and photos.total_count > 0
    except:
        has_photo = False

    name = new_user.first_name
    captions = [
        f"🎉🎉🎉 يا هلا وسهلا بـ {name} 🌟\nمنور الجروب يا صديق، والله كنا نستناك! 🔥\nاكتب **'تم'** وابدأ المغامرة معنا 💪",
        f"🤩 القمر {name} انضم إلنا أخيراً!\nمنور ومنورة الدنيا كلها 🫶✨\nجرب تكتب **'تم'** عشان تبدأ تجمع نقاط وترتفع رتبتك! 🏆",
        f"🥳🥳 مبروك انضمام {name} لأطيب وأحلى جروب!\nمنور والله، فرحتنا ما تكتمل إلا بوجودك 🫶🔥\nلا تنسى تكتب **'تم'** وتبدأ المشوار 💯🚀",
        f"💥 انفجار ترحيبي بـ {name}!\nيا هلا فيك والله، الجروب منور بوجودك 🌞\nاكتب **'تم'** وخلنا ننطلق مع بعض نحو القمة 🚀🔥",
        f"🌟 **{name}** نور الجروب اليوم!\nأنت العضو المنتظر والله! استعد لأجواء المرح والألعاب والنكت 🎮🤣\nأول خطوة: اكتب **'تم'** 💪",
    ]
    texts = [
        f"🎯 يا هلا وغلا بـ {name} منور جروبنا السعيد! ✨\nاكتب كلمة **'تم'** وسولف معنا عشان تجمع نقاط وتاخذ ألقاب فخمة! 🔥",
        f"🤗 {name} انضم للعيلة! منور يا غالي 💎\nاكتب **'تم'** وابدأ الرحلة معنا في عالم المرح! 🚀",
        f"🎊 {name} نور الجروب وأضاف للبهجة! يا مرحبا مليون 💫\nجرب **'تم'** وشوف المفاجآت اللي بنتظارك 🎁🎉",
        f"👋 عضونا الجديد {name} انضم!\nمنور يا صديق، استعد لمتعة وتحديات ما بتخلص ⚡\nأول كلمة: **'تم'** وتنطلق 🏃‍♂️🔥",
        f"💫 منور يا {name}! الجروب فرحان بانضمامك\nكلنا هون صحبة وأحباب ومتعة بلا حدود 🫂\nقول **'تم'** وخلنا نتعرف عليك أكثر 😍",
    ]

    if has_photo:
        file_id = photos.photos[0][0].file_id
        await update.message.reply_photo(
            file_id, caption=random.choice(captions), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(random.choice(texts))


def get_welcome_handlers() -> list:
    return [
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_join),
    ]
