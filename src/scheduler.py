"""🔔 زمان‌بند یادآور روزانهٔ تمرین."""
from __future__ import annotations

import asyncio
from datetime import datetime

from aiogram import Bot

from .context import get_db
from . import texts as T


async def reminder_loop(bot: Bot, interval: int = 60) -> None:
    """هر دقیقه کاربران با یادآور فعال را چک می‌کند و در ساعت مقرر پیام می‌فرستد."""
    await asyncio.sleep(5)
    while True:
        try:
            db = get_db()
            now_dt = datetime.now()
            today = now_dt.strftime("%Y-%m-%d")
            users = db.con.execute(
                "SELECT * FROM users WHERE reminder_on = 1 AND reminder_hour = ? AND is_blocked = 0",
                (now_dt.hour,),
            ).fetchall()
            for u in users:
                if u["last_reminded"] == today:
                    continue
                try:
                    await bot.send_message(
                        u["id"], T.REMINDER_MSG.format(name=u["name"] or "قهرمان")
                    )
                    db.set_user_field(u["id"], "last_reminded", today)
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
        except Exception:
            pass
        await asyncio.sleep(interval)
