from __future__ import annotations

import random
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from src.database.repository import ChatMemberRepository

# ---------- Game Data ----------

قائمة_لو_خيروك = [
    "تاكل بصل ني 🧅 أو تاكل ليمونة كاملة بقشرها 🍋؟",
    "تعيش بدون جوال أسبوع 📱 أو بدون نت شهر 🌐؟",
    "تصير غني وتعيش لحالك 💰 أو على قد حالك ومعك ربعك 👥؟",
    "تسافر للمستقبل وتشوف نفسك 🚀 أو ترجع للماضي وتغير غلطة ⏳؟",
    "تختفي وتسمع وش يقولون الناس عنك 👻 أو تقرأ أفكارهم بلمسة 🧠؟",
    "تعيش في غابة مع حيوانات أليفة 🦁 أو تعيش بقصر فخم لحالك 🏰؟",
    "تنام في مقبرة ليلة كاملة لحالك 🪦 أو تسبح مع قروش في البحر 🦈؟",
    "تخسر كل فلوسك الحين 💸 أو تخسر كل ذكريات طفولتك 🧠؟",
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
    "أكثر صفة تكرهها في الشخص اللي قدامك؟ 🧐",
    "لو كان عندك قوة خارقة، وش تختار تكون؟ 🦸‍♂️",
    "وش آخر مصيبة سويتها وجوالك طافي؟ 💀",
    "اعتراف خطير بدون ذكر أسماء؟ 🤫",
    "شخص بالجروب ودك تعطيه كف وتطلع؟ 😂 (بدون منشن)",
    "لو باقي يوم واحد بالعالم وش بتسوي فيه؟ 🌍",
    "أكثر أكلة مستحيل تاكلها لو تموت جوع؟ 🤮",
    "هل تؤمن بالحب من أول نظرة، ولا السالفة كلها كذب؟ 👁️❤️",
    "لو فتحنا معرض لعيوبك، وش بيكون المَعْروض الرئيسي؟ 🖼️",
    "وش الكلمة اللي لو حد قالها لك الحين تبتسم تلقائياً؟ 😊",
    "شيء سويته بالماضي وكل ما تتذكره تحس بالندم أو الفشلة؟ 🤦‍♂️",
    "لو خيروك تسمي نفسك اسم جديد الحين، وش بتختار؟ 📝",
    "تفضل الصديق العاقل الزيادة، ولا الصديق الفاصل اللي يوديك بداهية؟ 🤣",
    "متى كانت آخر مرة بكيت فيها ومن قلب؟ 😢",
    "شيء غريب تحب تسويه لما تكون لحالك بالبيت؟ 🏠🍿",
    "لو حياتك عبارة عن فيلم، وش بيكون تصنيفه (كوميدي، دراما، رعب)؟ 🎬",
]

قائمة_نكت = [
    "محشش شاف إشارة ممنوع الوقوف.. قام انبطح! 🏛️😂",
    "واحد بخيل تزوج بخيلة.. جابوا ولد حطوه بالبنك! 💰🤣",
    "نملة شافت عصير فراولة.. قالت: واو أخيراً شفت البحر الأحمر! 🐜🍓",
    "محشش ضاعت محفظته راح يبلغ الشرطة، قالوا له: ولا يهمك روح البيت واحنا بنطلعها من تحت الأرض.. وهو راجع شاف عمال بلدية يحفرون الشارع، صاح عليهم: كفووو شدوا حيلكم لونها بني! 💼😂",
    "واحد غبي راح يشتري عطر، سأله البائع: تبيه بخاخ ولا صب؟ قال: لا خله عصير أشربه هنا! 🧴🤣",
    "ديك شاف بيضة مسلوقة، راح للدجاجة قال لها: وش هذا؟ شغالين حبوب منع حمل من وراي؟ 🐓😂",
    "أستاذ سأل طالب غبي: اعطيني جملة فيها كلمة (سكر).. قال الطالب: شربت الشاهي الصبح.. قال الأستاذ: وين السكر؟ قال الطالب: ذاب بالشاهي يا أستاذ! ☕🤪",
    "محشش اتصل بالخطوط الجوية قالهم: كم تستغرق الرحلة من هنا لأمريكا؟ قالوا له: ثانية واحدة يا فندم.. قال: شكراً، وقفل الخط! ✈️😭",
    "واحد قروي دخل ماكدونالدز قالهم: عطوني واحد فلافل، قالوا له: ما عندنا، قال: طيب وش هاللوحة الكبيرة اللي حاطين فيها صورتي وأنا لابس شماغ؟ (طلع شعار كنتاكي)! 🍗😂",
]

