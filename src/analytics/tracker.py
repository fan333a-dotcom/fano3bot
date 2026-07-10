from __future__ import annotations

from datetime import datetime, timedelta

from src.config import settings


class AnalyticsTracker:
    def __init__(self):
        self._daily_counts: dict[str, dict] = {}
        self._peak_hours: dict[str, list[int]] = {}
        self._word_freq: dict[str, dict[str, int]] = {}

    def track_message(
        self, chat_id: int, user_id: int, text: str, content_type: str = "text"
    ):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        chat_key = str(chat_id)
        hour = datetime.utcnow().hour

        if chat_key not in self._daily_counts:
            self._daily_counts[chat_key] = {}
        if today not in self._daily_counts[chat_key]:
            self._daily_counts[chat_key][today] = {
                "messages": 0,
                "users": set(),
                "links": 0,
                "media": 0,
            }

        stats = self._daily_counts[chat_key][today]
        stats["messages"] += 1
        stats["users"].add(user_id)

        if chat_key not in self._peak_hours:
            self._peak_hours[chat_key] = [0] * 24
        self._peak_hours[chat_key][hour] += 1

        if content_type in ("photo", "video", "animation", "document"):
            stats["media"] += 1

        if text and ("http://" in text.lower() or "https://" in text.lower() or "t.me/" in text.lower()):
            stats["links"] += 1

        if text:
            if chat_key not in self._word_freq:
                self._word_freq[chat_key] = {}
            for word in text.split():
                if len(word) > 2:
                    self._word_freq[chat_key][word] = self._word_freq[chat_key].get(word, 0) + 1

    def get_daily_summary(self, chat_id: int) -> dict:
        chat_key = str(chat_id)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        stats = self._daily_counts.get(chat_key, {}).get(today, {})
        return {
            "messages": stats.get("messages", 0),
            "active_users": len(stats.get("users", set())),
            "links": stats.get("links", 0),
            "media": stats.get("media", 0),
        }

    def get_peak_hours(self, chat_id: int) -> list[int]:
        chat_key = str(chat_id)
        return self._peak_hours.get(chat_key, [0] * 24)

    def get_top_words(self, chat_id: int, limit: int = 10) -> list[tuple[str, int]]:
        chat_key = str(chat_id)
        freq = self._word_freq.get(chat_key, {})
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_weekly_trend(self, chat_id: int) -> list[dict]:
        chat_key = str(chat_id)
        result = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self._daily_counts.get(chat_key, {}).get(date, {})
            result.append({
                "date": date,
                "messages": stats.get("messages", 0),
                "active_users": len(stats.get("users", set())),
            })
        return list(reversed(result))


analytics_tracker = AnalyticsTracker()
