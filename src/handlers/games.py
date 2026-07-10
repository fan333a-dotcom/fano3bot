from __future__ import annotations

import random

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from src.database.engine import async_session_factory
from src.database.repository import ChatMemberRepository

# ---------- Game Data ----------

قائمة_لو_خيروك = [
    "تاكل بصل ني 🧅 أو تاكل ليمونة كاملة بقشرها 🍋؟",
    "تعيش بدون جوال أسبوع 📱 أو بدون نت شهر 🌐؟",
    "تصير غني وتعيش لحالك 💰 أو على قد حالك ومعك ربعك 👥؟",
    "تسافر للمستقبل وتشوف نفسك 🚀 أو ترجع للماضي وتغير غلطة ⏳؟",
    "تختفي وتسمع شو بقولوا الناس عنك 👻 أو تقرأ أفكارهم بلمسة 🧠؟",
    "تعيش في غابة مع حيوانات أليفة 🦁 أو تعيش بقصر فخم لحالك 🏰؟",
    "تنام في مقبرة ليلة كاملة لحالك 🪦 أو تسبح مع قروش في البحر 🦈؟",
    "تخسر كل فلوسك هلأ 💸 أو تخسر كل ذكريات طفولتك 🧠؟",
    "تتكلم بصوت عالي طول عمرك 📢 أو تهمس همس طول عمرك 🤫؟",
    "تتحكم بالوقت (توقفه وترجعه) ⏳ أو تطير في السماء زي الصقر 🦅؟",
    "تاكل وجبة وحدة طول حياتك 🍔 أو كل يوم تاكل أكلة جديدة طعمها غريب 🤮؟",
    "تعيش بدون مكيف في الصيف 🥵 أو بدون دفاية في الشتاء 🥶؟",
    "تكون مشهور ومكروه من الناس 🎭 أو مجهول والكل يحبك إذا شافك 🤍؟",
    "تتخلى عن ذكائك وتصير سعيد ومفهي 🥴 أو تضل ذكي وحزين 🧠؟",
    "تاكل ملعقة شطة حارة جداً 🌶️ أو تشرب كاسة موية مالحة 🌊؟",
    "تمشي حافي على رمل حار 🥵 أو تمشي حافي على ثلج 🥶؟",
]

قائمة_كت_تويت = [
    "أكثر إشي بتكرهه بالشخص اللي قدامك؟ 🧐",
    "لو كان عندك قوة خارقة، شو بتختار تكون؟ 🦸‍♂️",
    "شو آخر مصيبة سويتها وجوالك طافي؟ 💀",
    "اعتراف خطير بدون ذكر أسماء؟ 🤫",
    "شخص بالجروب بدك تعطيه كف وتطلع؟ 😂 (بدون منشن)",
    "لو باقي يوم واحد بالعالم شو رح تسوي فيه؟ 🌍",
    "أكثر أكلة مستحيل تاكلها لو تموت جوع؟ 🤮",
    "هل تؤمن بالحب من أول نظرة، ولا السالفة كلها كذب؟ 👁️❤️",
    "لو فتحنا معرض لعيوبك، شو رح يكون المَعْروض الرئيسي؟ 🖼️",
    "شو الكلمة اللي لو حد قالها لك هلأ تبتسم تلقائياً؟ 😊",
    "إشي سويته بالماضي وكل ما تتذكره تحس بالندم أو الفشلة؟ 🤦‍♂️",
    "لو خيروك تسمي نفسك اسم جديد هلأ، شو رح تختار؟ 📝",
    "تفضل الصديق العاقل الزيادة، ولا الصديق الفاصل اللي يوديك بداهية؟ 🤣",
    "متى كانت آخر مرة بكيت فيها ومن قلب؟ 😢",
    "إشي غريب تحب تسويه لما تكون لحالك بالبيت؟ 🏠🍿",
    "لو حياتك عبارة عن فيلم، شو رح يكون تصنيفه (كوميدي، دراما، رعب)؟ 🎬",
]

