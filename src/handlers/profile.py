"""👤 پروفایل — آمار، ویرایش اطلاعات و یادآور روزانه."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..context import get_db
from .. import keyboards as K, texts as T
from ..states import EditProfile
from ..utils import GRADE_ICON, fmt_duration

router = Router()


async def _profile_text(db, uid: int) -> tuple[str, bool]:
    user = db.get_user(uid)
    cards = db.user_cards_viewed(uid)
    exams = len([a for a in db.user_attempts(uid) if a["finished_at"]])
    avg = db.user_avg_percent(uid)
    best = db.user_best_rank(uid)
    points = db.user_points(uid)
    week_pts = db.user_points(uid, days=7)
    lb_pos = db.leaderboard_user_pos(uid, days=30)
    extra = T.PROFILE_EXTRA_RANK.format(lb_pos=lb_pos) if lb_pos else T.PROFILE_NO_RANK
    text = T.PROFILE.format(
        name=user["name"], grade=user["grade"],
        grade_icon=GRADE_ICON.get(user["grade"], "📚"),
        major=user["major"], uid=uid,
        cards=cards, exams=exams, avg=avg,
        best_rank=f"#{best}" if best else "—",
        points=points, week_pts=week_pts, extra=extra,
    )
    return text, bool(user["reminder_on"])


@router.message(F.text == K.BTN_PROFILE)
async def profile_home(message: Message, state: FSMContext):
    db = get_db()
    db.touch(message.from_user.id)
    await state.clear()
    text, reminder_on = await _profile_text(db, message.from_user.id)
    await message.answer(text, reply_markup=K.profile_kb(reminder_on))


# ── کارنامهٔ آزمون‌ها ─────────────────────────

@router.callback_query(F.data == "pf:exams")
async def my_exam_reports(call: CallbackQuery):
    db = get_db()
    atts = db.user_attempts(call.from_user.id)
    if not atts:
        await call.answer("🧪 هنوز توی هیچ آزمونی شرکت نکردی!", show_alert=True)
        return
    lines = []
    for a in atts[:15]:
        if not a["finished_at"]:
            lines.append(f"🟡 <b>{a['title']}</b> — نیمه‌تموم (ادامه بده!)")
        elif a["results_published"]:
            lines.append(
                f"🏁 <b>{a['title']}</b> — {a['percent']}٪ | ⭐ تراز {round(a['taraz'],0)} | 🏅 رتبه #{a['rank_pos']}"
            )
        else:
            lines.append(f"⏳ <b>{a['title']}</b> — ثبت‌شده، در انتظار انتشار نتیجه")
    await call.message.edit_text(
        "🧾 <b>کارنامهٔ آزمون‌هات:</b>\n\n" + "\n".join(lines),
        reply_markup=K.back_to_lb_menu_kb(),
    )
    await call.answer()


# ── ویرایش پروفایل ─────────────────────────────

@router.callback_query(F.data == "pf:edit")
async def edit_menu(call: CallbackQuery):
    await call.message.edit_text(T.EDIT_MENU, reply_markup=K.profile_edit_kb())
    await call.answer()


@router.callback_query(F.data == "pf:back")
async def edit_back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    db = get_db()
    text, reminder_on = await _profile_text(db, call.from_user.id)
    await call.message.edit_text(text, reply_markup=K.profile_kb(reminder_on))
    await call.answer()


@router.callback_query(F.data == "pf:e:name")
async def edit_name_ask(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.name)
    await call.message.edit_text(T.EDIT_NAME_ASK)
    await call.answer()


@router.message(EditProfile.name)
async def edit_name_save(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not (1 < len(name) < 60):
        await message.answer(T.INVALID_NAME)
        return
    db = get_db()
    db.set_user_field(message.from_user.id, "name", name)
    await state.clear()
    await message.answer(T.EDIT_SAVED)
    text, reminder_on = await _profile_text(db, message.from_user.id)
    await message.answer(text, reply_markup=K.profile_kb(reminder_on))


@router.callback_query(F.data == "pf:e:grade")
async def edit_grade_ask(call: CallbackQuery):
    await call.message.edit_text("📚 <b>پایهٔ جدیدت رو انتخاب کن:</b>", reply_markup=K.edit_grade_kb())
    await call.answer()


@router.callback_query(F.data == "pf:e:major")
async def edit_major_ask(call: CallbackQuery):
    await call.message.edit_text("🎓 <b>رشتهٔ جدیدت رو انتخاب کن:</b>", reply_markup=K.edit_major_kb())
    await call.answer()


@router.callback_query(F.data.startswith("pf:g:"))
async def edit_grade_save(call: CallbackQuery):
    grade = call.data.split(":")[-1]
    db = get_db()
    db.set_user_field(call.from_user.id, "grade", grade)
    await call.answer(T.EDIT_SAVED, show_alert=True)
    text, reminder_on = await _profile_text(db, call.from_user.id)
    await call.message.edit_text(text, reply_markup=K.profile_kb(reminder_on))


@router.callback_query(F.data.startswith("pf:m:"))
async def edit_major_save(call: CallbackQuery):
    major = call.data.split(":")[-1]
    db = get_db()
    db.set_user_field(call.from_user.id, "major", major)
    await call.answer(T.EDIT_SAVED, show_alert=True)
    text, reminder_on = await _profile_text(db, call.from_user.id)
    await call.message.edit_text(text, reply_markup=K.profile_kb(reminder_on))


# ── یادآور روزانه ──────────────────────────────

@router.callback_query(F.data == "pf:reminder")
async def reminder_menu(call: CallbackQuery):
    db = get_db()
    user = db.get_user(call.from_user.id)
    status = "✅ روشن" if user["reminder_on"] else "❌ خاموش"
    await call.message.edit_text(
        T.REMINDER_MENU.format(status=status, hour=user["reminder_hour"]),
        reply_markup=K.reminder_kb(bool(user["reminder_on"]), user["reminder_hour"]),
    )
    await call.answer()


@router.callback_query(F.data == "pf:r:toggle")
async def reminder_toggle(call: CallbackQuery):
    db = get_db()
    user = db.get_user(call.from_user.id)
    new_val = 0 if user["reminder_on"] else 1
    db.set_user_field(call.from_user.id, "reminder_on", new_val)
    await call.answer("🔔 یادآور روشن شد! از فردا یادت می‌ندازم 😊" if new_val else "🔕 یادآور خاموش شد")
    user = db.get_user(call.from_user.id)
    status = "✅ روشن" if user["reminder_on"] else "❌ خاموش"
    await call.message.edit_text(
        T.REMINDER_MENU.format(status=status, hour=user["reminder_hour"]),
        reply_markup=K.reminder_kb(bool(user["reminder_on"]), user["reminder_hour"]),
    )


@router.callback_query(F.data.startswith("pf:r:h:"))
async def reminder_set_hour(call: CallbackQuery):
    hour = int(call.data.split(":")[-1])
    db = get_db()
    db.set_user_field(call.from_user.id, "reminder_hour", hour)
    db.set_user_field(call.from_user.id, "reminder_on", 1)
    await call.answer(f"⏰ باشه! هر روز ساعت {hour}:۰۰ یادآوری می‌کنم 🔔")
    user = db.get_user(call.from_user.id)
    status = "✅ روشن" if user["reminder_on"] else "❌ خاموش"
    await call.message.edit_text(
        T.REMINDER_MENU.format(status=status, hour=user["reminder_hour"]),
        reply_markup=K.reminder_kb(bool(user["reminder_on"]), user["reminder_hour"]),
    )
