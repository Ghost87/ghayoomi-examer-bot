"""🛠 پنل مدیریت — نسخهٔ ساده و مطمئن.

🔧 فلسفه: بدون فیلتر سراسری، بدون history، بدون auto-register.
هر handler کاملاً مستقل کار می‌کنه. اگه handler عوض بشه،
مدیریت خطا داخل خودشه.
"""
from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..context import get_db
from .. import importer, keyboards as K, texts as T
from ..states import (
    AdminCardWizard, AdminExamWizard, AdminSearch, Broadcast, EditContent,
)
from ..utils import (
    CATEGORY_ICON, GRADE_ICON, GRADES, LESSONS, fmt_duration, fmt_time_limit,
    now_str,
)

router = Router()


def _grade_line(grade: str) -> str:
    return f"{GRADE_ICON.get(grade, '📚')} {grade}"


# ═══════════════ توابع کمکی ═══════════════

def _is_admin(uid: int) -> bool:
    """🆕 چک ساده: اگه توی env OWNER_ID یا ADMIN_IDS باشه، ادمینه.
    یا اگه توی db نقش owner/admin داشته باشه."""
    from ..config import OWNER_ID, ADMIN_IDS
    if uid == OWNER_ID or uid in ADMIN_IDS:
        return True
    db = get_db()
    user = db.get_user(uid)
    return bool(user) and user["role"] in ("owner", "admin")


def _wizard_back_kb(back_cb: str = "ad:back") -> InlineKeyboardMarkup:
    """🆕 کیبورد ساده فقط با دکمهٔ بازگشت."""
    b = InlineKeyboardBuilder()
    b.button(text="🔙 بازگشت", callback_data=back_cb)
    return b.as_markup()


# ═══════════════ کیبورد Reply ادمین ═══════════════

@router.message(F.text == "🧪 ساخت آزمون")
async def admin_kb_exam_new(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AdminExamWizard.title)
    await message.answer(
        T.ADMIN_NEW_EXAM_TITLE,
        reply_markup=_wizard_back_kb("ad:exam:back"),
    )


@router.message(F.text == "📋 مدیریت آزمون‌ها")
async def admin_kb_exam_list(message: Message):
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    exams = db.list_exams()
    if not exams:
        await message.answer("📋 هنوز آزمونی ساخته نشده.")
        return
    items = "\n".join(f"• {e['title']}" for e in exams[:20])
    await message.answer(
        f"📋 <b>آزمون‌ها ({len(exams)}):</b>\n\n{items}\n\n👇 انتخاب کن:",
        reply_markup=K.admin_exams_list_kb([(e["id"], e["title"]) for e in exams[:20]]),
    )


@router.message(F.text == "🃏 افزودن کارت")
async def admin_kb_card_add(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AdminCardWizard.grade)
    await message.answer(
        T.ADMIN_ADD_CARD_PICK_GRADE,
        reply_markup=K.exam_grade_kb("adc"),
    )


@router.message(F.text == "🃏 مدیریت فلش‌کارت‌ها")
async def admin_kb_card_manage(message: Message):
    """کیبورد reply → لیست پایه‌ها (callback)."""
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    counts = db.card_counts()
    if not counts:
        await message.answer(
            "🃏 <b>مدیریت فلش‌کارت‌ها</b>\n\n🏜 هنوز کارتی ساخته نشده.",
            reply_markup=K.card_manage_menu_kb(),
        )
        return
    items = []
    for r in counts[:30]:
        lesson = LESSONS[r["grade"]][r["lesson"] - 1]["en"] if r["lesson"] <= len(LESSONS[r["grade"]]) else f"درس {r['lesson']}"
        items.append(
            f"{GRADE_ICON[r['grade']]} {r['grade']} | 📖 {lesson} | {CATEGORY_ICON.get(r['category'], '🗂')} {r['category']}: <b>{r['c']}</b>"
        )
    text = "🃏 <b>مدیریت فلش‌کارت‌ها</b>\n\n" + "\n".join(items) + "\n\n👇 یه پایه انتخاب کن:"
    b = InlineKeyboardBuilder()
    for g in GRADES:
        b.button(text=f"{GRADE_ICON[g]} {g}", callback_data=f"adm:card:g:{g}")
    b.button(text="🔙 بازگشت", callback_data="ad:back")
    b.adjust(3, 1)
    await message.answer(text, reply_markup=b.as_markup())


@router.message(F.text == "📊 مدیریت نتایج")
async def admin_kb_results(message: Message):
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    exams = db.list_exams()
    if not exams:
        await message.answer("🧪 هنوز آزمونی نیست.")
        return
    items = []
    buttons = []
    for e in exams:
        atts = db.exam_attempts(e["id"])
        if not atts:
            status = "🔴"
        elif e["results_published"]:
            status = "🟢"
        else:
            status = "🟡"
        label = f"{status} {e['title']} ({len(atts)} نفر)"
        items.append(label)
        buttons.append((e["id"], label))
    await message.answer(
        T.ADMIN_RESULTS_MENU.format(items="\n".join(items)),
        reply_markup=K.admin_results_kb(buttons[:20]),
    )