قائمة_نكت = [
    "واحد شاف إشارة ممنوع الوقوف.. فكر حالو سيارة وقام انبطح! 🏛️😂",
    "واحد بخيل تزوج بخيلة.. جابوا ولد حطوه بالبنك عشان ما يصرفوش! 💰🤣",
    "نملة شافت عصير فراولة.. قالت: ياه أخيراً لقيت البحر الأحمر! 🐜🍓",
    "واحد ضاعت محفظتو راح يبلغ الشرطة، قالوا له: ولا يهمك روح البيت واحنا منحفرلك.. وهو راجع شاف عمال بلدية بيحفروا الشارع، صاح فيهم: كفووو لونها بني مش أسود! 💼😂",
    "واحد غبي راح يشتري عطر، سأله البائع: بدك بخاخ ولا عادي؟ قال: لا خلّي عصير باشربه هون! 🧴🤣",
    "ديك شاف بيضة مسلوقة، راح للدجاجة قالها: شو هاد؟ صرتو تحضروا حبوب منع حمل من وراي؟ 🐓😂",
    "أستاذ سأل طالب: أعطيني جملة فيها كلمة (سكر).. قال الطالب: شربت الشاي الصبح.. قال الأستاذ: وين السكر؟ قال: ذاب بالشاي يا أستاذ! ☕🤪",
    "واحد اتصل بالخطوط الجوية قالهم: قديش تستغرق الرحلة من هون لأمريكا؟ قالوا له: ثانية يا فندم.. قال: شكراً، وقفل! ✈️😭",
    "واحد دخل ماكدونالدز قالهم: عطوني فلافل، قالوا له: ما عندنا، قال: طيب شو هالصورة الكبيرة اللي حاطينها وفيها أنا لابس شماغ؟ (طلع شعار كنتاكي)! 🍗😂",
]

قائمة_فعاليات = [
    "🎯 فعالية هلأ: كل واحد يكتب اسم أكثر شخص يثق فيه بالجروب!",
    "🔮 فعالية هلأ: أرسل آخر إيموجي استخدمته بالواتساب بدون كذب!",
    "📱 فعالية هلأ: قديش نسبة شحن جوالك هلأ؟ اللي شحنه أقل من 20% يروح يشحن!",
    "📸 فعالية هلأ: أرسل أكثر صورة مضحكة (ميمز) موجودة باستديو جوالك!",
    "💬 فعالية هلأ: منشن لأكثر شخص يسولف بالجروب وقولو (خف علينا يا راديو) 🎙️",
    "🍽️ فعالية هلأ: شو كان أكلكم اليوم؟ اعترفوا بدون كذب 🥘",
    "💡 فعالية هلأ: اكتب كلمة (فنوع) وعطنا رأيك بالبوت بكل صراحة!",
    "⏰ فعالية هلأ: قديش ساعة بتقضيها على جوالك باليوم؟ 📱",
]

قائمة_صراحة = [
    "هل سبق وسرقت إشي بسيط من أغراض أخوانك؟ 👀",
    "مين الشخص اللي بالجروب وتتابع رسايله بصمت؟ 🤫",
    "شو أكبر كذبة كذبتها على أهلك ومشت عليهم؟ 🤥",
    "هل شكلك بالبطاقة الشخصية يفشل ولا حلو؟ 🪪😂",
    "لو شفت حبيبك القديم بالشارع بالصدفة، شو رح تسوي؟ 🏃‍♂️",
    "قديش رصيدك بالحساب البنكي هَلأ بدون خجل؟ 💵",
    "هل أنت شخص غيور بالعلاقات ولا عادي بارد؟ 🔥",
    "شو أكثر عيب دايماً الناس بلاحظوه بشخصيتك؟ 😕",
]

قائمة_أمثال = [
    "إذا كان الكلام من فضة فالسكوت من ذهب 🪙",
    "القرش الأبيض ينفع في اليوم الأسود 💵",
    "من حفر حفرة لأخيه وقع فيها 🕳️",
    "يا داخل بين البصلة وقشرتها ما ينوبك إلا ريحتها 🧅",
    "الذي بيته من زجاج لا يرمي الناس بالحجارة 🧱",
    "عصفور في اليد خير من عشرة على الشجرة 🐦",
    "القرعة تتباهى بشعر بنت أختها 👩‍🦲",
    "امش في جنازة ولا تمش في جوازة 🚶‍♂️",
]