قائمة_فعاليات = [
    "🎯 فعالية الحين: كل واحد يكتب اسم أكثر شخص يثق فيه بالجروب!",
    "🔮 فعالية الحين: أرسل آخر إيموجي استخدمته بالواتساب بدون كذب!",
    "🎤 فعالية الحين: اكتب بيت شعر أو سطر من أغنية معلقة ببالك اليوم.",
    "📱 فعالية الحين: كم نسبة شحن جوالك الحين؟ اللي شحنه أقل من 20% يروح يشحن!",
    "📸 فعالية الحين: أرسل أكثر صورة مضحكة (ميمز) موجودة في استديو جوالك الحين!",
    "💬 فعالية الحين: منشن لأكثر شخص يسولف بالجروب وقول له (خف علينا يا راديو)🎙️",
    "🍽️ فعالية الحين: وش كان غداكم اليوم؟ اعترفوا بدون كذب 🥘",
    "💡 فعالية الحين: اكتب كلمة (فنوع) وعطنا رأيك بالبوت بكل صراحة!",
    "⏰ فعالية الحين: كم ساعة تقضيها على جوالك باليوم؟ (ادخل الإعدادات وصور الشاشة لو تجرؤ) 📱",
]

قائمة_صراحة = [
    "هل سبق وسرقت شيء بسيط من أغراض أخوانك؟ 👀",
    "مين الشخص اللي بالجروب وتتابع رسايله بصمت؟ 🤫",
    "وش أكبر كذبة كذبتها على أهلك ومشت عليهم؟ 🤥",
    "هل شكلك بالبطاقة الشخصية/الهوية يفشل ولا حلو؟ 🪪😂",
    "لو شفت حبيبك القديم بالشارع بالصدفة، وش بتسوي؟ 🏃‍♂️",
    "كم رصيدك بالحساب البنكي حالياً بدون خجل؟ 💵",
    "هل أنت شخص غيور في العلاقات ولا عادي بارد؟ 🔥",
    "وش أكثر عيب دايماً الناس يلاحظونه بشخصيتك؟ 😕",
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
        "🔹 **فعالية** -> يطرح فعالية حماسية للجروب الحين ✨\n"
        "🔹 **صراحة** -> سؤال صراحة قوي ومحرج 🤫\n"
        "🔹 **مثل** -> يعطيك مَثَل عربي قديم وحكمة 📜\n"
        "🔹 **حزورة** -> ألغاز وفوازير تخلي مخك شغال 🧠\n"
        "🔹 **نسبة الحب** -> تقيس المحبة والانسجام بالجروب 🥰\n"
        "🔹 **معلوماتي** -> كشف حساب لنقاطك ورتبتك الحالية 📊\n"
        "🔹 **المتجر** -> اشتر ألقاب وألوان ومؤثرات 🛍️\n"
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
        msg = f"🥰 نسبة الحب بينك وبين الشات الحين هي: **{percentage}%** 💔 (الوضع جفاف عاطفي وتكفيكم الابتسامة!)"
    elif percentage < 70:
        msg = f"🥰 نسبة الحب بينك وبين الشات الحين هي: **{percentage}%** 🧡 (علاقة طيبة وصداقة مستقرة)"
    else:
        msg = f"🥰 نسبة الحب بينك وبين الشات الحين هي: **{percentage}%** ❤️ (عشق وغرام والجروب كله يحبك!)"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def معلوماتي(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name

    member_repo: ChatMemberRepository = context.user_data.get("member_repo")
    if not member_repo:
        await update.message.reply_text("❌ النظام ليس جاهزاً بعد، حاول مرة أخرى.")
        return

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

    member_repo: ChatMemberRepository = context.user_data.get("member_repo")
    if not member_repo:
        return

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
    }

    return [
        MessageHandler(
            filters.Text(game_cmd) & ~filters.COMMAND, handler
        )
        for game_cmd, handler in game_commands.items()
    ]
