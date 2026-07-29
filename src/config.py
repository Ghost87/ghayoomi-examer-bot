"""⚙️ تنظیمات مرکزی ربات — همه چیز از فایل .env خوانده می‌شود."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:  # dot نصب نبود، مشکلی نیست
    pass


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

OWNER_ID: int = int(os.getenv("OWNER_ID", "0") or 0)

ADMIN_IDS: list[int] = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "ghayoomi.db"))

# 🔐 ورود مخفی ادمین — یوزرنیم/رمز پنل مدیریت
ADMIN_LOGIN: str = os.getenv("ADMIN_LOGIN", "CHANGE_ME")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "CHANGE_ME")

BOT_NAME = "Ghayoomi Examer"
BOT_USERNAME = "@GhayoomiARBot"
BRAND_NAME = "کالج آموزش زبان علی قیومی"


def validate() -> list[str]:
    """بررسی می‌کند تنظیمات حیاتی پر شده‌اند یا نه."""
    problems: list[str] = []
    if not BOT_TOKEN:
        problems.append("❌ BOT_TOKEN خالی است — از @BotFather بگیر و داخل .env بگذار.")
    if not OWNER_ID:
        problems.append("❌ OWNER_ID خالی است — آیدی عددی خودت را در .env بگذار.")
    return problems
