#!/usr/bin/env python3
"""🎨 تنظیم پروفایل ربات از طریق Bot API.

این اسکریپت این‌ها را ست می‌کند (همه چیز به‌جز تصویر پروفایل):
✅ اسم نمایشی (display name)
✅ بیوگرافی کوتاه (about)
✅ متن پیش‌نمایش (description — قبل از شروع چت)
✅ منوی دستورها (commands menu)

اجرا:
    python scripts/setup_bot_profile.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from aiogram import Bot  # noqa: E402
from aiogram.types import BotCommand  # noqa: E402
from src.config import BOT_TOKEN, validate  # noqa: E402

COLOR_NAME = "Ghayoomi Examer 🎓"

SHORT_DESCRIPTION = (
    "🎓 Ghayoomi Examer — فلش‌کارت و آزمون انگلیسی دهم تا دوازدهم 📚 به سبک استاد قیومی ✨ سازنده: ARIAMIR"
)

DESCRIPTION = (
    "✨ به Ghayoomi Examer خوش اومدی!\n\n"
    "ربات رسمی «انگلیسی به سبک استاد قیومی» برای پایه‌های دهم تا دوازدهم 🎓\n\n"
    "🃏 فلش‌کارت لغات، گرامر و عبارات Vision 1/2/3\n"
    "🧪 آزمون زمان‌دار با تحلیل، درصد و تراز\n"
    "🏆 لیدربورد هفتگی، ماهانه و هر آزمون\n"
    "🔔 یادآور روزانهٔ تمرین\n\n"
    "📣 @alighayoomi_teacher | 👨‍🏫 @Alighayoomizaban\n"
    "🌐 alighayoomi.com | 👨‍💻 سازنده: ARIAMIR\n\n"
    "بزن /start و بریم! 🚀"
)

COMMANDS = [
    BotCommand(command="start", description="شروع / ورود به ربات 🚀"),
]


async def main() -> None:
    problems = validate()
    if problems:
        for p in problems:
            print(p)
        sys.exit(1)

    bot = Bot(BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"🤖 متصل به: @{me.username}")

        await bot.set_my_name(COLOR_NAME)
        await bot.set_my_short_description(SHORT_DESCRIPTION)
        await bot.set_my_description(DESCRIPTION)
        await bot.set_my_commands(COMMANDS)

        print("✅ اسم نمایشی:", COLOR_NAME)
        print("✅ بیوگرافی (about) ست شد")
        print("✅ متن پیش‌نمایش (description) ست شد")
        print("✅ منوی دستورها ست شد:", ", ".join(f"/{c.command}" for c in COMMANDS))
        print("\n🎨 فقط تصویر پروفایل مونه — اون رو خودت از طریق @BotFather بذار 😉")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
