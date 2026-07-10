import os
import telebot
import random
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.environ.get("BOT_TOKEN") or '8826743057:AAG3PVj8vTGCG_bh2Mr3CJnKsemMHPxBe0U'
bot = telebot.TeleBot(TOKEN)

# قاعدة بيانات مؤقتة في ذاكرة السيرفر لحفظ التفاعل
user_points = {}
# أدمنية البوت (رفع ادمن/تنزيل ادمن) — {chat_id: set(user_ids)}
promoted_admins: dict[int, set[int]] = {}

# قائمة الفلترة والحماية (الكلمات الممنوعة)
bad_words = [
    "كلب", "حمار", "غبي", "تفه", "منحط", "يا كلب", "يا حمار", "تيس", "يا تيس", 
    "حيوان", "يا حيوان", "كلاب", "الحمار", "الكلب", "تفو", "قليل حيا"
]

# ========================================================
# 📚 بنك البيانات العملاق للألعاب والفعاليات والردود
# ========================================================

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
    "تمشي حافي على رمل حار 🥵 أو تمشي حافي على ثلج 🥶؟"
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
    "لو حياتك عبارة عن فيلم، وش بيكون تصنيفه (كوميدي، دراما، رعب)؟ 🎬"
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
    "واحد قروي دخل ماكدونالدز قالهم: عطوني واحد فلافل، قالوا له: ما عندنا، قال: طيب وش هاللوحة الكبيرة اللي حاطين فيها صورتي وأنا لابس شماغ؟ (طلع شعار كنتاكي)! 🍗😂"
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
    "⏰ فعالية الحين: كم ساعة تقضيها على جوالك باليوم؟ (ادخل الإعدادات وصور الشاشة لو تجرؤ) 📱"
]

قائمة_صراحة = [
    "هل سبق وسرقت شيء بسيط من أغراض أخوانك؟ 👀",
    "مين الشخص اللي بالجروب وتتابع رسايله بصمت؟ 🤫",
    "وش أكبر كذبة كذبتها على أهلك ومشت عليهم؟ 🤥",
    "هل شكلك بالبطاقة الشخصية/الهوية يفشل ولا حلو؟ 🪪😂",
    "لو شفت حبيبك القديم بالشارع بالصدفة، وش بتسوي؟ 🏃‍♂️",
    "كم رصيدك بالحساب البنكي حالياً بدون خجل؟ 💵",
    "هل أنت شخص غيور في العلاقات ولا عادي بارد؟ 🔥",
    "وش أكثر عيب دايماً الناس يلاحظونه بشخصيتك؟ 😕"
]

قائمة_أمثال = [
    "إذا كان الكلام من فضة فالسكوت من ذهب 🪙",
    "القرش الأبيض ينفع في اليوم الأسود 💵",
    "من حفر حفرة لأخيه وقع فيها 🕳️",
    "يا داخل بين البصلة وقشرتها ما ينوبك إلا ريحتها 🧅",
    "الذي بيته من زجاج لا يرمي الناس بالحجارة 🧱",
    "عصفور في اليد خير من عشرة على الشجرة 🐦",
    "القرعة تتباهى بشعر بنت أختها 👩‍🦲",
    "امش في جنازة ولا تمش في جوازة 🚶‍♂️"
]

# ---- Groq (LLaMA) الذكاء الاصطناعي ----
from collections import deque

ai_memory: dict[int, deque] = {}

SYSTEM_PROMPT_GROQ = (
    "أنت بوت تلغرام ثقيل دم وزَنخ. تتحدث باللهجة الفلسطينية البدوية. "
    "ردودك قصيرة (جملة أو جملتين). "
    "استخدم كلمتي 'تقرفنييش' و'تقرفوناش' فقط لما يكون المعنى مناسب، مو بكل رد. "
    "لا تصرح بهويتك أو شخصيتك."
)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or ""

def ask_groq(messages: list[dict]) -> str:
    if not GROQ_API_KEY:
        return "ما في مفتاح AI، حط GROQ_API_KEY في .env 🧠"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": messages}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return "سيرفر الذكاء نايم حالياً، خلنا نلعب أحسن 😴"

