from __future__ import annotations

import asyncio
import random
from datetime import datetime

from loguru import logger

from src.database.engine import async_session_factory
from src.database.repository import ScheduledJobRepository

فعاليات = [
    "🎯 فعالية الحين: كل واحد يكتب اسم أكثر شخص يثق فيه بالجروب!",
    "🔮 فعالية الحين: أرسل آخر إيموجي استخدمته بالواتساب بدون كذب!",
    "📱 فعالية الحين: قديش نسبة شحن جوالك هلأ؟ اللي شحنه أقل من 20% يروح يشحن!",
    "📸 فعالية الحين: أرسل أكثر صورة مضحكة (ميمز) موجودة في استديو جوالك!",
    "💬 فعالية الحين: منشن لأكثر شخص يسولف بالجروب وقول له (خف علينا يا راديو)🎙️",
    "🍽️ فعالية الحين: شو كان أكلكم اليوم؟ اعترفوا بدون كذب 🥘",
    "💡 فعالية الحين: اكتب كلمة (فنوع) وعطنا رأيك بالبوت بكل صراحة!",
    "⏰ فعالية الحين: قديش ساعة بتقضيها على جوالك باليوم؟ 📱",
]

أذكار = [
    "🌿 **ذكر عشوائي:**\n\nاللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور 🤲",
    "🌿 **ذكر عشوائي:**\n\nسبحان الله وبحمده عدد خلقه ورضا نفسه وزنة عرشه ومداد كلماته 🤲",
    "🌿 **ذكر عشوائي:**\n\nاللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك 🤲",
    "🌿 **ذكر عشوائي:**\n\nحسبي الله لا إله إلا هو، عليه توكلت، وهو رب العرش العظيم 🤲",
    "🌿 **ذكر عشوائي:**\n\nاللهم إني أسألك العفو والعافية في الدنيا والآخرة 🤲",
    "🌿 **ذكر عشوائي:**\n\nرضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً 🤲",
    "🌿 **ذكر عشوائي:**\n\nلا حول ولا قوة إلا بالله 🤲",
    "🌿 **ذكر عشوائي:**\n\nاللهم صل وسلم على نبينا محمد 🤲",
    "🌿 **ذكر عشوائي:**\n\nأستغفر الله الذي لا إله إلا هو الحي القيوم وأتوب إليه 🤲",
    "🌿 **ذكر عشوائي:**\n\nلا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🤲",
    "🌿 **ذكر عشوائي:**\n\nاللهم إني أسألك الهدى والتقى والعفاف والغنى 🤲",
    "🌿 **ذكر عشوائي:**\n\nربنا آتنا في الدنيا حسنة وفي الآخرة حسنة وقنا عذاب النار 🤲",
]


class SchedulerService:
    def __init__(self, bot=None):
        self._bot = bot
        self._tasks = []
        self._running = False

    def set_bot(self, bot):
        self._bot = bot

    async def start(self):
        self._running = True
        self._tasks.append(asyncio.create_task(self._auto_activity_loop()))
        self._tasks.append(asyncio.create_task(self._auto_azkar_loop()))
        self._tasks.append(asyncio.create_task(self._check_expired_jobs()))
        logger.info("Scheduler started")

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        logger.info("Scheduler stopped")

    async def _auto_activity_loop(self):
        while self._running:
            await asyncio.sleep(2700)
            await self._broadcast_activity()

    async def _broadcast_activity(self):
        if not self._bot:
            return
        try:
            async with async_session_factory() as session:
                job_repo = ScheduledJobRepository(session)
                jobs = await job_repo.get_due()

                for job in jobs:
                    if job.job_type == "activity":
                        activity = random.choice(فعاليات)
                        try:
                            await self._bot.send_message(
                                job.chat_id,
                                f"⏰ **فعالية عشوائية من فنوع:**\n\n{activity}",
                                parse_mode="Markdown",
                            )
                            job.last_run = datetime.utcnow()
                        except Exception as e:
                            logger.warning(f"Failed to send activity to {job.chat_id}: {e}")

                await session.commit()
        except Exception as e:
            logger.error(f"Error in broadcast_activity: {e}")

    async def _auto_azkar_loop(self):
        while self._running:
            await asyncio.sleep(10800)
            await self._broadcast_azkar()

    async def _broadcast_azkar(self):
        if not self._bot:
            return
        try:
            async with async_session_factory() as session:
                job_repo = ScheduledJobRepository(session)
                jobs = await job_repo.get_due()

                for job in jobs:
                    if job.job_type == "activity":
                        zekr = random.choice(أذكار)
                        try:
                            await self._bot.send_message(
                                job.chat_id,
                                f"⏰ **ذكر من فنوع:**\n\n{zekr}",
                                parse_mode="Markdown",
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send azkar to {job.chat_id}: {e}")

                await session.commit()
        except Exception as e:
            logger.error(f"Error in broadcast_azkar: {e}")

    async def _check_expired_jobs(self):
        from src.database.repository import InfractionRepository

        while self._running:
            await asyncio.sleep(60)
            try:
                async with async_session_factory() as session:
                    repo = InfractionRepository(session)
                    expired = await repo.deactivate_expired()
                    if expired:
                        logger.info(f"Deactivated {len(expired)} expired infractions")
            except Exception as e:
                logger.error(f"Error checking expired infractions: {e}")


scheduler_service = SchedulerService()
