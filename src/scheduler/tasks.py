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
    "🎤 فعالية الحين: اكتب بيت شعر أو سطر من أغنية معلقة ببالك اليوم.",
    "📱 فعالية الحين: كم نسبة شحن جوالك الحين؟ اللي شحنه أقل من 20% يروح يشحن!",
    "📸 فعالية الحين: أرسل أكثر صورة مضحكة (ميمز) موجودة في استديو جوالك الحين!",
    "💬 فعالية الحين: منشن لأكثر شخص يسولف بالجروب وقول له (خف علينا يا راديو)🎙️",
    "🍽️ فعالية الحين: وش كان غداكم اليوم؟ اعترفوا بدون كذب 🥘",
    "💡 فعالية الحين: اكتب كلمة (فنوع) وعطنا رأيك بالبوت بكل صراحة!",
    "⏰ فعالية الحين: كم ساعة تقضيها على جوالك باليوم؟ (ادخل الإعدادات وصور الشاشة لو تجرؤ) 📱",
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
