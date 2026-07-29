"""⌨️ کیبوردهای ربات Ghayoomi Examer — منوها، اینلاین‌ها و دکمه‌ها."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import texts as T
from .utils import (
    BOOK_NAMES, CATEGORY_ICON, CATEGORIES, GRADE_BTN_STYLE, GRADE_ICON, GRADES,
    LESSONS, MAJOR_ICON, MAJORS, fmt_time_limit,
)

# ── لیبل‌های منوی اصلی ──────────────────────────

BTN_FLASH = "🃏 فلش کارت"
BTN_EXAM = "🧪 آزمون"
BTN_LB = "🏆 لیدربورد"
BTN_PROFILE = "👤 پروفایل"
BTN_HELP = "📖 راهنما"
BTN_ABOUT = "ℹ️ درباره ما و تماس با ما"
BTN_ADMIN = "🛠 پنل مدیریت"


def main_menu(is_admin: bool = False, in_admin_panel: bool = False) -> ReplyKeyboardMarkup:
    """🆕 کیبورد اصلی با چیدمان جدید:
    ردیف ۱: 🧪 آزمون (تمام عرض، طلایی)
    ردیف ۲: 🃏 فلش کارت (تمام عرض، آبی)
    ردیف ۳: 👤 پروفایل + 🏆 لیدربورد (ساده، نصف-نصف)
    ردیف ۴: 📖 راهنما + ℹ️ درباره ما (ساده، نصف-نصف)
    اگه ادمین باشه + توی پنل نباشه: ردیف ۵ = 🛠 پنل مدیریت (تمام عرض)
    """
    if in_admin_panel:
        # 🆕 کیبورد ادمین داخل پنل — فقط دستورات ادمینی
        return _admin_panel_kb()

    rows = [
        # ردیف ۱: آزمون (تمام عرض، سبز) 🆕
        [KeyboardButton(text=BTN_EXAM, style="success")],
        # ردیف ۲: فلش کارت (تمام عرض، آبی)
        [KeyboardButton(text=BTN_FLASH, style="primary")],
        # ردیف ۳: پروفایل + لیدربورد (ساده، نصف-نصف)
        [
            KeyboardButton(text=BTN_PROFILE),
            KeyboardButton(text=BTN_LB),
        ],
        # ردیف ۴: راهنما + درباره ما (ساده، نصف-نصف)
        [
            KeyboardButton(text=BTN_HELP),
            KeyboardButton(text=BTN_ABOUT),
        ],
    ]
    if is_admin:
        # ردیف ۵ فقط برای ادمین: پنل مدیریت (تمام عرض)
        rows.append([KeyboardButton(text=BTN_ADMIN, style="primary")])
    return ReplyKeyboardMarkup(
        keyboard=rows, resize_keyboard=True,
        input_field_placeholder="یه گزینه انتخاب کن… 👇",
    )


def _admin_panel_kb() -> ReplyKeyboardMarkup:
    """🆕 کیبورد ادمین داخل پنل — چیدمان استاندارد، هر ردیف ۲ یا ۱ دکمه."""
    rows = [
        # ردیف ۱: آزمون (دو دکمه)
        [
            KeyboardButton(text="🧪 ساخت آزمون", style="primary"),
            KeyboardButton(text="📋 مدیریت آزمون‌ها"),
        ],
        # ردیف ۲: فلش‌کارت (دو دکمه) — ایمپورت حذف شد، مدیریت اضافه شد
        [
            KeyboardButton(text="🃏 افزودن کارت", style="primary"),
            KeyboardButton(text="🃏 مدیریت فلش‌کارت‌ها"),
        ],
        # ردیف ۳: نتایج + کاربران (دو دکمه)
        [
            KeyboardButton(text="📊 مدیریت نتایج", style="danger"),
            KeyboardButton(text="👥 مدیریت کاربران", style="success"),
        ],
        # ردیف ۴: تیم + همگانی (دو دکمه)
        [
            KeyboardButton(text="🛡 تیم مدیریت", style="danger"),
            KeyboardButton(text="📢 پیام همگانی", style="success"),
        ],
        # ردیف ۵: ویرایش متن‌ها (تک)
        [KeyboardButton(text="✏️ ویرایش متن‌ها", style="primary")],
        # ردیف ۶: بازگشت (تک)
        [KeyboardButton(text="↩️ بازگشت به منو")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows, resize_keyboard=True,
        input_field_placeholder="🛠 فرمان بده…",
    )


# ── Onboarding ─────────────────────────────────

def grade_kb(prefix: str = "onb") -> InlineKeyboardMarkup:
    """🆕 دکمهٔ پایه با ایموجی + رنگ هماهنگ (دهم=آبی، یازدهم=سبز، دوازدهم=قرمز)."""
    b = InlineKeyboardBuilder()
    for g in GRADES:
        b.button(
            text=f"{GRADE_ICON[g]} {g}",
            callback_data=f"{prefix}:grade:{g}",
            style=GRADE_BTN_STYLE.get(g, "primary"),
        )
    b.adjust(3)
    return b.as_markup()


def major_kb(prefix: str = "onb") -> InlineKeyboardMarkup:
    """🆕 رشته با ایموجی اختصاصی + رنگ هماهنگ (ریاضی=آبی، تجربی=سبز، انسانی=قرمز)."""
    b = InlineKeyboardBuilder()
    style_for = {
        "ریاضی فیزیک": "primary",
        "علوم تجربی": "success",
        "علوم انسانی": "danger",
    }
    for m in MAJORS:
        b.button(
            text=f"{MAJOR_ICON.get(m, '🎓')} {m}",
            callback_data=f"{prefix}:major:{m}",
            style=style_for.get(m, "primary"),
        )
    b.adjust(3)
    return b.as_markup()


# ── فلش کارت ───────────────────────────────────

def flash_grade_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for g in GRADES:
        b.button(text=f"{GRADE_ICON[g]} {g}", callback_data=f"fl:g:{g}")
    b.button(text=T.BTN_MENU, callback_data="fl:menu")
    b.adjust(3, 1)
    return b.as_markup()


def flash_lesson_kb(grade: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for l in LESSONS[grade]:
        b.button(
            text=f"📖 درس {l['n']}: {l['en']}",
            callback_data=f"fl:l:{grade}:{l['n']}",
        )
    b.button(text="🎲 ترکیبی (همهٔ درس‌ها)", callback_data=f"fl:all:{grade}")
    b.button(text=T.BTN_BACK, callback_data="fl:back:g")
    b.adjust(1)
    return b.as_markup()


def flash_category_kb(grade: str, lesson: int | None) -> InlineKeyboardMarkup:
    le = lesson if lesson else "all"
    b = InlineKeyboardBuilder()
    for c in CATEGORIES:
        b.button(text=f"{CATEGORY_ICON[c]} {c}", callback_data=f"fl:c:{grade}:{le}:{c}")
    b.button(text=T.BTN_BACK, callback_data=f"fl:back:l:{grade}")
    b.adjust(1, 1, 1, 1)
    return b.as_markup()


def card_kb(has_prev: bool, has_next: bool, is_flipped: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    row = []
    if has_prev:
        b.button(text="⬅️ قبلی", callback_data="fl:nav:prev")
    b.button(
        text="🔄 بچرخون" if not is_flipped else "🔄 برگردون",
        callback_data="fl:flip",
    )
    if has_next:
        b.button(text="➡️ بعدی", callback_data="fl:nav:next")
    b.button(text="✅ بلدم", callback_data="fl:mark:known")
    b.button(text="🔁 باید مرور کنم", callback_data="fl:mark:review")
    b.button(text="🏁 پایان جلسه", callback_data="fl:end")
    b.button(text=T.BTN_MENU, callback_data="fl:menu")
    b.adjust(3, 2, 1, 1)
    return b.as_markup()


# ── آزمون ──────────────────────────────────────

def exams_list_kb(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for eid, title in items:
        b.button(text=f"🧪 {title}", callback_data=f"ex:open:{eid}")
    b.button(text=T.BTN_MENU, callback_data="ex:menu")
    b.adjust(1)
    return b.as_markup()


def exam_info_kb(exam_id: int, state: str) -> InlineKeyboardMarkup:
    """state: not_started / in_progress / pending / published"""
    b = InlineKeyboardBuilder()
    if state == "not_started":
        b.button(text="▶️ شروع آزمون", callback_data=f"ex:start:{exam_id}")
    elif state == "in_progress":
        b.button(text="▶️ ادامه از جایی که مونده", callback_data=f"ex:resume:{exam_id}")
        b.button(text="🔄 شروع دوباره", callback_data=f"ex:start:{exam_id}")
    elif state == "published":
        b.button(text="📊 نتیجهٔ من", callback_data=f"ex:myresult:{exam_id}")
        b.button(text="🏆 لیدربورد این آزمون", callback_data=f"ex:lb:{exam_id}")
    b.button(text="🔙 بازگشت به لیست", callback_data="ex:list")
    b.adjust(1)
    return b.as_markup()


def exam_question_kb(attempt_id: int, total: int, idx: int,
                     options: list[str], chosen: int | None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    marks = ["🅰️", "🅱️", "🅲", "🅳"]
    for i, opt in enumerate(options, start=1):
        tick = " ✅" if chosen == i else ""
        label = opt if len(opt) <= 30 else opt[:27] + "…"
        b.button(text=f"{marks[i-1]} {label}{tick}",
                 callback_data=f"exq:a:{attempt_id}:{idx}:{i}")
    b.adjust(1)
    nav = InlineKeyboardBuilder()
    if idx > 0:
        nav.button(text="⬅️ سؤال قبل", callback_data=f"exq:n:{attempt_id}:{idx-1}")
    nav.button(text="🏁 تحویل آزمون", callback_data=f"exq:f:{attempt_id}")
    if idx < total - 1:
        nav.button(text="➡️ سؤال بعد", callback_data=f"exq:n:{attempt_id}:{idx+1}")
    nav.adjust(3)
    second = nav.as_markup().inline_keyboard
    full = [row for row in b.as_markup().inline_keyboard] + second
    return InlineKeyboardMarkup(inline_keyboard=full)


def exam_confirm_finish_kb(attempt_id: int, unanswered: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ آره، تحویل بده", callback_data=f"exq:cf:{attempt_id}")
    b.button(text=f"❌ نه، هنوز {unanswered} سؤال مونده" if unanswered else "❌ برگرد",
             callback_data=f"exq:back:{attempt_id}")
    b.adjust(1)
    return b.as_markup()


# ── لیدربورد ───────────────────────────────────

def leaderboard_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📆 هفتگی (۷ روز اخیر)", callback_data="lb:week")
    b.button(text="🗓 ماهانه (۳۰ روز اخیر)", callback_data="lb:month")
    b.button(text="🧪 لیدربورد آزمون‌ها", callback_data="lb:exams")
    b.button(text=T.BTN_MENU, callback_data="lb:menu")
    b.adjust(1)
    return b.as_markup()


def leaderboard_exams_kb(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for eid, title in items:
        b.button(text=f"🧪 {title}", callback_data=f"lb:exam:{eid}")
    b.button(text=T.BTN_BACK, callback_data="lb:back")
    b.adjust(1)
    return b.as_markup()


def back_to_lb_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=T.BTN_BACK, callback_data="lb:back")
    return b.as_markup()


# ── پروفایل ────────────────────────────────────

def profile_kb(reminder_on: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ ویرایش پروفایل", callback_data="pf:edit")
    b.button(text="🧪 کارنامهٔ آزمون‌ها", callback_data="pf:exams")
    b.button(
        text="🔔 یادآور روزانه ✅" if reminder_on else "🔕 یادآور روزانه ❌",
        callback_data="pf:reminder",
    )
    b.adjust(1)
    return b.as_markup()


def profile_edit_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✍️ نام", callback_data="pf:e:name")
    b.button(text="📚 پایه", callback_data="pf:e:grade")
    b.button(text="🎓 رشته", callback_data="pf:e:major")
    b.button(text=T.BTN_BACK, callback_data="pf:back")
    b.adjust(3, 1)
    return b.as_markup()


def edit_grade_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for g in GRADES:
        b.button(text=f"{GRADE_ICON[g]} {g}", callback_data=f"pf:g:{g}")
    b.button(text=T.BTN_CANCEL, callback_data="pf:back")
    b.adjust(3, 1)
    return b.as_markup()


def edit_major_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for m in MAJORS:
        b.button(text=f"{MAJOR_ICON.get(m, '🎓')} {m}", callback_data=f"pf:m:{m}")
    b.button(text=T.BTN_CANCEL, callback_data="pf:back")
    b.adjust(3, 1)
    return b.as_markup()


def reminder_kb(on: bool, hour: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="✅ روشن" if not on else "❌ خاموش",
        callback_data="pf:r:toggle",
    )
    hours = [7, 9, 12, 15, 18, 20, 22]
    row = []
    for h in hours:
        mark = "•" if h == hour else ""
        row.append((f"🕐 {h}:۰۰{mark}", f"pf:r:h:{h}"))
    for text, cb in row:
        b.button(text=text, callback_data=cb)
    b.button(text=T.BTN_BACK, callback_data="pf:back")
    b.adjust(1, 4, 3, 1)
    return b.as_markup()


# ── درباره ما – لینک‌ها ────────────────────────

def about_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📣 کانال آموزشی", url="https://t.me/alighayoomi_teacher")
    b.button(text="👨‍🏫 ارتباط مستقیم با استاد", url="https://t.me/Alighayoomizaban")
    b.button(text="🌐 وب‌سایت", url="https://alighayoomi.com")
    b.button(text="📸 اینستاگرام", url="https://instagram.com/alighayoomiofficial")
    b.button(text="🎬 آپارات", url="https://www.aparat.com/ALIGHAYOOMI_teacher")
    # 🆕 ثبت سفارش ربات: سبز کم‌رنگ (success)
    b.button(text="🤖 ثبت سفارش ساخت ربات", style="success", url="https://t.me/ARIAMIR_IR")
    # 🆕 کانال ARIAMIR: طلایی (primary با متن متمایز)
    b.button(text="📡 کانال ARIAMIR", style="primary", url="https://t.me/Ariamir_academy")
    b.adjust(1)
    return b.as_markup()


# ── پنل ادمین ──────────────────────────────────

def admin_menu_kb(is_owner: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🧪 ساخت آزمون جدید", callback_data="ad:exam:new", style="primary")
    b.button(text="📋 مدیریت آزمون‌ها", callback_data="ad:exam:list")
    b.button(text="🃏 مدیریت فلش‌کارت‌ها", callback_data="ad:card:menu", style="primary")
    b.button(text="📊 مدیریت نتایج", callback_data="ad:results", style="danger")
    b.button(text="👥 مدیریت کاربران", callback_data="ad:users")
    b.button(text="🛡 تیم مدیریت", callback_data="ad:admins")
    b.button(text="📢 پیام همگانی", callback_data="ad:bc", style="success")
    b.button(text="✏️ ویرایش متن‌ها", callback_data="ad:content")
    b.button(text=T.BTN_MENU, callback_data="ad:menu")
    b.adjust(2, 2, 2, 1, 2, 1)
    return b.as_markup()


def exam_grade_kb(prefix: str) -> InlineKeyboardMarkup:
    """🆕 دکمهٔ پایه در ویزارد ادمین — رنگ هماهنگ با هر پایه."""
    b = InlineKeyboardBuilder()
    for g in GRADES:
        b.button(
            text=f"{GRADE_ICON[g]} {g}",
            callback_data=f"{prefix}:g:{g}",
            style=GRADE_BTN_STYLE.get(g, "primary"),
        )
    b.button(text=T.BTN_CANCEL, callback_data=f"{prefix}:cancel")
    b.adjust(3, 1)
    return b.as_markup()


def exam_lessons_select_kb(grade: str, selected: list[int]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for l in LESSONS[grade]:
        tick = "✅ " if l["n"] in selected else ""
        b.button(
            text=f"{tick}📖 درس {l['n']}: {l['en']}",
            callback_data=f"adx:l:{l['n']}",
        )
    b.button(text="✅ تأیید درس‌ها", callback_data="adx:l:done", style="success")
    b.button(text=T.BTN_BACK, callback_data="adx:back")      # 🐛 FIX
    b.button(text=T.BTN_CANCEL, callback_data="adx:cancel")
    b.adjust(1)
    return b.as_markup()


def exam_time_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    times = [
        ("♾ بدون زمان", 0), ("⏱ ۱۰ دقیقه", 600), ("⏱ ۲۰ دقیقه", 1200),
        ("⏱ ۳۰ دقیقه", 1800), ("⏱ ۴۵ دقیقه", 2700), ("⏱ ۶۰ دقیقه", 3600),
    ]
    for label, sec in times:
        b.button(text=label, callback_data=f"adx:t:{sec}")
    b.button(text=T.BTN_BACK, callback_data="adx:back")      # 🐛 FIX
    b.button(text=T.BTN_CANCEL, callback_data="adx:cancel")
    b.adjust(3, 3, 1, 1)
    return b.as_markup()


def exam_mode_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✍️ ساخت دستی سؤال‌ها", callback_data="adx:mode:manual", style="primary")
    b.button(text="📥 ایمپورت از فایل/گوگل‌شیت", callback_data="adx:mode:file", style="success")
    b.button(text=T.BTN_BACK, callback_data="adx:back")      # 🐛 FIX
    b.button(text=T.BTN_CANCEL, callback_data="adx:cancel")
    b.adjust(1)
    return b.as_markup()


def exam_question_correct_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    marks = ["🅰️", "🅱️", "🅲", "🅳"]
    for i, m in enumerate(marks, start=1):
        b.button(text=f"{m} گزینه {i}", callback_data=f"adx:corr:{i}")
    b.adjust(4)
    return b.as_markup()


def exam_q_next_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📝 سؤال بعدی", callback_data="adx:nextq")
    b.button(text="🏁 پایان آزمون‌سازی", callback_data="adx:finalq")
    b.adjust(2)
    return b.as_markup()


def skip_kb(prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=T.BTN_SKIP, callback_data=f"{prefix}:skip")
    return b.as_markup()


def admin_exams_list_kb(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for eid, title in items:
        b.button(text=f"🧪 {title}", callback_data=f"ad:ex:open:{eid}")
    b.button(text=T.BTN_BACK, callback_data="ad:back")
    b.button(text=T.BTN_MENU, callback_data="ad:menu")
    b.adjust(1)
    return b.as_markup()


def admin_exam_detail_kb(exam_id: int, is_active: bool, published: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="🔴 غیرفعال کن" if is_active else "🟢 فعال کن",
        callback_data=f"ad:ex:toggle:{exam_id}",
    )
    if not published:
        b.button(text="✅ انتشار نتایج", callback_data=f"ad:ex:publish:{exam_id}")
    b.button(text="🗑 حذف آزمون", callback_data=f"ad:ex:del:{exam_id}")
    b.button(text=T.BTN_BACK, callback_data="ad:exam:list")
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def admin_results_kb(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for eid, title in items:
        b.button(text=title, callback_data=f"ad:res:open:{eid}")
    b.button(text=T.BTN_BACK, callback_data="ad:back")
    b.button(text=T.BTN_MENU, callback_data="ad:menu")
    b.adjust(1)
    return b.as_markup()


def admin_publish_confirm_kb(exam_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله، منتشر کن", callback_data=f"ad:res:publish:{exam_id}")
    b.button(text=T.BTN_CANCEL, callback_data="ad:results")
    b.adjust(1)
    return b.as_markup()


def confirm_kb(prefix: str, payload: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله، مطمئنم", callback_data=f"{prefix}:yes:{payload}")
    b.button(text=T.BTN_CANCEL, callback_data=f"{prefix}:no")
    b.adjust(1)
    return b.as_markup()


def user_admin_kb(uid: int, is_blocked: bool, role: str, viewer_is_owner: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="🔓 رفع مسدودی" if is_blocked else "🔒 مسدود کن",
        callback_data=f"ad:u:block:{uid}",
    )
    if viewer_is_owner and role != "owner":
        b.button(
            text="➖ حذف ادمین" if role == "admin" else "🛡 ادمین کن",
            callback_data=f"ad:u:role:{uid}",
        )
    b.button(text="🔄 تازه‌سازی آمار", callback_data=f"ad:u:refresh:{uid}")
    b.button(text=T.BTN_BACK, callback_data="ad:users:back")
    b.button(text=T.BTN_MENU, callback_data="ad:menu")
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def card_manage_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ افزودن دستی کارت", callback_data="ad:card:add")
    b.button(text="📥 ایمپورت از فایل/گوگل‌شیت", callback_data="ad:card:import")
    b.button(text=T.BTN_BACK, callback_data="ad:back")
    b.adjust(1)
    return b.as_markup()


def card_lesson_kb(grade: str, prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for l in LESSONS[grade]:
        b.button(
            text=f"📖 درس {l['n']}: {l['en']}",
            callback_data=f"{prefix}:l:{l['n']}",
        )
    b.button(text=T.BTN_BACK, callback_data="ad:card:menu")   # 🐛 FIX
    b.button(text=T.BTN_CANCEL, callback_data=f"{prefix}:cancel")
    b.adjust(1)
    return b.as_markup()


def card_category_kb(prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for c in CATEGORIES:
        b.button(text=f"{CATEGORY_ICON[c]} {c}", callback_data=f"{prefix}:c:{c}")
    b.button(text=T.BTN_BACK, callback_data="ad:card:menu")   # 🐛 FIX
    b.adjust(3, 1)
    return b.as_markup()


def card_saved_next_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ کارت بعدی", callback_data="ad:card:add")
    b.button(text="🏁 برگرد به پنل", callback_data="ad:back")
    b.adjust(2)
    return b.as_markup()


def content_edit_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="ℹ️ درباره ما", callback_data="ad:ct:about")
    b.button(text="📬 تماس با ما", callback_data="ad:ct:contact")
    b.button(text="📖 راهنما", callback_data="ad:ct:guide")
    b.button(text=T.BTN_BACK, callback_data="ad:back")
    b.button(text=T.BTN_MENU, callback_data="ad:menu")
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def bc_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ ارسال", callback_data="ad:bc:send", style="success")
    b.button(text=T.BTN_CANCEL, callback_data="ad:bc:cancel")
    b.adjust(1)
    return b.as_markup()


# 🆕 کیبورد فیلتر گیرندگان (تیک چندگانه)
def bc_filter_kb(grades: list[str], majors: list[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📚 پایه:", callback_data="bc:noop")
    for g in GRADES:
        mark = " ✅" if g in grades else ""
        b.button(
            text=f"{GRADE_ICON[g]} {g}{mark}",
            callback_data=f"ad:bc:g:{g}",
        )
    b.button(text="🎓 رشته:", callback_data="bc:noop")
    for m in MAJORS:
        mark = " ✅" if m in majors else ""
        b.button(
            text=f"{m}{mark}",
            callback_data=f"ad:bc:m:{m}",
        )
    b.button(text="➡️ مرحلهٔ بعد (تأیید)", callback_data="ad:bc:next", style="success")
    b.button(text=T.BTN_CANCEL, callback_data="ad:bc:cancel")
    # چیدمان: ۱ دکمهٔ هدر + ۳ پایه، ۱ هدر + ۳ رشته، ۲ دکمهٔ پایانی
    b.adjust(1, 3, 1, 3, 1, 1)
    return b.as_markup()


# 🆕 کیبورد بعد از ارسال موفق — ادامه یا بازگشت
def bc_after_send_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📝 پیام بعدی", callback_data="ad:bc:again", style="primary")
    b.button(text="↩️ بازگشت به پنل", callback_data="ad:bc:back_panel")
    b.adjust(2)
    return b.as_markup()


def kb_menu_only() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=T.BTN_MENU, callback_data="gen:menu")
    return b.as_markup()


# 🐛 FIX: دکمهٔ بازگشت در مدیریت کاربران + فیلتر و تیم مدیریت
def users_menu_kb() -> InlineKeyboardMarkup:
    """کیبورد صفحهٔ مدیریت کاربران — با فیلتر ادمین و لینک تیم مدیریت."""
    b = InlineKeyboardBuilder()
    b.button(text="🛡 فقط ادمین‌ها", callback_data="ad:users:filter:admins")
    b.button(text="👥 همه کاربران", callback_data="ad:users:filter:all")
    b.button(text="🛡 تیم مدیریت", callback_data="ad:admins")
    b.button(text=T.BTN_BACK, callback_data="ad:users:back")
    b.button(text=T.BTN_MENU, callback_data="ad:menu")
    b.adjust(2, 1, 2)
    return b.as_markup()