# ========================================================
# �️ دوال مساعدة للأدمن والمشرفين
# ========================================================

def is_admin(chat_id, user_id):
    if chat_id in promoted_admins and user_id in promoted_admins[chat_id]:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False


def get_target_user(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user

    if message.entities:
        for entity in message.entities:
            if entity.type in ['text_mention', 'mention']:
                if entity.type == 'text_mention' and entity.user:
                    return entity.user
                elif entity.type == 'mention':
                    username = message.text[entity.offset:entity.offset + entity.length].lstrip('@')
                    try:
                        user = bot.get_chat_member(message.chat.id, username).user
                        return user
                    except:
                        return None
    return None


def admin_only(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⚠️ هذه الأوامر خاصة بالمشرفين فقط.")
        return False
    return True

# ========================================================
# �🚨 ميزة المغادرة التلقائية الاحترافية + الترقية الفورية
# ========================================================
@bot.message_handler(content_types=['new_chat_members'])
def on_bot_join(message):
    for new_user in message.new_chat_members:
        # إذا كان العضو المضاف هو البوت نفسه
        if new_user.id == bot.get_me().id:
            chat_id = message.chat.id
            bot_username = bot.get_me().username
            bot_member = bot.get_chat_member(chat_id, bot.get_me().id)
            
            # التحقق: هل أضيف كعضو عادي أم مشرف؟
            if bot_member.status not in ['administrator', 'creator']:
                # إنشاء زر الترقية الفوري بالصلاحيات اللازمة للجروبات
                markup = InlineKeyboardMarkup()
                admin_link = f"https://t.me/{bot_username}?startgroup=Commands&admin=ban_users+restrict_members+delete_messages+add_admins+change_info+invite_users+pin_messages"
                upgrade_button = InlineKeyboardButton(text="اضغط هنا لرفع فنوع مشرف 👑", url=admin_link)
                markup.add(upgrade_button)
                
                warning_text = (
                    "⚠️ **تنبيه من البوت فنوع:**\n"
                    "قمت بإضافة البوت كعضو في المجموعة! يجب رفعه مشرفاً لكي يتم تفعيله ويحميك.\n\n"
                    "اضغط على الزر بالأسفل لرفعي مشرفاً بالصلاحيات المطلوبة فوراً وجاهزة 👇"
                )
                bot.send_message(chat_id, warning_text, reply_markup=markup, parse_mode="Markdown")
                
                # المغادرة التلقائية فوراً لحماية السيرفر واجبار صاحب الجروب على ترقيته
                bot.leave_chat(chat_id)
                return
            else:
                bot.send_message(chat_id, "🥳 كفو! تم تفعيل البوت فنوع بنجاح كـ مشرف بالجروب! اكتب 'الألعاب' وخلنا نفلها! 🔥")
                return
        else:
            # الترحيب بالأعضاء العاديين الجدد
            welcome_text = (
                f"🎯 يا هلا وغلا بـ {new_user.first_name} نورت جروبنا السعيد! ✨\n"
                "اكتب كلمة **'تم'** وسولف معنا عشان تجمع نقاط وتأخذ ألقاب فخمة بالجروب! 🔥"
            )
            bot.send_message(message.chat.id, welcome_text)

# ========================================================
# ⚙️ قراءة الرسائل، الألعاب، الردود الذكية والذكاء الاصطناعي
# ========================================================
@bot.message_handler(func=lambda message: True)
def main_handler(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    text = message.text.strip() if message.text else ""

    # ---- [حماية] منع الروابط الإعلانية ----
    if "http://" in text.lower() or "https://" in text.lower() or "t.me/" in text.lower():
        try:
            chat_member = bot.get_chat_member(message.chat.id, user_id)
            if chat_member.status not in ['administrator', 'creator']:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"⚠️ عذراً يا {user_name}، الروابط ممنوعة هنا للحماية من الإعلانات! ⛔")
                return
        except:
            pass

    # ---- [حماية] منع الكلمات البذيئة ----
    if any(word in text for word in bad_words):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"🤫 أستغفر الله! يا {user_name} جروبنا محترم وما نبي كلام يزعل الأعضاء! 🥛")
            return
        except:
            pass

    # ---- نظام زيادة نقاط التفاعل ----
    if user_id not in user_points:
        user_points[user_id] = 0
    user_points[user_id] += 1 

    # ================= قـائـمـة الأوامـر والـألـعـاب العـربـيـة =================

    if text == "الألعاب" or text == "الاوامر" or text == "الالعاب" or text == "قائمة الألعاب":
        menu = (
            "🎮 **قائمة ألعاب وفعاليات فنوع العملاقة:**\n"
            "(اكتب الكلمة مباشرة بدون فواصل أو رموز إنجليزية)\n\n"
            "🔹 **لو خيروك** -> خيارات صعبة ومحرجة 🤔\n"
            "🔹 **كت تويت** -> أسئلة لتحريك الشات والسوالف 💬\n"
            "🔹 **نكتة** -> أحدث وأقوى النكت التليجرامية 🤣\n"
            "🔹 **فعالية** -> يطرح فعالية حماسية للجروب الحين ✨\n"
            "🔹 **صراحة** -> سؤال صراحة قوي ومحرج 🤫\n"
            "🔹 **مثل** -> يعطيك مَثَل عربي قديم وحكمة 📜\n"
            "🔹 **نسبة الحب** -> تقيس المحبة والانسجام بالجروب 🥰\n"
            "🔹 **معلوماتي** -> كشف حساب لنقاطك ورتبتك الحالية 📊\n\n"
            "💡 **شات الذكاء الاصطناعي المطور:**\n"
            "نادني بكلمة (يا فنوع) واكتب سؤالك بعدها مباشرة، وبسولف معك كأني خويك بالجروب! 🧠🤖"
        )
        bot.reply_to(message, menu)

    elif text == "لو خيروك":
        bot.reply_to(message, f"🤔 **لو خيروك:**\n\n{random.choice(قائمة_لو_خيروك)}")

    elif text == "كت تويت":
        bot.reply_to(message, f"💬 **كت تويت:**\n\n{random.choice(قائمة_كت_تويت)}")

    elif text == "نكتة" or text == "نكته":
        bot.reply_to(message, f"🤣 **خذ هالنكتة وسلك لي:**\n\n{random.choice(قائمة_نكت)}")

    elif text == "فعالية" or text == "فعاليه":
        bot.reply_to(message, f"{random.choice(قائمة_فعاليات)}")

    elif text == "صراحة" or text == "صراحه":
        bot.reply_to(message, f"🤫 **سؤال صراحة قوي لـ {user_name}:**\n\n{random.choice(قائمة_صراحة)}")

    elif text == "مثل" or text == "مثله":
        bot.reply_to(message, f"📜 **من حكم وأمثال زمان:**\n\n{random.choice(قائمة_أمثال)}")

    elif text == "نسبة الحب" or text == "نسبه الحب":
        percentage = random.randint(0, 100)
        if percentage < 30:
            bot.reply_to(message, f"🥰 نسبة الحب بينك وبين الشات الحين هي: **{percentage}%** 💔 (الوضع جفاف عاطفي وتكفيكم الابتسامة!)")
        elif percentage < 70:
            bot.reply_to(message, f"🥰 نسبة الحب بينك وبين الشات الحين هي: **{percentage}%** 🧡 (علاقة طيبة وصداقة مستقرة)")
        else:
            bot.reply_to(message, f"🥰 نسبة الحب بينك وبين الشات الحين هي: **{percentage}%** ❤️ (عشق وغرام والجروب كله يحبك!)")

    elif text == "معلوماتي":
        points = user_points.get(user_id, 1)
        if points < 15: rank = "عضو جديد خجول 👶"
        elif points < 50: rank = "منور السهرة والجروب 🌟"
        elif points < 150: rank = "المتحدث اللبق للجروب 🎤"
        else: rank = "شيخ الجروب والقلب النابض للدردشة 👑"
        
        status_text = f"📊 **بطاقة هويتك التفاعلية:**\n\n👤 اسمك الكريم: {user_name}\n🪙 عدد رسائلك ونقاطك: {points}\n🎖️ رتبتك الحالية: {rank}"
        bot.reply_to(message, status_text)

    # ================= أوامر مشرفين وإدارة =================
    elif text == "قائمة الأدمن":
        if not admin_only(message):
            return
        admin_menu = (
            "🛡️ **أوامر الأدمن في فنوع:**\n"
            "- ارفض (رد على رسالة) -> يحظر مؤقتاً أو يبند حسب الحاجة\n"
            "- كيك (رد على رسالة) -> يطرد العضو من الجروب\n"
            "- اسكت (رد على رسالة) -> يكتم العضو 60 ثانية\n"
            "- فك اسكت (رد على رسالة) -> يفك الكتم عن العضو\n"
            "- حظر (رد على رسالة أو @username) -> يمنع العضو من الجروب\n"
            "- رفع صوتي -> يرفع صوت البوت ويشير إنه شغال\n"
            "- تنزيل صوتي -> يوقف صوت البوت ويشير إنه هادي\n"
        )
        bot.reply_to(message, admin_menu)

    elif text.startswith("حظر"):
        if not admin_only(message):
            return
        target = get_target_user(message)
        if not target:
            bot.reply_to(message, "❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر حظر.")
            return
        try:
            bot.kick_chat_member(message.chat.id, target.id)
            bot.reply_to(message, f"✅ تم حظر {target.first_name} من المجموعة.")
        except Exception as e:
            bot.reply_to(message, f"⚠️ ما قدرت أحظر العضو، تأكد أني مشرف وعندي صلاحيات. \n{e}")

    elif text.startswith("طرد") or text.startswith("كيك"):
        if not admin_only(message):
            return
        target = get_target_user(message)
        if not target:
            bot.reply_to(message, "❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر كيك.")
            return
        try:
            bot.kick_chat_member(message.chat.id, target.id)
            bot.unban_chat_member(message.chat.id, target.id)
            bot.reply_to(message, f"✅ تم طرد {target.first_name} من المجموعة.")
        except Exception as e:
            bot.reply_to(message, f"⚠️ ما قدرت أطرد العضو، تأكد أني مشرف وعندي صلاحيات. \n{e}")

    elif text.startswith("اسكت"):
        if not admin_only(message):
            return
        target = get_target_user(message)
        if not target:
            bot.reply_to(message, "❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر اسكت.")
            return
        try:
            permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(message.chat.id, target.id, permissions=permissions, until_date=None)
            bot.reply_to(message, f"✅ تم كتم {target.first_name} مؤقتاً.")
        except Exception as e:
            bot.reply_to(message, f"⚠️ ما قدرت أكتم العضو، تأكد أني مشرف وعندي صلاحيات. \n{e}")

    elif text.startswith("فك اسكت"):
        if not admin_only(message):
            return
        target = get_target_user(message)
        if not target:
            bot.reply_to(message, "❌ رجاءً رد على رسالة العضو أو استخدم @username بعد أمر فك اسكت.")
            return
        try:
            permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True,
                                          can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False,
                                          can_invite_users=True, can_pin_messages=False)
            bot.restrict_chat_member(message.chat.id, target.id, permissions=permissions)
            bot.reply_to(message, f"✅ تم رفع الكتم عن {target.first_name}.")
        except Exception as e:
            bot.reply_to(message, f"⚠️ ما قدرت أفك الكتم، تأكد أني مشرف وعندي صلاحيات. \n{e}")

    elif text == "رفع صوتي":
        if not admin_only(message):
            return
        bot.reply_to(message, "🔊 تم تفعيل وضع الزعلان، البوت جاهز وأعلى صوت!")

    elif text == "تنزيل صوتي":
        if not admin_only(message):
            return
        bot.reply_to(message, "🤫 تم تفعيل وضع الهدوء، البوت سيصبح خفيف وهادي.")

    elif text.startswith("رفع ادمن"):
        if user_name != "فَـنّـعِـهْ" and user_id != 5544674713:
            bot.reply_to(message, "⚠️ هاد الأمر بس للمالك.")
            return
        target = get_target_user(message)
        if not target:
            bot.reply_to(message, "❌ رد على رسالة العضو اللي بدك ترفعه.")
            return
        cid = message.chat.id
        promoted_admins.setdefault(cid, set()).add(target.id)
        bot.reply_to(message, f"✅ تم رفع {target.first_name} إلى أدمن في البوت.")

    elif text.startswith("تنزيل ادمن"):
        if user_name != "فَـنّـعِـهْ" and user_id != 5544674713:
            bot.reply_to(message, "⚠️ هاد الأمر بس للمالك.")
            return
        target = get_target_user(message)
        if not target:
            bot.reply_to(message, "❌ رد على رسالة العضو اللي بدك تنزله.")
            return
        cid = message.chat.id
        if cid in promoted_admins:
            promoted_admins[cid].discard(target.id)
        bot.reply_to(message, f"✅ تم تنزيل {target.first_name} من أدمن البوت.")

    # ================= قائمة الردود التلقائية الفكاهية واليومية =================
    elif "طفش" in text or "ملل" in text:
        bot.reply_to(message, "افا! الطفش ممنوع بوجود فنوع 🥳 اكتب كلمة 'الألعاب' وخلنا نفلها ونطرد الملل!")
        
    elif text == "باك" or text == "بااك":
        bot.reply_to(message, f"أحلى وأجمل باك في العالم! منورنا يا {user_name} ورجعت لنا الضحكة ✨")
        
    elif text == "برب":
        bot.reply_to(message, f"لا تطول علينا يا {user_name}، الجروب بيظلم وبنصير نشتاق لك! 🏃‍♂️")
        
    elif "سلام" in text or text == "السلام عليكم":
        bot.reply_to(message, f"وعليكم السلام ورحمة الله وبركاته! يا هلا وغلا بـ {user_name} نورتنا يا عسل 🌸")

    elif text == "فنوع" or text == "يا فنوع":
        bot.reply_to(message, "لبيه وسعدك! عيون فنوع وروحه تآمرك. اكتب 'الألعاب' عشان نلعب، أو اسألني بـ (يا فنوع...) وبجاوبك فوراً 😉")

    elif "هههه" in text or "خخخخ" in text:
        responses = ["جعلها دوم هالضحكة يا رب! 😂", "ضحكتك تفتح النفس وربي 🤍", "تدوم الضحكة الحلوة يا عسل 🥰"]
        bot.reply_to(message, random.choice(responses))

    elif text == "تصبحون على خير" or text == "بنام":
        bot.reply_to(message, f"تلاقي الخير يا {user_name} 🌙 أحلام سعيدة ونوم العوافي، لا تنسى تصحى وتجيب لنا كيك بكرا! 🍰")

    elif text == "الحمد لله" or text == "الحمدلله":
        bot.reply_to(message, "الحمد لله دائماً وأبداً على كل حال 🤲 ربي يديم عليك النعمة والراحة.")

    # ================= شات الذكاء الاصطناعي (يا فنوع + السؤال) =================
    elif text.startswith("يا فنوع ") or text.startswith("فنوع "):
        question = text.replace("يا فنوع", "").replace("فنوع", "").strip()
        if not question:
            bot.reply_to(message, "لبيه! ناديتني؟ اسألني أي شيء وبجاوبك، مثلاً: (يا فنوع عطني نصيحة مضحكة) 🤖")
        else:
            bot.send_chat_action(message.chat.id, 'typing')
            cid = message.chat.id
            if cid not in ai_memory:
                ai_memory[cid] = deque(maxlen=30)
            ai_memory[cid].append({"role": "user", "content": question})
            msgs = [{"role": "system", "content": SYSTEM_PROMPT_GROQ}]
            msgs.extend(list(ai_memory[cid])[-20:])
            reply = ask_groq(msgs)
            ai_memory[cid].append({"role": "assistant", "content": reply})
            bot.reply_to(message, reply)

# تشغيل البوت واستمراريته
import sys; sys.stdout.reconfigure(encoding='utf-8', errors='replace')
print("🚀 البوت العملاق 'فنوع' شغال الآن بكفاءة واحترافية وبدون أوامر إنجليزية...")
bot.infinity_polling()