قائمة_حزورة = [
    ("شيء له أسنان ولا يعض؟", "المشط 🪥"),
    ("شيء كلما أخذت منه يكبر؟", "الحفرة 🕳️"),
    ("شيء يطير بلا أجنحة ويسيل بلا أرجل؟", "الغيوم ☁️"),
    ("شيء له وجه ولا يتكلم؟", "الساعة ⏰"),
    ("شيء يمشي بلا رجلين ويبكي بلا عيون؟", "الغيمة ☁️"),
    ("شيء يموت إذا بللته بالماء؟", "النار 🔥"),
    ("بيت بلا أبواب ولا نوافذ؟", "بيت الشعر 🏠"),
    ("شيء يكون في الشتاء خمسة وفي الصيف ثلاثة؟", "النقط (حر/شمس) ☀️"),
    ("ما هو الشيء الذي يقرصك ولا تراه؟", "الجوع 🍔"),
    ("ما هو الشيء الذي كلما زاد نقص؟", "العمر 🎂"),
]


async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu = (
        "🎮 **قائمة ألعاب وفعاليات فنوع العملاقة:**\n"
        "(اكتب الكلمة مباشرة بدون فواصل أو رموز إنجليزية)\n\n"
        "🔹 **لو خيروك** -> خيارات صعبة ومحرجة 🤔\n"
        "🔹 **كت تويت** -> أسئلة لتحريك الشات والسوالف 💬\n"
        "🔹 **نكتة** -> أحدث وأقوى النكت التليجرامية 🤣\n"
        "🔹 **فعالية** -> بطرح فعالية حماسية للجروب هلأ ✨\n"
        "🔹 **صراحة** -> سؤال صراحة قوي ومحرج 🤫\n"
        "🔹 **مثل** -> بيعطيك مَثَل عربي قديم وحكمة 📜\n"
        "🔹 **حزورة** -> ألغاز وفوازير بتخلي مخك شغال 🧠\n"
        "🔹 **نسبة الحب** -> بتقيس المحبة والانسجام بالجروب 🥰\n"
        "🔹 **معلوماتي** -> كشف حساب لنقاطك ورتبتك الحالية 📊\n"
        "🔹 **كِشري** -> لعبة الحظ المثيرة 🎲\n\n"
        "💡 **شات الذكاء الاصطناعي المطور:**\n"
        "نادني بكلمة (يا فنوع) واكتب سؤالك بعدها مباشرة، وبسولف معك كأني خويك بالجروب! 🧠🤖"
    )
    await update.message.reply_text(menu, parse_mode="Markdown")


async def لعبة_خيروك(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"🤔 **لو خيروك:**\n\n{random.choice(قائمة_لو_خيروك)}",
        parse_mode="Markdown",
    )


async def كت_تويت(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"💬 **كت تويت:**\n\n{random.choice(قائمة_كت_تويت)}",
        parse_mode="Markdown",
    )


async def نكتة(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"🤣 **خذ هالنكتة وسلك لي:**\n\n{random.choice(قائمة_نكت)}",
    )


