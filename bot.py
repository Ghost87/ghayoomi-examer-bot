"""🤖 نقطهٔ ورود ربات — اجرا: python bot.py"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src import context
from src.config import BOT_TOKEN, DB_PATH, validate
from src.db import DB
from src.handlers import register_all
from src.scheduler import reminder_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ghayoomi")


async def main() -> None:
    problems = validate()
    if problems:
        for p in problems:
            logger.error(p)
        logger.error("⛔ فایل .env را کامل کن و دوباره بیا — راهنما: docs/SETUP.md")
        sys.exit(1)

    context.db = DB(DB_PATH)
    logger.info("🗄 دیتابیس آماده شد: %s", DB_PATH)

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    register_all(dp)

    asyncio.create_task(reminder_loop(bot))
    logger.info("🔔 زمان‌بند یادآور روزانه فعال شد")

    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("🚀 ربات روشن شد: @%s (%s)", me.username, me.full_name)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        context.db.close()


if __name__ == "__main__":
    asyncio.run(main())