@router.message(F.text == "👥 مدیریت کاربران")
async def admin_kb_users(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    db = get_db()
    counts = db.user_counts()
    admins = db.admin_ids()
    await state.set_state(AdminSearch.user)
    await state.update_data(users_search_role=None)
    await message.answer(
        T.ADMIN_USERS_MENU.format(
            total=counts["total"], today=counts["today"],
            week=counts["week"], blocked=counts["blocked"],
            admins=len(admins),
        ),
        reply_markup=K.users_menu_kb(),
    )


@router.message(F.text == "🛡 تیم مدیریت")
async def admin_kb_admins(message: Message):
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    admins = db.con.execute(
        "SELECT * FROM users WHERE role IN ('owner','admin') ORDER BY role, id"
    ).fetchall()
    if not admins:
        text = "🛡 <b>تیم مدیریت</b>\n\nفعلاً هیچ ادمینی ثبت نشده."
    else:
        lines = []
        for a in admins:
            role_emoji = "👑" if a["role"] == "owner" else "🛡"
            username = f"@{a['username']}" if a["username"] else "—"
            lines.append(
                f"{role_emoji} <b>{a['name'] or '—'}</b>\n"
                f"    🆔 <code>{a['id']}</code> | {username}\n"
                f"    {a['grade'] or '—'} | {a['major'] or '—'}"
            )
        text = "🛡 <b>تیم مدیریت</b>\n\n" + "\n\n".join(lines)
    text += "\n\n💡 برای تغییر نقش، از «👥 مدیریت کاربران» کاربر رو سرچ کن و نقشش رو عوض کن."
    b = InlineKeyboardBuilder()
    b.button(text="↩️ بازگشت", callback_data="ad:back")
    await message.answer(text, reply_markup=b.as_markup())


@router.message(F.text == "📢 پیام همگانی")
async def admin_kb_bc(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(Broadcast.text)
    await state.update_data(bc_grades=[], bc_majors=[])
    await message.answer(T.BC_ASK)


@router.message(F.text == "✏️ ویرایش متن‌ها")
async def admin_kb_content(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer(T.EDIT_CONTENT_MENU, reply_markup=K.content_edit_kb())


@router.message(F.text == "↩️ بازگشت به منو")
async def admin_kb_back_user(message: Message, state: FSMContext):
    """خروج از پنل و برگشت به منوی کاربری."""
    await state.clear()
    await message.answer(
        T.MAIN_MENU_HINT,
        reply_markup=K.main_menu(is_admin=True, in_admin_panel=False),
    )


# ═══════════════ ساخت آزمون — callbacks ═══════════════

@router.callback_query(F.data == "ad:exam:new")
async def exam_new(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer("🚫", show_alert=True)
    await state.set_state(AdminExamWizard.title)
    await call.message.edit_text(
        T.ADMIN_NEW_EXAM_TITLE,
        reply_markup=_wizard_back_kb("ad:exam:back"),
    )
    await call.answer()


@router.callback_query(F.data == "ad:exam:back")
async def exam_back(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.edit_text("↩️ از ویزارد خارج شدی. از کیبورد پایین استفاده کن.")
    await call.answer()


@router.message(AdminExamWizard.title)
async def exam_w_title(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ عنوان خالیه! دوباره بنویس:", reply_markup=_wizard_back_kb("ad:exam:back"))
        return
    await state.update_data(exam_title=title, exam_lessons=[])
    await state.set_state(AdminExamWizard.grade)
    await message.answer(T.ADMIN_NEW_EXAM_GRADE, reply_markup=K.exam_grade_kb("adx"))


@router.callback_query(F.data.startswith("adx:g:"), AdminExamWizard.grade)
async def exam_w_grade(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    grade = call.data.split(":")[-1]
    await state.update_data(exam_grade=grade, exam_lessons=[])
    await state.set_state(AdminExamWizard.lessons)
    await call.message.edit_text(
        T.ADMIN_NEW_EXAM_LESSONS,
        reply_markup=K.exam_lessons_select_kb(grade, []),
    )
    await call.answer()


@router.callback_query(F.data == "adx:l:done", AdminExamWizard.lessons)
async def exam_w_lessons_done(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    data = await state.get_data()
    selected = data.get("exam_lessons", [])
    await state.set_state(AdminExamWizard.time)
    note = "همهٔ درس‌ها" if not selected else "درس " + " و ".join(str(s) for s in sorted(selected))
    await call.message.edit_text(
        f"📖 انتخاب شد: {note}\n\n" + T.ADMIN_NEW_EXAM_TIME,
        reply_markup=K.exam_time_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adx:l:"), AdminExamWizard.lessons)
async def exam_w_lesson_toggle(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    n = int(call.data.split(":")[-1])
    data = await state.get_data()
    selected: list = data.get("exam_lessons", [])
    selected = [x for x in selected if x != n] if n in selected else selected + [n]
    await state.update_data(exam_lessons=selected)
    await call.message.edit_text(
        T.ADMIN_NEW_EXAM_LESSONS,
        reply_markup=K.exam_lessons_select_kb(data["exam_grade"], selected),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adx:t:"), AdminExamWizard.time)
async def exam_w_time(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    sec = int(call.data.split(":")[-1])
    await state.update_data(exam_time=sec)
    data = await state.get_data()
    await state.set_state(AdminExamWizard.mode)
    lessons = data.get("exam_lessons", [])
    lessons_str = "همه" if not lessons else ",".join(str(s) for s in sorted(lessons))
    await state.update_data(exam_lessons_str=lessons_str)
    await call.message.edit_text(
        T.ADMIN_NEW_EXAM_MODE.format(
            title=data["exam_title"], grade=data["exam_grade"],
            time=fmt_time_limit(sec),
        ),
        reply_markup=K.exam_mode_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "adx:mode:manual", AdminExamWizard.mode)
async def exam_w_mode_manual(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    data = await state.get_data()
    exam_id = db.create_exam(
        title=data["exam_title"], grade=data["exam_grade"],
        lessons=data["exam_lessons_str"], time_limit=data["exam_time"],
        created_by=call.from_user.id,
    )
    await state.update_data(exam_id=exam_id, q_count=0)
    await state.set_state(AdminExamWizard.q_text)
    await call.message.edit_text(
        T.ADD_Q_TEXT.format(n=1),
        reply_markup=_wizard_back_kb("adx:back"),
    )
    await call.answer()


@router.callback_query(F.data == "adx:mode:file", AdminExamWizard.mode)
async def exam_w_mode_file(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    data = await state.get_data()
    exam_id = db.create_exam(
        title=data["exam_title"], grade=data["exam_grade"],
        lessons=data["exam_lessons_str"], time_limit=data["exam_time"],
        created_by=call.from_user.id,
    )
    await state.update_data(exam_id=exam_id)
    await state.set_state(AdminExamWizard.import_file)
    await call.message.edit_text(T.IMPORT_GUIDE, reply_markup=_wizard_back_kb("adx:back"))
    await call.answer()


@router.callback_query(F.data == "adx:back")
async def exam_w_back(call: CallbackQuery, state: FSMContext):
    """بازگشت یک مرحله در ویزارد آزمون."""
    cur = await state.get_state()
    await call.answer("↩️ برگشتی")
    if cur == AdminExamWizard.grade:
        await state.clear()
        await call.message.edit_text("↩️ از ویزارد خارج شدی.")
        return
    if cur == AdminExamWizard.lessons:
        await state.set_state(AdminExamWizard.grade)
        await call.message.edit_text(T.ADMIN_NEW_EXAM_GRADE, reply_markup=K.exam_grade_kb("adx"))
        return
    if cur == AdminExamWizard.time:
        data = await state.get_data()
        await state.set_state(AdminExamWizard.lessons)
        await call.message.edit_text(
            T.ADMIN_NEW_EXAM_LESSONS,
            reply_markup=K.exam_lessons_select_kb(data.get("exam_grade", "دهم"), data.get("exam_lessons", [])),
        )
        return
    if cur == AdminExamWizard.mode:
        data = await state.get_data()
        await state.set_state(AdminExamWizard.time)
        await call.message.edit_text(T.ADMIN_NEW_EXAM_TIME, reply_markup=K.exam_time_kb())
        return
    if cur in (AdminExamWizard.q_text, AdminExamWizard.q_opt1, AdminExamWizard.q_opt2,
               AdminExamWizard.q_opt3, AdminExamWizard.q_opt4, AdminExamWizard.q_correct,
               AdminExamWizard.q_expl):
        data = await state.get_data()
        exam_id = data.get("exam_id")
        if exam_id:
            count = get_db().exam_question_count(exam_id)
            if count > 0:
                await state.set_state(AdminExamWizard.q_done)
                await call.message.edit_text(
                    T.ADD_Q_SAVED.format(n=count),
                    reply_markup=K.exam_q_next_kb(),
                )
                return
            get_db().delete_exam(exam_id)
        await state.clear()
        await call.message.edit_text("↩️ آزمون ساخته نشد.")
        return
    if cur == AdminExamWizard.q_done:
        await state.clear()
        await call.message.edit_text("↩️ از ویزارد خارج شدی.")
        return
    if cur == AdminExamWizard.import_file:
        data = await state.get_data()
        exam_id = data.get("exam_id")
        if exam_id:
            get_db().delete_exam(exam_id)
        await state.clear()
        await call.message.edit_text("↩️ از ویزارد خارج شدی.")
        return
    await state.clear()


# ── ویزارد سؤال دستی ──────────────────────────

@router.message(AdminExamWizard.q_text)
async def qw_text(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(q_text=message.text.strip())
    await state.set_state(AdminExamWizard.q_opt1)
    await message.answer(T.ADD_Q_OPT.format(letter="🅰️"), reply_markup=_wizard_back_kb("adx:back"))


@router.message(AdminExamWizard.q_opt1)
async def qw_opt1(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(opt1=message.text.strip())
    await state.set_state(AdminExamWizard.q_opt2)
    await message.answer(T.ADD_Q_OPT.format(letter="🅱️"), reply_markup=_wizard_back_kb("adx:back"))


@router.message(AdminExamWizard.q_opt2)
async def qw_opt2(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(opt2=message.text.strip())
    await state.set_state(AdminExamWizard.q_opt3)
    await message.answer(T.ADD_Q_OPT.format(letter="🅲"), reply_markup=_wizard_back_kb("adx:back"))


@router.message(AdminExamWizard.q_opt3)
async def qw_opt3(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(opt3=message.text.strip())
    await state.set_state(AdminExamWizard.q_opt4)
    await message.answer(T.ADD_Q_OPT.format(letter="🅳"), reply_markup=_wizard_back_kb("adx:back"))


@router.message(AdminExamWizard.q_opt4)
async def qw_opt4(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(opt4=message.text.strip())
    data = await state.get_data()
    options = "\n".join(
        f"{m} {d}" for m, d in zip(T.OPT_LINE_LETTERS, [data['opt1'], data['opt2'], data['opt3'], data['opt4']])
    )
    await state.set_state(AdminExamWizard.q_correct)
    await message.answer(
        T.ADD_Q_CORRECT.format(text=data["q_text"], options=options),
        reply_markup=K.exam_question_correct_kb(),
    )


@router.callback_query(F.data.startswith("adx:corr:"), AdminExamWizard.q_correct)
async def qw_correct(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    correct = int(call.data.split(":")[-1])
    await state.update_data(q_correct=correct)
    await state.set_state(AdminExamWizard.q_expl)
    await call.message.edit_text(T.ADD_Q_EXPL, reply_markup=K.skip_kb("adx:expl"))
    await call.answer()


@router.callback_query(F.data == "adx:expl:skip", AdminExamWizard.q_expl)
async def qw_expl_skip(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    data = await state.get_data()
    exam_id = data["exam_id"]
    idx = db.exam_question_count(exam_id) + 1
    db.add_question(
        exam_id, idx, data["q_text"], data["opt1"], data["opt2"],
        data["opt3"], data["opt4"], data["q_correct"], "",
    )
    await state.update_data(q_count=idx)
    await state.set_state(AdminExamWizard.q_done)
    await call.message.edit_text(
        T.ADD_Q_SAVED.format(n=idx),
        reply_markup=K.exam_q_next_kb(),
    )
    await call.answer()


@router.message(AdminExamWizard.q_expl)
async def qw_expl(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    data = await state.get_data()
    exam_id = data["exam_id"]
    idx = db.exam_question_count(exam_id) + 1
    db.add_question(
        exam_id, idx, data["q_text"], data["opt1"], data["opt2"],
        data["opt3"], data["opt4"], data["q_correct"], message.text.strip(),
    )
    await state.update_data(q_count=idx)
    await state.set_state(AdminExamWizard.q_done)
    await message.answer(
        T.ADD_Q_SAVED.format(n=idx),
        reply_markup=K.exam_q_next_kb(),
    )


@router.callback_query(F.data == "adx:nextq", AdminExamWizard.q_done)
async def qw_next(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    data = await state.get_data()
    await state.set_state(AdminExamWizard.q_text)
    await call.message.edit_text(
        T.ADD_Q_TEXT.format(n=data.get("q_count", 0) + 1),
        reply_markup=_wizard_back_kb("adx:back"),
    )
    await call.answer()


@router.callback_query(F.data == "adx:finalq", AdminExamWizard.q_done)
async def qw_final(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    data = await state.get_data()
    exam_id = data["exam_id"]
    exam = db.get_exam(exam_id)
    count = db.exam_question_count(exam_id)
    if count == 0:
        db.delete_exam(exam_id)
        await state.clear()
        await call.message.edit_text("⚠️ هیچ سؤالی اضافه نشد — آزمون حذف شد.")
        await call.answer()
        return
    await state.clear()
    await call.message.edit_text(
        T.ADD_EXAM_DONE.format(
            title=exam["title"], count=count,
            time=fmt_time_limit(exam["time_limit"]),
            grade=exam["grade"], grade_icon=GRADE_ICON.get(exam["grade"], "📚"),
        ),
        reply_markup=K.admin_exams_list_kb([]),
    )
    await call.answer("🎉 آفرین رئیس!")


# ── ایمپورت آزمون از فایل/URL ──────────────────

@router.message(AdminExamWizard.import_file, F.document | F.text)
async def exam_import_file(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    exam_id = data["exam_id"]
    db = get_db()
    try:
        raw = await _get_raw_bytes(message)
        name = (message.document.file_name if message.document else "").lower()
        if name.endswith(".json"):
            rows = importer.parse_questions_json(raw)
        elif name.endswith((".xlsx", ".xls")):
            rows = importer.parse_questions_xlsx(raw)
        else:
            rows = importer.parse_questions_csv(raw)
    except importer.ImportError_ as e:
        await message.answer(str(e) + "\n\nدوباره بفرست 👇")
        return
    except Exception:
        await message.answer(f"{T.ERROR_GENERIC}\n\nدوباره بفرست 👇")
        return

    start_idx = db.exam_question_count(exam_id)
    for i, q in enumerate(rows, start=1):
        db.add_question(
            exam_id, start_idx + i, q["text"], q["opt1"], q["opt2"],
            q["opt3"], q["opt4"], q["correct"], q.get("explanation", ""),
        )
    await state.clear()
    exam = db.get_exam(exam_id)
    total = db.exam_question_count(exam_id)
    await message.answer(
        T.ADD_EXAM_DONE.format(
            title=exam["title"], count=total,
            time=fmt_time_limit(exam["time_limit"]),
            grade=exam["grade"], grade_icon=GRADE_ICON.get(exam["grade"], "📚"),
        )
    )


async def _get_raw_bytes(message: Message) -> bytes:
    if message.document:
        buf = await message.bot.download(message.document.file_id)
        return buf.read()
    url = (message.text or "").strip()
    if url.startswith("http"):
        return await importer.fetch_bytes(url)
    raise importer.ImportError_("😕 نه فایل بود نه لینک — فایل CSV/XLSX/JSON یا لینک گوگل‌شیت بفرست.")


# ═══════════════ مدیریت آزمون‌ها (callbacks) ═══════════════

@router.callback_query(F.data == "ad:exam:list")
async def exams_admin_list(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    exams = db.list_exams()
    if not exams:
        await call.answer("📋 هنوز آزمونی ساخته نشده.", show_alert=True)
        return
    await call.message.edit_text(
        "📋 <b>آزمون‌های ساخته‌شده:</b>\n\nروی هرکدوم بزن تا مدیریتش کنی 👇",
        reply_markup=K.admin_exams_list_kb([(e["id"], e["title"]) for e in exams[:20]]),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ad:ex:open:"))
async def exam_admin_open(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    exam = db.get_exam(exam_id)
    if not exam:
        await call.answer("😕 آزمون پیدا نشد.", show_alert=True)
        return
    count = db.exam_question_count(exam_id)
    atts = db.exam_attempts(exam_id)
    status = "🟢 فعال" if exam["is_active"] else "🔴 غیرفعال"
    pub = "✅ منتشر شده" if exam["results_published"] else "🟡 در انتظار انتشار"
    await call.message.edit_text(
        f"🧪 <b>{exam['title']}</b>\n\n"
        f"{_grade_line(exam['grade'])} | ⏱ {fmt_time_limit(exam['time_limit'])}\n"
        f"📖 درس‌ها: {exam['lessons']}\n"
        f"📝 سؤال: <b>{count}</b> | 👥 شرکت‌کننده: <b>{len(atts)}</b>\n"
        f"🚦 وضعیت: {status} | 📢 نتایج: {pub}",
        reply_markup=K.admin_exam_detail_kb(exam_id, bool(exam["is_active"]), bool(exam["results_published"])),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ad:ex:toggle:"))
async def exam_admin_toggle(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    exam = db.get_exam(exam_id)
    db.set_exam_field(exam_id, "is_active", 0 if exam["is_active"] else 1)
    await call.answer("🚦 وضعیت عوض شد")
    # بازسازی صفحه
    exam2 = db.get_exam(exam_id)
    count = db.exam_question_count(exam_id)
    atts = db.exam_attempts(exam_id)
    status = "🟢 فعال" if exam2["is_active"] else "🔴 غیرفعال"
    pub = "✅ منتشر شده" if exam2["results_published"] else "🟡 در انتظار انتشار"
    await call.message.edit_text(
        f"🧪 <b>{exam2['title']}</b>\n\n"
        f"{_grade_line(exam2['grade'])} | ⏱ {fmt_time_limit(exam2['time_limit'])}\n"
        f"📖 درس‌ها: {exam2['lessons']}\n"
        f"📝 سؤال: <b>{count}</b> | 👥 شرکت‌کننده: <b>{len(atts)}</b>\n"
        f"🚦 وضعیت: {status} | 📢 نتایج: {pub}",
        reply_markup=K.admin_exam_detail_kb(exam_id, bool(exam2["is_active"]), bool(exam2["results_published"])),
    )


@router.callback_query(F.data.startswith("ad:ex:del:"))
async def exam_admin_delete_ask(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    await call.message.edit_text(
        "🗑 <b>حذف آزمون</b>\n\nآزمون + همهٔ سؤال‌ها + نتایجش پاک می‌شه. مطمئنی؟",
        reply_markup=K.confirm_kb("ad:exdel", str(exam_id)),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ad:exdel:yes:"))
async def exam_admin_delete_yes(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    get_db().delete_exam(exam_id)
    await call.message.edit_text("🗑 آزمون حذف شد.")
    await call.answer()


@router.callback_query(F.data == "ad:exdel:no")
async def exam_admin_delete_no(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await call.message.edit_text("❌ حذف لغو شد.")
    await call.answer()


@router.callback_query(F.data.startswith("ad:ex:publish:"))
async def exam_admin_publish(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    await _publish_results(call, exam_id)


# ═══════════════ نتایج ═══════════════

@router.callback_query(F.data == "ad:results")
async def results_menu(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    exams = db.list_exams()
    if not exams:
        await call.answer("🧪 هنوز آزمونی نیست.", show_alert=True)
        return
    items = []
    buttons = []
    for e in exams:
        atts = db.exam_attempts(e["id"])
        if not atts:
            status = "🔴"
        elif e["results_published"]:
            status = "🟢"
        else:
            status = "🟡"
        label = f"{status} {e['title']} ({len(atts)} نفر)"
        items.append(label)
        buttons.append((e["id"], label))
    await call.message.edit_text(
        T.ADMIN_RESULTS_MENU.format(items="\n".join(items)),
        reply_markup=K.admin_results_kb(buttons[:20]),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ad:res:open:"))
async def results_detail(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    exam = db.get_exam(exam_id)
    atts = db.exam_attempts(exam_id)
    if not atts:
        await call.answer("🔴 هنوز کسی در این آزمون شرکت نکرده.", show_alert=True)
        return
    percents = [a["percent"] for a in atts]
    avg = round(sum(percents) / len(percents), 1)
    avg_time = fmt_duration(sum(a["duration"] for a in atts) // len(atts))
    status = "✅ منتشر شده" if exam["results_published"] else "🟡 در انتظار تأیید تو"
    kb = (K.admin_publish_confirm_kb(exam_id) if not exam["results_published"]
          else K.admin_exams_list_kb([]))
    await call.message.edit_text(
        T.ADMIN_RESULT_DETAIL.format(
            title=exam["title"], count=len(atts), avg=avg,
            top=max(percents), min=min(percents), avg_time=avg_time, status=status,
        ),
        reply_markup=kb,
    )
    await call.answer()


@router.callback_query(F.data.startswith("ad:res:publish:"))
async def results_publish(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    exam_id = int(call.data.split(":")[-1])
    await _publish_results(call, exam_id)


async def _publish_results(call: CallbackQuery, exam_id: int):
    db = get_db()
    atts = db.publish_exam_results(exam_id)
    exam = db.get_exam(exam_id)
    notified = 0
    for a in atts:
        att = db.get_attempt_by_id(a["id"])
        participants = len(atts)
        percent = att["percent"]
        verdict = (T.VERDICT["top"] if percent >= 80 else
                   T.VERDICT["good"] if percent >= 60 else
                   T.VERDICT["mid"] if percent >= 40 else T.VERDICT["low"])
        try:
            await call.bot.send_message(
                att["user_id"],
                T.RESULTS_PUBLISHED_USER.format(
                    title=exam["title"], score=att["score"], total=att["total"],
                    percent=percent, taraz=round(att["taraz"], 0),
                    rank=att["rank_pos"], participants=participants,
                    duration=fmt_duration(att["duration"]), verdict=verdict,
                ),
            )
            notified += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await call.message.edit_text(
        T.PUBLISH_DONE_ADMIN.format(title=exam["title"], count=len(atts)) +
        f"\n\n📩 ارسال موفق: <b>{notified}</b> از {len(atts)}"
    )
    await call.answer("📣 منتشر شد!")


# ═══════════════ فلش‌کارت — callbacks ═══════════════

@router.callback_query(F.data == "ad:card:menu")
async def card_menu(call: CallbackQuery):
    """ورود به مدیریت از callback (مثلاً اگه از اینلاین اومد)."""
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    counts = db.card_counts()
    if not counts:
        await call.message.edit_text(
            "🃏 <b>مدیریت فلش‌کارت‌ها</b>\n\n🏜 هنوز کارتی ساخته نشده.",
            reply_markup=K.card_manage_menu_kb(),
        )
        await call.answer()
        return
    items = []
    for r in counts[:30]:
        lesson = LESSONS[r["grade"]][r["lesson"] - 1]["en"] if r["lesson"] <= len(LESSONS[r["grade"]]) else f"درس {r['lesson']}"
        items.append(
            f"{GRADE_ICON[r['grade']]} {r['grade']} | 📖 {lesson} | {CATEGORY_ICON.get(r['category'], '🗂')} {r['category']}: <b>{r['c']}</b>"
        )
    text = "🃏 <b>مدیریت فلش‌کارت‌ها</b>\n\n" + "\n".join(items) + "\n\n👇 یه پایه انتخاب کن:"
    b = InlineKeyboardBuilder()
    for g in GRADES:
        b.button(text=f"{GRADE_ICON[g]} {g}", callback_data=f"adm:card:g:{g}")
    b.button(text="🔙 بازگشت", callback_data="ad:back")
    b.adjust(3, 1)
    await call.message.edit_text(text, reply_markup=b.as_markup())
    await call.answer()


# 🆕 callback_dataهای مدیریت کارت با prefix adm: (برای تشخیص از adc:)
@router.callback_query(F.data.startswith("adm:card:g:"))
async def adm_card_grade(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    grade = call.data.split(":")[-1]
    db = get_db()
    counts = db.card_counts(grade=grade)
    if not counts:
        await call.answer(f"🏜 کارتی در {grade} نیست.", show_alert=True)
        return
    lessons = {}
    for r in counts:
        lessons.setdefault(r["lesson"], []).append(r)
    b = InlineKeyboardBuilder()
    for ln in sorted(lessons.keys()):
        l = LESSONS[grade][ln - 1] if ln <= len(LESSONS[grade]) else None
        title = f"{l['en']}" if l else f"درس {ln}"
        total = sum(r["c"] for r in lessons[ln])
        b.button(text=f"📖 درس {ln}: {title} ({total} کارت)", callback_data=f"adm:card:l:{grade}:{ln}")
    b.button(text="🔙 بازگشت", callback_data="adm:card:b:root")
    b.adjust(1)
    await call.message.edit_text(
        f"🃏 <b>مدیریت — {grade}</b>\n\nیه درس انتخاب کن:",
        reply_markup=b.as_markup(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:card:l:"))
async def adm_card_lesson(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    parts = call.data.split(":")
    grade = parts[-2]
    lesson = int(parts[-1])
    db = get_db()
    counts = db.card_counts(grade=grade)
    cats = [r["category"] for r in counts if r["lesson"] == lesson]
    if not cats:
        await call.answer("کارتی در این درس نیست.", show_alert=True)
        return
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"{CATEGORY_ICON.get(c, '🗂')} {c}", callback_data=f"adm:card:c:{grade}:{lesson}:{c}")
    b.button(text="🔙 بازگشت", callback_data=f"adm:card:b:lessons:{grade}")
    b.adjust(1)
    await call.message.edit_text(
        f"🃏 <b>{grade} | درس {lesson}</b>\n\nکدوم دسته؟",
        reply_markup=b.as_markup(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:card:c:"))
async def adm_card_category(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    parts = call.data.split(":")
    grade = parts[-3]
    lesson = int(parts[-2])
    category = parts[-1]
    db = get_db()
    cards = db.get_deck(grade, lesson, category)
    if not cards:
        await call.answer("کارتی نیست.", show_alert=True)
        return
    items = []
    for c in cards[:15]:
        items.append(f"<code>{c['id']}</code> | <b>{c['front'][:30]}</b> → {c['back'][:30]}")
    text = (
        f"🃏 <b>{grade} | درس {lesson} | {category}</b> ({len(cards)} کارت)\n\n"
        + "\n".join(items)
        + "\n\n💡 روی هر کارت بزن:"
    )
    b = InlineKeyboardBuilder()
    for c in cards[:15]:
        b.button(text=f"✏️ {c['front'][:20]}", callback_data=f"adm:card:e:{c['id']}")
    b.button(text="🔙 بازگشت", callback_data=f"adm:card:b:cats:{grade}:{lesson}")
    b.adjust(1)
    await call.message.edit_text(text, reply_markup=b.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("adm:card:e:"))
async def adm_card_edit_view(call: CallbackQuery):
    """نمایش کارت + دکمه‌های ویرایش/حذف."""
    if not _is_admin(call.from_user.id):
        return await call.answer()
    card_id = int(call.data.split(":")[-1])
    db = get_db()
    card = db.con.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
    if not card:
        await call.answer("کارت پیدا نشد.", show_alert=True)
        return
    text = (
        f"🃏 <b>کارت #{card['id']}</b>\n\n"
        f"📌 {card['grade']} | درس {card['lesson']} | {card['category']}\n\n"
        f"🗝 <b>جلو:</b> {card['front']}\n"
        f"✅ <b>پشت:</b> {card['back']}\n"
        f"📝 <b>مثال:</b> {card['example'] or '—'}\n"
        f"💡 <b>نکته:</b> {card['tip'] or '—'}"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🗑 حذف", callback_data=f"adm:card:d:{card['id']}")
    b.button(text="🔙 بازگشت به لیست", callback_data=f"adm:card:b:list:{card['grade']}:{card['lesson']}:{card['category']}")
    b.adjust(1)
    await call.message.edit_text(text, reply_markup=b.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("adm:card:d:"))
async def adm_card_delete(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    card_id = int(call.data.split(":")[-1])
    db = get_db()
    _card = db.con.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
    db.delete_card(card_id)
    _kb = None
    if _card:
        _b = InlineKeyboardBuilder()
        _b.button(text="🔙 بازگشت به لیست", callback_data=f"adm:card:b:list:{_card['grade']}:{_card['lesson']}:{_card['category']}")
        _kb = _b.as_markup()
    await call.message.edit_text(f"🗑 کارت #{card_id} حذف شد.", reply_markup=_kb)
    await call.answer("✅ حذف شد")


# ── 🔙 برگشت‌های مدیریت فلش‌کارت ─────────────────

async def _adm_render_lessons(message, grade: str) -> None:
    db = get_db()
    counts = db.card_counts(grade=grade)
    if not counts:
        await message.edit_text("🏜 کارتی در این بخش نیست.")
        return
    lessons = {}
    for r in counts:
        lessons.setdefault(r["lesson"], []).append(r)
    b = InlineKeyboardBuilder()
    for ln in sorted(lessons.keys()):
        l = LESSONS[grade][ln - 1] if ln <= len(LESSONS[grade]) else None
        title = f"{l['en']}" if l else f"درس {ln}"
        total = sum(r["c"] for r in lessons[ln])
        b.button(text=f"📖 درس {ln}: {title} ({total} کارت)", callback_data=f"adm:card:l:{grade}:{ln}")
    b.button(text="🔙 بازگشت", callback_data="adm:card:b:root")
    b.adjust(1)
    await message.edit_text(f"🃏 <b>مدیریت — {grade}</b>\n\nیه درس انتخاب کن:", reply_markup=b.as_markup())


async def _adm_render_cats(message, grade: str, lesson: int) -> None:
    db = get_db()
    counts = db.card_counts(grade=grade)
    cats = [r["category"] for r in counts if r["lesson"] == lesson]
    if not cats:
        await message.edit_text("🏜 کارتی در این درس نیست.")
        return
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"{CATEGORY_ICON.get(c, '🗂')} {c}", callback_data=f"adm:card:c:{grade}:{lesson}:{c}")
    b.button(text="🔙 بازگشت", callback_data=f"adm:card:b:lessons:{grade}")
    b.adjust(1)
    await message.edit_text(f"🃏 <b>{grade} | درس {lesson}</b>\n\nکدوم دسته؟", reply_markup=b.as_markup())


async def _adm_render_list(message, grade: str, lesson: int, category: str) -> None:
    db = get_db()
    cards = db.get_deck(grade, lesson, category)
    if not cards:
        await message.edit_text("🏜 کارتی در این بخش نیست.")
        return
    items = [f"<code>{c['id']}</code> | <b>{c['front'][:30]}</b> → {c['back'][:30]}" for c in cards[:15]]
    text = (f"🃏 <b>{grade} | درس {lesson} | {category}</b> ({len(cards)} کارت)\n\n"
            + "\n".join(items) + "\n\n💡 روی هر کارت بزن:")
    b = InlineKeyboardBuilder()
    for c in cards[:15]:
        b.button(text=f"✏️ {c['front'][:20]}", callback_data=f"adm:card:e:{c['id']}")
    b.button(text="🔙 بازگشت", callback_data=f"adm:card:b:cats:{grade}:{lesson}")
    b.adjust(1)
    await message.edit_text(text, reply_markup=b.as_markup())


@router.callback_query(F.data == "adm:card:b:root")
async def adm_back_root(call: CallbackQuery):
    """برگشت به لیست پایه‌ها."""
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await card_menu(call)


@router.callback_query(F.data.startswith("adm:card:b:lessons:"))
async def adm_back_lessons(call: CallbackQuery):
    """برگشت به لیست درس‌ها."""
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await _adm_render_lessons(call.message, call.data.split(":")[-1])
    await call.answer()


@router.callback_query(F.data.startswith("adm:card:b:cats:"))
async def adm_back_cats(call: CallbackQuery):
    """برگشت به لیست دسته‌ها."""
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await _adm_render_cats(call.message, call.data.split(":")[-2], int(call.data.split(":")[-1]))
    await call.answer()


@router.callback_query(F.data.startswith("adm:card:b:list:"))
async def adm_back_list(call: CallbackQuery):
    """برگشت به لیست کارت‌ها."""
    if not _is_admin(call.from_user.id):
        return await call.answer()
    parts = call.data.split(":")
    await _adm_render_list(call.message, parts[-3], int(parts[-2]), parts[-1])
    await call.answer()


# ── ویزارد افزودن دستی ────────────────────────

@router.callback_query(F.data == "ad:card:add")
async def card_add_start(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminCardWizard.grade)
    await call.message.edit_text(T.ADMIN_ADD_CARD_PICK_GRADE, reply_markup=K.exam_grade_kb("adc"))
    await call.answer()


@router.callback_query(F.data.startswith("adc:g:"), AdminCardWizard.grade)
async def card_add_grade(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    grade = call.data.split(":")[-1]
    await state.update_data(card_grade=grade)
    await state.set_state(AdminCardWizard.lesson)
    await call.message.edit_text(T.ADMIN_ADD_CARD_PICK_LESSON, reply_markup=K.card_lesson_kb(grade, "adc"))
    await call.answer()


@router.callback_query(F.data.startswith("adc:l:"), AdminCardWizard.lesson)
async def card_add_lesson(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    lesson = int(call.data.split(":")[-1])
    await state.update_data(card_lesson=lesson)
    await state.set_state(AdminCardWizard.category)
    await call.message.edit_text(T.ADMIN_ADD_CARD_PICK_CAT, reply_markup=K.card_category_kb("adc"))
    await call.answer()


@router.callback_query(F.data.startswith("adc:c:"), AdminCardWizard.category)
async def card_add_category(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    cat = call.data.split(":")[-1]
    await state.update_data(card_category=cat)
    await state.set_state(AdminCardWizard.front)
    await call.message.edit_text(T.ADMIN_ADD_CARD_FRONT, reply_markup=_wizard_back_kb("adc:back"))
    await call.answer()


@router.callback_query(F.data == "adc:back")
async def card_w_back(call: CallbackQuery, state: FSMContext):
    """بازگشت یک مرحله در ویزارد کارت."""
    cur = await state.get_state()
    await call.answer("↩️ برگشتی")
    if cur == AdminCardWizard.grade:
        await state.clear()
        await call.message.edit_text("↩️ از ویزارد خارج شدی.")
        return
    if cur == AdminCardWizard.lesson:
        await state.set_state(AdminCardWizard.grade)
        await call.message.edit_text(T.ADMIN_ADD_CARD_PICK_GRADE, reply_markup=K.exam_grade_kb("adc"))
        return
    if cur == AdminCardWizard.category:
        data = await state.get_data()
        await state.set_state(AdminCardWizard.lesson)
        await call.message.edit_text(T.ADMIN_ADD_CARD_PICK_LESSON, reply_markup=K.card_lesson_kb(data.get("card_grade", "دهم"), "adc"))
        return
    if cur in (AdminCardWizard.front, AdminCardWizard.back, AdminCardWizard.example, AdminCardWizard.tip):
        await state.set_state(AdminCardWizard.category)
        await call.message.edit_text(T.ADMIN_ADD_CARD_PICK_CAT, reply_markup=K.card_category_kb("adc"))
        return
    await state.clear()


@router.message(AdminCardWizard.front)
async def card_add_front(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(card_front=message.text.strip())
    await state.set_state(AdminCardWizard.back)
    await message.answer(T.ADMIN_ADD_CARD_BACK, reply_markup=_wizard_back_kb("adc:back"))


@router.message(AdminCardWizard.back)
async def card_add_back(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(card_back=message.text.strip())
    await state.set_state(AdminCardWizard.example)
    await message.answer(T.ADMIN_ADD_CARD_EX, reply_markup=_wizard_back_kb("adc:back"))


@router.message(AdminCardWizard.example)
async def card_add_example(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.update_data(card_example=message.text.strip())
    await state.set_state(AdminCardWizard.tip)
    await message.answer(T.ADMIN_ADD_CARD_TIP, reply_markup=K.skip_kb("adc:tip"))


@router.callback_query(F.data == "adc:tip:skip", AdminCardWizard.tip)
async def card_add_tip_skip(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    data = await state.get_data()
    db.add_card(
        data["card_grade"], data["card_lesson"], data["card_category"],
        data["card_front"], data["card_back"], data["card_example"], "",
    )
    await state.clear()
    await call.message.answer(T.ADMIN_CARD_SAVED, reply_markup=K.card_saved_next_kb())
    await call.answer()


@router.message(AdminCardWizard.tip)
async def card_add_tip(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    data = await state.get_data()
    db.add_card(
        data["card_grade"], data["card_lesson"], data["card_category"],
        data["card_front"], data["card_back"], data["card_example"], message.text.strip(),
    )
    await state.clear()
    await message.answer(T.ADMIN_CARD_SAVED, reply_markup=K.card_saved_next_kb())


# ═══════════════ کاربران ═══════════════

@router.callback_query(F.data == "ad:users")
async def users_menu(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    counts = db.user_counts()
    admins = db.admin_ids()
    await state.set_state(AdminSearch.user)
    await state.update_data(users_search_role=None)
    await call.message.edit_text(
        T.ADMIN_USERS_MENU.format(
            total=counts["total"], today=counts["today"],
            week=counts["week"], blocked=counts["blocked"],
            admins=len(admins),
        ),
        reply_markup=K.users_menu_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "ad:users:back")
async def users_back(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.answer("↩️ برگشتی")


@router.callback_query(F.data == "ad:users:filter:admins", AdminSearch.user)
async def users_filter_admins(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    admins = db.con.execute(
        "SELECT * FROM users WHERE role IN ('owner','admin') ORDER BY role, id"
    ).fetchall()
    if not admins:
        text = "🛡 <b>تیم مدیریت</b>\n\nفعلاً هیچ ادمینی ثبت نشده."
    else:
        lines = []
        for a in admins:
            role_emoji = "👑" if a["role"] == "owner" else "🛡"
            username = f"@{a['username']}" if a["username"] else "—"
            lines.append(
                f"{role_emoji} <b>{a['name'] or '—'}</b>\n"
                f"    🆔 <code>{a['id']}</code> | {username}\n"
                f"    {a['grade'] or '—'} | {a['major'] or '—'}"
            )
        text = "🛡 <b>تیم مدیریت</b>\n\n" + "\n\n".join(lines)
    b = InlineKeyboardBuilder()
    b.button(text="↩️ بازگشت", callback_data="ad:users")
    b.adjust(1)
    await call.message.edit_text(text, reply_markup=b.as_markup())
    await call.answer()


@router.callback_query(F.data == "ad:users:filter:all", AdminSearch.user)
async def users_filter_all(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await users_menu(call, state)
    await call.answer()


@router.callback_query(F.data == "ad:admins")
async def admins_list(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    admins = db.con.execute(
        "SELECT * FROM users WHERE role IN ('owner','admin') ORDER BY role, id"
    ).fetchall()
    if not admins:
        text = "🛡 <b>تیم مدیریت</b>\n\nفعلاً هیچ ادمینی ثبت نشده."
    else:
        lines = []
        for a in admins:
            role_emoji = "👑" if a["role"] == "owner" else "🛡"
            username = f"@{a['username']}" if a["username"] else "—"
            lines.append(
                f"{role_emoji} <b>{a['name'] or '—'}</b>\n"
                f"    🆔 <code>{a['id']}</code> | {username}\n"
                f"    {a['grade'] or '—'} | {a['major'] or '—'}"
            )
        text = "🛡 <b>تیم مدیریت</b>\n\n" + "\n\n".join(lines)
    text += "\n\n💡 برای تغییر نقش، از «👥 مدیریت کاربران» کاربر رو سرچ کن و نقشش رو عوض کن."
    b = InlineKeyboardBuilder()
    b.button(text="↩️ بازگشت", callback_data="ad:back")
    b.adjust(1)
    await call.message.edit_text(text, reply_markup=b.as_markup())
    await call.answer()


async def _user_card_text(db, uid: int) -> str:
    u = db.get_user(uid)
    if not u:
        return T.USER_NOT_FOUND
    role_label = {"owner": "👑 صاحب ربات", "admin": "🛡 ادمین", "student": "🧑‍🎓 دانش‌آموز"}[u["role"]]
    return T.USER_CARD.format(
        name=u["name"] or "—", uid=u["id"], username=u["username"] or "—",
        grade=u["grade"] or "—", grade_icon=GRADE_ICON.get(u["grade"], "📚"),
        major=u["major"] or "—", role=role_label,
        blocked="🔴 مسدود" if u["is_blocked"] else "🟢 فعال",
        cards=db.user_cards_viewed(uid),
        exams=len([a for a in db.user_attempts(uid) if a["finished_at"]]),
        points=db.user_points(uid),
        joined=u["created_at"][:10], active=u["last_active"][:16],
    )


@router.message(AdminSearch.user)
async def users_search(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    db = get_db()
    term = (message.text or "").strip()
    if not term:
        return
    data = await state.get_data()
    role_filter = data.get("users_search_role")
    rows = db.search_users(term, role_filter=role_filter)
    if not rows:
        b = InlineKeyboardBuilder()
        b.button(text=T.BTN_BACK, callback_data="ad:users")
        b.adjust(1)
        await message.answer(
            T.USER_NOT_FOUND + " دوباره بفرست 👇",
            reply_markup=b.as_markup(),
        )
        return
    if len(rows) == 1:
        u = rows[0]
        viewer = db.get_user(message.from_user.id)
        await message.answer(
            await _user_card_text(db, u["id"]),
            reply_markup=K.user_admin_kb(
                u["id"], bool(u["is_blocked"]), u["role"],
                viewer_is_owner=viewer["role"] == "owner",
            ),
        )
        await state.clear()
        return
    b = InlineKeyboardBuilder()
    for u in rows:
        b.button(text=f"👤 {u['name'] or '—'} ({u['id']})", callback_data=f"ad:u:view:{u['id']}")
    b.button(text=T.BTN_BACK, callback_data="ad:users")
    b.adjust(1)
    await message.answer(f"🔍 <b>{len(rows)} نفر پیدا شد:</b>", reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("ad:u:view:"))
async def user_view(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    uid = int(call.data.split(":")[-1])
    db = get_db()
    u = db.get_user(uid)
    if not u:
        await call.answer(T.USER_NOT_FOUND, show_alert=True)
        return
    await state.clear()
    viewer = db.get_user(call.from_user.id)
    await call.message.edit_text(
        await _user_card_text(db, uid),
        reply_markup=K.user_admin_kb(
            uid, bool(u["is_blocked"]), u["role"],
            viewer_is_owner=viewer["role"] == "owner",
        ),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ad:u:block:"))
async def user_toggle_block(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    uid = int(call.data.split(":")[-1])
    db = get_db()
    u = db.get_user(uid)
    if u["role"] in ("owner", "admin"):
        await call.answer("🛡 نمی‌تونی ادمین رو مسدود کنی!", show_alert=True)
        return
    db.set_user_field(uid, "is_blocked", 0 if u["is_blocked"] else 1)
    await call.answer("🚦 وضعیت عوض شد")
    u = db.get_user(uid)
    viewer = db.get_user(call.from_user.id)
    await call.message.edit_text(
        await _user_card_text(db, uid),
        reply_markup=K.user_admin_kb(
            uid, bool(u["is_blocked"]), u["role"],
            viewer_is_owner=viewer["role"] == "owner",
        ),
    )


@router.callback_query(F.data.startswith("ad:u:role:"))
async def user_toggle_admin(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    uid = int(call.data.split(":")[-1])
    db = get_db()
    u = db.get_user(uid)
    new_role = "student" if u["role"] == "admin" else "admin"
    db.set_user_field(uid, "role", new_role)
    await call.answer("🛡 نقش عوض شد" if new_role == "admin" else "➖ ادمینی لغو شد")
    u = db.get_user(uid)
    viewer = db.get_user(call.from_user.id)
    await call.message.edit_text(
        await _user_card_text(db, uid),
        reply_markup=K.user_admin_kb(
            uid, bool(u["is_blocked"]), u["role"],
            viewer_is_owner=viewer["role"] == "owner",
        ),
    )


@router.callback_query(F.data.startswith("ad:u:refresh:"))
async def user_refresh(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    uid = int(call.data.split(":")[-1])
    db = get_db()
    u = db.get_user(uid)
    viewer = db.get_user(call.from_user.id)
    await call.message.edit_text(
        await _user_card_text(db, uid),
        reply_markup=K.user_admin_kb(
            uid, bool(u["is_blocked"]), u["role"],
            viewer_is_owner=viewer["role"] == "owner",
        ),
    )
    await call.answer("🔄 به‌روز شد")


# ═══════════════ پیام همگانی ═══════════════

@router.callback_query(F.data == "ad:bc")
async def bc_start(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await state.set_state(Broadcast.text)
    await state.update_data(bc_grades=[], bc_majors=[])
    await call.message.edit_text(T.BC_ASK)
    await call.answer()


@router.message(Broadcast.text)
async def bc_text(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    text = (message.html_text or "").strip()
    if not text:
        await message.answer("⚠️ پیام خالیه! متنش رو بنویس:")
        return
    db = get_db()
    await state.update_data(bc_text=text)
    await state.set_state(Broadcast.confirm)
    counts = db.user_counts()
    await message.answer(
        T.BC_FILTER_PROMPT.format(total=counts["total"]),
        reply_markup=K.bc_filter_kb([], []),
    )


@router.callback_query(F.data.startswith("ad:bc:g:"), Broadcast.confirm)
async def bc_toggle_grade(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    grade = call.data.split(":")[-1]
    data = await state.get_data()
    grades: list = list(data.get("bc_grades", []))
    grades = [g for g in grades if g != grade] if grade in grades else grades + [grade]
    await state.update_data(bc_grades=grades)
    majors: list = list(data.get("bc_majors", []))
    await call.message.edit_reply_markup(reply_markup=K.bc_filter_kb(grades, majors))
    await call.answer(f"📌 پایه‌ها: {', '.join(grades) if grades else 'همه'}")


@router.callback_query(F.data.startswith("ad:bc:m:"), Broadcast.confirm)
async def bc_toggle_major(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    major = call.data.split(":")[-1]
    data = await state.get_data()
    majors: list = list(data.get("bc_majors", []))
    majors = [m for m in majors if m != major] if major in majors else majors + [major]
    await state.update_data(bc_majors=majors)
    grades: list = list(data.get("bc_grades", []))
    await call.message.edit_reply_markup(reply_markup=K.bc_filter_kb(grades, majors))
    await call.answer(f"📌 رشته‌ها: {', '.join(majors) if majors else 'همه'}")


@router.callback_query(F.data == "ad:bc:next", Broadcast.confirm)
async def bc_to_confirm(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    data = await state.get_data()
    text = data.get("bc_text", "")
    grades = data.get("bc_grades", [])
    majors = data.get("bc_majors", [])
    db = get_db()
    targets = db.filtered_users(grades=grades, majors=majors, only_active=True)
    if not targets:
        await call.answer("❌ با این فیلتر هیچ کاربر فعالی پیدا نشد!", show_alert=True)
        return
    target_desc = _bc_target_desc(grades, majors)
    await call.message.edit_text(
        T.BC_PREVIEW.format(text=text, count=len(targets)) + f"\n🎯 <b>هدف:</b> {target_desc}",
        reply_markup=K.bc_confirm_kb(),
    )
    await call.answer()


def _bc_target_desc(grades: list, majors: list) -> str:
    parts = []
    if grades:
        parts.append("پایه: " + " | ".join(grades))
    else:
        parts.append("پایه: همه")
    if majors:
        parts.append("رشته: " + " | ".join(majors))
    else:
        parts.append("رشته: همه")
    return "  •  ".join(parts)


@router.callback_query(F.data == "ad:bc:send", Broadcast.confirm)
async def bc_send(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    db = get_db()
    data = await state.get_data()
    text = data.get("bc_text", "")
    grades = data.get("bc_grades", [])
    majors = data.get("bc_majors", [])
    users = db.filtered_users(grades=grades, majors=majors, only_active=True)
    msg = await call.message.edit_text(T.BC_RUNNING.format(sent=0, failed=0))
    sent, failed = 0, 0
    for i, u in enumerate(users, start=1):
        try:
            await call.bot.send_message(u["id"], text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
        if i % 25 == 0:
            try:
                await msg.edit_text(T.BC_RUNNING.format(sent=sent, failed=failed))
            except Exception:
                pass
    db.log_broadcast(text, sent, failed, call.from_user.id)
    target_desc = _bc_target_desc(grades, majors)
    await state.set_state(Broadcast.text)
    await state.update_data(bc_text="", bc_grades=[], bc_majors=[])
    await msg.edit_text(
        T.BC_DONE.format(sent=sent, failed=failed)
        + f"\n\n🎯 <b>ارسال به:</b> {target_desc}\n\n"
        "💡 پیام بعدی؟ بنویس 👇\n"
        "یا از کیبورد پایین استفاده کن:",
        reply_markup=K.bc_after_send_kb(),
    )
    await call.answer("📢 ارسال شد!")


@router.callback_query(F.data == "ad:bc:again")
async def bc_again(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(Broadcast.text)
    await state.update_data(bc_text="", bc_grades=[], bc_majors=[])
    await call.message.edit_text(T.BC_ASK)
    await call.answer()


@router.callback_query(F.data == "ad:bc:back_panel")
async def bc_back_panel(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.message.edit_text("↩️ از پیام همگانی خارج شدی.")
    await call.answer()


@router.callback_query(F.data == "ad:bc:cancel")
async def bc_cancel(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.message.edit_text("↩️ از پیام همگانی خارج شدی.")
    await call.answer()


# ═══════════════ ویرایش متن‌ها ═══════════════

CONTENT_KEYS = {"about": "ℹ️ درباره ما", "contact": "📬 تماس با ما", "guide": "📖 راهنما"}


@router.callback_query(F.data == "ad:content")
async def content_menu(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await call.message.edit_text(T.EDIT_CONTENT_MENU, reply_markup=K.content_edit_kb())
    await call.answer()


@router.callback_query(F.data.startswith("ad:ct:"))
async def content_pick(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    key = call.data.split(":")[-1]
    if key not in CONTENT_KEYS:
        await call.answer()
        return
    db = get_db()
    current = db.get_content(key) or {
        "about": T.ABOUT_CONTACT_DEFAULT, "contact": T.CONTACT_DEFAULT, "guide": T.HELP_TEXT,
    }[key]
    await state.update_data(ct_key=key)
    await state.set_state(EditContent.value)
    await call.message.edit_text(
        f"✏️ <b>ویرایش «{CONTENT_KEYS[key]}»</b>\n\n📄 متن فعلی:\n━━━━━━━━━━━━━━━\n{current[:800]}\n━━━━━━━━━━━━━━━\n\n" +
        T.EDIT_CONTENT_ASK.format(label=CONTENT_KEYS[key]),
    )
    await call.answer()


@router.message(EditContent.value)
async def content_save(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data["ct_key"]
    get_db().set_content(key, message.html_text or "")
    await state.clear()
    await message.answer(
        f"✅ متن «{CONTENT_KEYS[key]}» به‌روز شد! 🎉",
        reply_markup=K.content_edit_kb(),
    )


# ═══════════════ بازگشت ساده ═══════════════

@router.callback_query(F.data == "ad:back")
async def admin_back(call: CallbackQuery, state: FSMContext):
    """ساده: فقط state پاک می‌شه. کاربر از کیبورد reply استفاده کنه."""
    await state.clear()
    await call.answer("↩️ از کیبورد پایین استفاده کن", show_alert=False)


@router.callback_query(F.data == "ad:menu")
async def admin_menu_cb(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.message.answer(
        T.MAIN_MENU_HINT,
        reply_markup=K.main_menu(is_admin(call.from_user.id), in_admin_panel=False),
    )
    await call.answer()


# ═══════════════ لغو ویزارد ═══════════════

@router.callback_query(F.data.in_({"adx:cancel", "adc:cancel"}))
async def wizard_cancel(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.message.edit_text("↩️ لغو شد — از کیبورد پایین استفاده کن.")
    await call.answer()


# ═══════════════ Guard: پیام/دکمه‌های بی‌صاحب ادمین ═══════════════
# ⚠️ این دو handler حتماً باید آخر فایل بمانند (بعد از همهٔ handlerهای
# اختصاصی بالا). چون بدون فیلترن، اگه بالای فایل باشن هر پیام/دکمه‌ای
# رو قبل از رسیدن به handler واقعیش می‌قاپن و بی‌جواب می‌ذارن.

@router.message()
async def admin_guard_message(message: Message, state: FSMContext):
    """فقط برای پیام‌های واقعاً بی‌صاحب (که هیچ handler دیگه‌ای جواب نداده)."""
    pass


@router.callback_query()
async def admin_guard_callback(call: CallbackQuery, state: FSMContext):
    """برای callbackهای unhandled: پیام راهنما بده."""
    await call.answer("⚠️ این دکمه قدیمیه. از کیبورد پایین استفاده کن.", show_alert=False)
