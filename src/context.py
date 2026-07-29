"""🔗 نگهدارندهٔ آبجکت‌های سراسری (DB و Bot) — جلوگیری از import چرخه‌ای."""
from __future__ import annotations

from .db import DB

db: DB | None = None  # in bot.py پر می‌شود


def get_db() -> DB:
    assert db is not None, "DB هنوز راه‌اندازی نشده (از bot.py صدا بزن)"
    return db