async def فعالية(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(random.choice(قائمة_فعاليات))


async def صراحة(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"🤫 **سؤال صراحة قوي لـ {name}:**\n\n{random.choice(قائمة_صراحة)}",
        parse_mode="Markdown",
    )


async def مثل(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"📜 **من حكم وأمثال زمان:**\n\n{random.choice(قائمة_أمثال)}",
        parse_mode="Markdown",
    )


async def حزورة(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    import asyncio

    riddle, answer = random.choice(قائمة_حزورة)
    await update.message.reply_text(
        f"🧩 **حزورة فنوع:**\n\n{riddle}\n\n(الجواب بعد 30 ثانية... فكر 🤔)",
        parse_mode="Markdown",
    )

    async def send_answer():
        await asyncio.sleep(30)
        await context.bot.send_message(
            update.effective_chat.id,
            f"⏳ **الجواب:**\n\n{answer} 🎯",
            parse_mode="Markdown",
        )

    asyncio.create_task(send_answer())


async def نسبة_الحب(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    percentage = random.randint(0, 100)
    if percentage < 30:
        msg = f"🥰 نسبة الحب بينك وبين الشات هلأ هي: **{percentage}%** 💔 (الوضع جفاف عاطفي وتكفيكم الابتسامة!)"
    elif percentage < 70:
        msg = f"🥰 نسبة الحب بينك وبين الشات هلأ هي: **{percentage}%** 🧡 (علاقة طيبة وصداقة مستقرة)"
    else:
        msg = f"🥰 نسبة الحب بينك وبين الشات هلأ هي: **{percentage}%** ❤️ (عشق وغرام والجروب كله يحبك!)"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def معلوماتي(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name

    async with async_session_factory() as session:
        member_repo = ChatMemberRepository(session)
        member = await member_repo.get_or_create(user_id, chat_id)
        points = member.points

        if points < 15:
            rank = "عضو جديد خجول 👶"
        elif points < 50:
            rank = "منور السهرة والجروب 🌟"
        elif points < 150:
            rank = "المتحدث اللبق للجروب 🎤"
        elif points < 300:
            rank = "نائب شيخ الجروب 👑"
        elif points < 500:
            rank = "شيخ الجروب والقلب النابض 👑🔥"
        elif points < 1000:
            rank = "أسطورة الجروب الخالدة 🏆"
        else:
            rank = "ملك فنوع الأول本王 👑🏆💎"

        status_text = (
            f"📊 **بطاقة هويتك التفاعلية - {name}:**\n\n"
            f"👤 **الاسم:** {name}\n"
            f"🪙 **النقاط:** {points}\n"
            f"🎖️ **الرتبة:** {rank}\n"
            f"✨ **المستوى:** {member.level}\n"
            f"💰 **العملات:** {member.coins}\n"
            f"⭐ **السمعة:** {member.reputation:.1f}\n"
            f"🔥 **التسجيل:** {member.streak_days} يوم\n\n"
            f"{['بداية قوية استمر', 'ماشاء الله تبارك الله', 'أنت روح الجروب', 'ناررر يا بطل'][min(points // 50, 3)]}"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")


async def كِشري(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bet = 10
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    async with async_session_factory() as session:
        member_repo = ChatMemberRepository(session)
        member = await member_repo.get_or_create(user_id, chat_id)

        if member.coins < bet:
            await update.message.reply_text("❌ ما عندك عملات كافية! اكتب 'معلوماتي' تشوف رصيدك.")
            return

        member.coins -= bet
        outcome = random.choices(
            ["lose", "small", "big", "jackpot"],
            weights=[40, 30, 20, 10],
        )[0]

        if outcome == "jackpot":
            win = bet * 10
            member.coins += win
            msg = f"🎉🎉🎉 **جاكبوت!** ربحت **{win}** عملة! مبروك يا محظوظ! 🎉🎉🎉"
        elif outcome == "big":
            win = bet * 3
            member.coins += win
            msg = f"🔥 **فوز كبير!** ربحت **{win}** عملة!"
        elif outcome == "small":
            win = bet * 2
            member.coins += win
            msg = f"✅ فزت بـ **{win}** عملة. مش بطال!"
        else:
            msg = f"💔 خسرت **{bet}** عملة. جرب مرة ثانية!"

        await update.message.reply_text(f"🎲 **كِشري:**\n\n{msg}", parse_mode="Markdown")
        await session.commit()


def get_game_handlers() -> list:
    from telegram.ext import CommandHandler, MessageHandler, filters

    game_commands = {
        "لو_خيروك": لعبة_خيروك,
        "كت_تويت": كت_تويت,
        "نكتة": نكتة,
        "نكته": نكتة,
        "فعالية": فعالية,
        "فعاليه": فعالية,
        "صراحة": صراحة,
        "صراحه": صراحة,
        "مثل": مثل,
        "مثله": مثل,
        "حزورة": حزورة,
        "حزوره": حزورة,
        "نسبة_الحب": نسبة_الحب,
        "نسبه_الحب": نسبة_الحب,
        "معلوماتي": معلوماتي,
        "الألعاب": games_menu,
        "الاوامر": games_menu,
        "الالعاب": games_menu,
        "قائمة_الألعاب": games_menu,
        "كِشري": كِشري,
        "كشري": كِشري,
    }

    return [
        MessageHandler(
            filters.Text([game_cmd]) & ~filters.COMMAND, handler
        )
        for game_cmd, handler in game_commands.items()
    ]
