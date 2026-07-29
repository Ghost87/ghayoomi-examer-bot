"""🧮 توابع کمکی: پایه‌ها، رشته‌ها، ساختار کتاب‌ها، تراز و زمان."""
from __future__ import annotations

import math
from datetime import datetime, timedelta

# ── ثابت‌های محصول ──────────────────────────────

GRADES = ["دهم", "یازدهم", "دوازدهم"]

MAJORS = ["ریاضی فیزیک", "علوم تجربی", "علوم انسانی"]

# آیکون اختصاصی هر رشته 📐❤️📜
MAJOR_ICON = {
    "ریاضی فیزیک": "📐",
    "علوم تجربی": "🧬",
    "علوم انسانی": "📜",
}

CATEGORIES = ["لغات", "گرامر", "عبارات"]

# 🆕 هر پایه یه ایموجی + یه رنگ (سبز/قرمز/آبی)
GRADE_ICON = {
    "دهم": "📘",      # آبی
    "یازدهم": "📗",   # سبز
    "دوازدهم": "📕",   # قرمز
}

# 🆕 استایل دکمهٔ هر پایه — هماهنگ با رنگ ایموجی
GRADE_BTN_STYLE = {
    "دهم": "primary",    # آبی
    "یازدهم": "success", # سبز
    "دوازدهم": "danger", # قرمز
}

CATEGORY_ICON = {"لغات": "🗣", "گرامر": "✏️", "عبارات": "💬"}

BOOK_NAMES = {
    "دهم": "📕 Vision 1 — پایه دهم",
    "یازدهم": "📗 Vision 2 — پایه یازدهم",
    "دوازدهم": "📘 Vision 3 — پایه دوازدهم",
}

# ساختار رسمی کتاب‌های درسی Vision 1 / 2 / 3
LESSONS: dict[str, list[dict]] = {
    "دهم": [
        {"n": 1, "en": "Saving Nature", "fa": "حفاظت از طبیعت"},
        {"n": 2, "en": "Wonders of Creation", "fa": "شگفتی‌های خلقت"},
        {"n": 3, "en": "The Value of Knowledge", "fa": "ارزش دانش"},
        {"n": 4, "en": "Traveling the World", "fa": "سفر دور دنیا"},
    ],
    "یازدهم": [
        {"n": 1, "en": "Understanding People", "fa": "درک آدم‌ها"},
        {"n": 2, "en": "A Healthy Lifestyle", "fa": "سبک زندگی سالم"},
        {"n": 3, "en": "Art and Culture", "fa": "هنر و فرهنگ"},
    ],
    "دوازدهم": [
        {"n": 1, "en": "Sense of Appreciation", "fa": "حس قدردانی"},
        {"n": 2, "en": "Look it Up", "fa": "جستجو و تحقیق"},
        {"n": 3, "en": "Renewable Energy", "fa": "انرژی تجدید پذیر"},
    ],
}

LESSON_TITLES_FA: dict[str, list[str]] = {
    g: [l["fa"] for l in ls] for g, ls in LESSONS.items()
}

# امتیازدهی
POINTS_CARD_VIEW = 5       # دیدن هر فلش‌کارت جدید (یک بار در روز برای هر کارت)
POINTS_PER_PERCENT = 1     # به ازای هر درصد آزمون


# ── زمان ──────────────────────────────────────────

def now() -> datetime:
    return datetime.now()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def days_ago_str(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_num(value) -> str:
    """تبدیل اعداد لاتین به فارسی برای نمایش زیباتر."""
    return str(value).translate(_FA_DIGITS)


def fmt_time_limit(seconds: int) -> str:
    if not seconds:
        return "♾ بدون محدودیت زمانی"
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return fa_num(f"⏳ {h} ساعت و {m} دقیقه")
    return fa_num(f"⏳ {m} دقیقه" + (f" و {s} ثانیه" if s else ""))


def fmt_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return fa_num(f"{h} ساعت و {m} دقیقه")
    return fa_num(f"{m} دقیقه و {s} ثانیه" if m else f"{s} ثانیه")


# ── آمار و تراز ──────────────────────────────────

def compute_taraz(percents: list[float]) -> list[float]:
    """تراز ساده‌شده: میانگین ۵۰۰۰ و انحراف معیار ۱۰۰۰ — سبک آزمون‌های سراسری."""
    if not percents:
        return []
    if len(percents) == 1:
        return [5000.0]
    mean = sum(percents) / len(percents)
    var = sum((p - mean) ** 2 for p in percents) / len(percents)
    std = math.sqrt(var)
    if std < 1:
        return [5000.0 for _ in percents]
    return [5000.0 + 1000.0 * (p - mean) / std for p in percents]


def rank_key(payload: dict) -> tuple:
    """کلید رتبه‌بندی: درصد بالاتر، بعد زمان کمتر."""
    return (-payload["percent"], payload["duration"])


def medal(i: int) -> str:
    return {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"🔹 {i + 1}.")


def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def dt_diff_seconds(start: str, end: str | None = None) -> int:
    end = end or now_str()
    return int((parse_dt(end) - parse_dt(start)).total_seconds())
