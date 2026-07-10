from __future__ import annotations

import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters


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
                    "قمت بإضافة البوت كعضو في المجموعة! يجب رفعه مشرفاً لكي يتم تفعيله ويحميك.\n\n"
                    "اضغط على الزر بالأسفل لرفعي مشرفاً بالصلاحيات المطلوبة فوراً وجاهزة 👇"
                )
                await update.message.reply_text(warning, reply_markup=markup, parse_mode="Markdown")
                await chat.leave()
                return
            else:
                await update.message.reply_text(
                    "🥳 كفو! تم تفعيل البوت فنوع بنجاح كـ مشرف بالجروب! "
                    "اكتب 'الألعاب' وخلنا نفلها! 🔥"
                )
                return
        else:
            await _welcome_user(update, context, new_user)


async def _welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE, new_user) -> None:
    try:
        photos = await context.bot.get_user_profile_photos(new_user.id, limit=1)
        has_photo = photos and photos.total_count > 0
    except:
        has_photo = False

    name = new_user.first_name
    captions = [
        f"🎉🎉🎉 يا هلا وسهلا بـ {name} 🌟\nنورت الجروب يا صديق، والله كنا ننتظرك! 🔥\nاكتب **'تم'** وابدا المغامرة معانا 💪",
        f"🤩 القمر {name} انضم لنا أخيراً!\nنورت ونورت الدنيا كلها 🫶✨\nجرب تكتب **'تم'** عشان تبدأ تجمع نقاط وترتفع رتبتك! 🏆",
        f"🥳🥳 مبروك انضمام {name} لأطيب وأحلى جروب!\nنورت والله، فرحتنا ما تكتمل إلا بوجودك 🫶🔥\nلا تنسى تكتب **'تم'** وتبدأ المشوار 💯🚀",
        f"💥 انفجار ترحيبي بـ {name}!\nيا هلا بيك والله، الجروب منور بوجودك 🌞\nاكتب **'تم'** وخلنا ننطلق مع بعض نحو القمة 🚀🔥",
        f"🌟 **{name}** نور الجروب اليوم!\nأنت العضو المنتظر والله! استعد لأجواء المرح والألعاب والنكت 🎮🤣\nأول خطوة: اكتب **'تم'** 💪",
    ]
    texts = [
        f"🎯 يا هلا وغلا بـ {name} نورت جروبنا السعيد! ✨\nاكتب كلمة **'تم'** وسولف معنا عشان تجمع نقاط وتأخذ ألقاب فخمة! 🔥",
        f"🤗 {name} انضم للعيلة! نورت يا غالي 💎\nاكتب **'تم'** وابدأ الرحلة معانا في عالم المرح! 🚀",
        f"🎊 {name} نور الجروب وأضاف للبهجة! يا مرحبا مليون 💫\nجرب **'تم'** وشوف المفاجآت اللي في انتظارك 🎁🎉",
        f"👋 عضونا الجديد {name} انضم!\nنورت يا صديق، استعد لمتعة وتحديات لا تنتهي ⚡\nأول كلمة: **'تم'** وتنطلق 🏃‍♂️🔥",
        f"💫 منور يا {name}! الجروب فرحان بانضمامك\nكلنا هنا صحبة وأحباب ومتعة بلا حدود 🫂\nقول **'تم'** وخلنا نتعرف عليك أكثر 😍",
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
