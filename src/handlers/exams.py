"""🧪 زمین آزمون — شرکت، تایمر، تحویل و نمایش نتایج منتشرشده."""
from __future__ import annotations

import json
import random

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..context import get_db
from .. import keyboards as K, texts as T
from ..utils import (
    BOOK_NAMES, GRADE_ICON, POINTS_PER_PERCENT,
    dt_diff_seconds, fmt_duration, fmt_time_limit,
)

router = Router()


def _exam_status(db, uid: int, exam_id: int) -> str:
    att = db.get_attempt(uid, exam_id)
    exam = db.get_exam(exam_id)
    if not att:
        return "not_started"
    if not att["finished_at"]:
        return "in_progress"
    return "published" if exam["results_published"] else "pending"


def _exam_list_items(db, exams) -> list[tuple[int, str]]:
    return [(e["id"], e["title"]) for e in exams]


# ── ورود از منو ────────────────────────────────

@router.message(F.text == K.BTN_EXAM)
async def exam_menu(message: Message, state: FSMContext):
    db = get_db()
    uid = message.from_user.id
    db.touch(uid)
    await state.clear()
    user = db.get_user(uid)
    if not user or not user["grade"]:
        await message.answer("🙂 اول ثبت‌نامت رو کامل کن — /start")
        return
    exams = db.list_exams(grade=user["grade"], active=True)
    if not exams:
        await message.answer(T.EXAM_NONE)
        return

    items = []
    for e in exams:
        st = _exam_status(db, uid, e["id"])
        icon = {"not_started": "🟢", "in_progress": "🟡", "pending": "⏳", "published": "🏁"}[st]
        count = db.exam_question_count(e["id"])
        lessons = e["lessons"] if e["lessons"] == "همه" else "درس‌های " + e["lessons"]
        items.append(T.EXAM_ITEM.format(
            icon=icon, title=e["title"], count=count,
            time=fmt_time_limit(e["time_limit"]), lessons=lessons,
        ))
    await message.answer(
        T.EXAM_MENU.format(grade=user["grade"], exams_list="\n\n".join(items)),
        reply_markup=K.exams_list_kb(_exam_list_items(db, exams)),
    )


# ── بازگشت به لیست ─────────────────────────────

@router.callback_query(F.data == "ex:list")
async def exam_list_cb(call: CallbackQuery):
    db = get_db()
    user = db.get_user(call.from_user.id)
    exams = db.list_exams(grade=user["grade"], active=True)
    items = []
    for e in exams:
        st = _exam_status(db, call.from_user.id, e["id"])
        icon = {"not_started": "🟢", "in_progress": "🟡", "pending": "⏳", "published": "🏁"}[st]
        count = db.exam_question_count(e["id"])
        lessons = e["lessons"] if e["lessons"] == "همه" else "درس‌های " + e["lessons"]
        items.append(T.EXAM_ITEM.format(
            icon=icon, title=e["title"], count=count,
            time=fmt_time_limit(e["time_limit"]), lessons=lessons,
        ))
    text = T.EXAM_MENU.format(grade=user["grade"], exams_list="\n\n".join(items)) if items else T.EXAM_NONE
    await call.message.edit_text(text, reply_markup=K.exams_list_kb(_exam_list_items(db, exams)) if exams else K.kb_menu_only())
    await call.answer()


# ── باز کردن آزمون ─────────────────────────────

@router.callback_query(F.data.startswith("ex:open:"))
async def exam_open(call: CallbackQuery):
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    exam = db.get_exam(exam_id)
    if not exam or not exam["is_active"]:
        await call.answer("😕 این آزمون دیگه در دسترس نیست.", show_alert=True)
        return
    st = _exam_status(db, call.from_user.id, exam_id)
    count = db.exam_question_count(exam_id)
    lessons = exam["lessons"] if exam["lessons"] == "همه" else "درس‌های " + exam["lessons"]
    status_line = {
        "not_started": "🟢 این آزمون آمادهٔ توئه!",
        "in_progress": "🟡 یه تلاش نیمه‌تموم داری — می‌تونی ادامش بدی",
        "pending": T.EXAM_INFO_PENDING_LINE,
        "published": T.EXAM_INFO_PUBLISHED_LINE,
    }[st]
    await call.message.edit_text(
        T.EXAM_INFO.format(
            title=exam["title"], grade=exam["grade"],
            grade_icon=GRADE_ICON.get(exam["grade"], "📚"),
            lessons=lessons, count=count,
            time=fmt_time_limit(exam["time_limit"]),
            status_line=status_line,
        ),
        reply_markup=K.exam_info_kb(exam_id, st),
    )
    await call.answer()


# ── شروع / شروع دوباره ────────────────────────

@router.callback_query(F.data.startswith("ex:start:"))
async def exam_start(call: CallbackQuery):
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    exam = db.get_exam(exam_id)
    if not exam or not exam["is_active"]:
        await call.answer("😕 این آزمون در دسترس نیست.", show_alert=True)
        return
    old = db.get_attempt(call.from_user.id, exam_id)
    if old and old["finished_at"]:
        await call.answer("✅ تو این آزمون رو یه بار شرکت کردی.", show_alert=True)
        return

    questions = db.exam_questions(exam_id)
    if not questions:
        await call.answer("😬 فعلاً سؤال‌دار نشده — به ادمین خبر بده.", show_alert=True)
        return

    order = [q["id"] for q in questions]
    random.shuffle(order)
    attempt_id = db.start_attempt(call.from_user.id, exam_id, order, len(order))
    await _serve_question(call, attempt_id, 0)
    await call.answer("🎯 موفق باشی قهرمان!")


@router.callback_query(F.data.startswith("ex:resume:"))
async def exam_resume(call: CallbackQuery):
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    att = db.get_attempt(call.from_user.id, exam_id)
    if not att or att["finished_at"]:
        await call.answer("😕 تلاش فعالی پیدا نشد.", show_alert=True)
        return
    order = json.loads(att["order_json"])
    answered = {a["question_id"] for a in db.attempt_answers(att["id"])}
    idx = 0
    for i, qid in enumerate(order):
        if qid not in answered:
            idx = i
            break
    else:
        idx = len(order) - 1
    await _serve_question(call, att["id"], idx)
    await call.answer("▶️ ادامه بده!")


# ── سرو سؤال ───────────────────────────────────

async def _serve_question(call: CallbackQuery, attempt_id: int, idx: int):
    db = get_db()
    att = db.get_attempt_by_id(attempt_id)
    if not att or att["finished_at"]:
        await call.answer(T.QUIZ_WRONG_STATE, show_alert=True)
        return
    order = json.loads(att["order_json"])
    qid = order[idx]
    q = db.con.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    exam = db.get_exam(att["exam_id"])

    elapsed = dt_diff_seconds(att["started_at"])
    if exam["time_limit"] and elapsed >= exam["time_limit"]:
        await _time_over_finish(call, att, exam)
        return

    timer = ""
    if exam["time_limit"]:
        remaining = exam["time_limit"] - elapsed
        timer = f"⏳ {fmt_duration(remaining)}"

    options = [q["opt1"], q["opt2"], q["opt3"], q["opt4"]]
    opt_lines = "\n".join(f"{T.OPT_LINE_LETTERS[i]} {o}" for i, o in enumerate(options))
    ans = db.get_answer(attempt_id, qid)

    await call.message.edit_text(
        T.QUESTION_TEXT.format(
            i=idx + 1, total=len(order), timer=timer,
            text=q["text"], options=opt_lines,
        ),
        reply_markup=K.exam_question_kb(
            attempt_id, len(order), idx, options,
            chosen=ans["chosen"] if ans else None,
        ),
    )


# ── ناوبری بین سؤال‌ها ────────────────────────

@router.callback_query(F.data.startswith("exq:n:"))
async def exam_nav(call: CallbackQuery):
    _, _, attempt_id, idx = call.data.split(":")
    await _serve_question(call, int(attempt_id), int(idx))
    await call.answer()


# ── ثبت پاسخ ──────────────────────────────────

@router.callback_query(F.data.startswith("exq:a:"))
async def exam_answer(call: CallbackQuery):
    _, _, attempt_id, idx, chosen = call.data.split(":")
    attempt_id, idx, chosen = int(attempt_id), int(idx), int(chosen)
    db = get_db()
    att = db.get_attempt_by_id(attempt_id)
    if not att or att["finished_at"] or att["user_id"] != call.from_user.id:
        await call.answer(T.QUIZ_WRONG_STATE, show_alert=True)
        return

    exam = db.get_exam(att["exam_id"])
    elapsed = dt_diff_seconds(att["started_at"])
    if exam["time_limit"] and elapsed >= exam["time_limit"]:
        await _time_over_finish(call, att, exam)
        return

    order = json.loads(att["order_json"])
    qid = order[idx]
    q = db.con.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    db.save_answer(attempt_id, qid, chosen, chosen == q["correct"])
    await call.answer("✍️ ثبت شد")

    if idx + 1 < len(order):
        await _serve_question(call, attempt_id, idx + 1)
    else:
        await _ask_finish(call, attempt_id)


# ── تحویل ──────────────────────────────────────

async def _ask_finish(call: CallbackQuery, attempt_id: int):
    db = get_db()
    att = db.get_attempt_by_id(attempt_id)
    order = json.loads(att["order_json"])
    answered = len(db.attempt_answers(attempt_id))
    unanswered = len(order) - answered
    await call.message.edit_text(
        f"🏁 <b>آخر سؤال بود!</b>\n\n"
        f"✍️ به {answered} سؤال از {len(order)} جواب دادی."
        + (f"\n⚠️ {unanswered} سؤال بی‌جواب مونده!" if unanswered else "\n👌 همهٔ سؤال‌ها جواب داده‌شده — خفن!")
        + "\n\nتحویل بدم؟ 👇",
        reply_markup=K.exam_confirm_finish_kb(attempt_id, unanswered),
    )


@router.callback_query(F.data.startswith("exq:f:"))
async def exam_finish_ask(call: CallbackQuery):
    attempt_id = int(call.data.split(":")[-1])
    db = get_db()
    att = db.get_attempt_by_id(attempt_id)
    if not att or att["finished_at"] or att["user_id"] != call.from_user.id:
        await call.answer(T.QUIZ_WRONG_STATE, show_alert=True)
        return
    exam = db.get_exam(att["exam_id"])
    elapsed = dt_diff_seconds(att["started_at"])
    if exam["time_limit"] and elapsed >= exam["time_limit"]:
        await _time_over_finish(call, att, exam)
        return
    await _ask_finish(call, attempt_id)
    await call.answer()


@router.callback_query(F.data.startswith("exq:cf:"))
async def exam_finish_confirm(call: CallbackQuery):
    attempt_id = int(call.data.split(":")[-1])
    db = get_db()
    att = db.get_attempt_by_id(attempt_id)
    if not att or att["finished_at"] or att["user_id"] != call.from_user.id:
        await call.answer(T.QUIZ_WRONG_STATE, show_alert=True)
        return
    duration = dt_diff_seconds(att["started_at"])
    db.finish_attempt(attempt_id, duration)

    # امتیاز: هر درصد = ۱ امتیاز
    att = db.get_attempt_by_id(attempt_id)
    db.add_points(att["user_id"], int(att["percent"] * POINTS_PER_PERCENT), "exam")

    from ..handlers.start import is_admin
    await call.message.edit_text(T.EXAM_SUBMITTED.format(total=att["total"]))
    await call.message.answer(T.MAIN_MENU_HINT, reply_markup=K.main_menu(is_admin(call.from_user.id)))
    await call.answer("✅ آفرین!")


@router.callback_query(F.data.startswith("exq:back:"))
async def exam_back_edit(call: CallbackQuery):
    attempt_id = int(call.data.split(":")[-1])
    db = get_db()
    att = db.get_attempt_by_id(attempt_id)
    if not att or att["finished_at"]:
        await call.answer(T.QUIZ_WRONG_STATE, show_alert=True)
        return
    order = json.loads(att["order_json"])
    answered = {a["question_id"] for a in db.attempt_answers(attempt_id)}
    idx = 0
    for i, qid in enumerate(order):
        if qid not in answered:
            idx = i
            break
    await _serve_question(call, attempt_id, idx)
    await call.answer()


async def _time_over_finish(call: CallbackQuery, att, exam):
    db = get_db()
    duration = dt_diff_seconds(att["started_at"])
    db.finish_attempt(att["id"], duration)
    att = db.get_attempt_by_id(att["id"])
    answered = len(db.attempt_answers(att["id"]))
    db.add_points(att["user_id"], int(att["percent"] * POINTS_PER_PERCENT), "exam")

    from ..handlers.start import is_admin
    text = T.TIME_OVER.format(title=exam["title"], answered=answered, total=att["total"])
    try:
        await call.message.edit_text(text)
    except Exception:
        await call.message.answer(text)
    await call.message.answer(T.MAIN_MENU_HINT, reply_markup=K.main_menu(is_admin(call.from_user.id)))
    await call.answer("⏰ وقت تموم شد!")


# ── نتیجهٔ من ─────────────────────────────────

@router.callback_query(F.data.startswith("ex:myresult:"))
async def exam_my_result(call: CallbackQuery):
    exam_id = int(call.data.split(":")[-1])
    db = get_db()
    att = db.get_attempt(call.from_user.id, exam_id)
    exam = db.get_exam(exam_id)
    if not att or not att["finished_at"]:
        await call.answer("😕 نتیجه‌ای ثبت نشده.", show_alert=True)
        return
    if not exam["results_published"]:
        await call.answer(T.EXAM_INFO_PENDING_LINE, show_alert=True)
        return
    participants = len(db.exam_attempts(exam_id))
    percent = att["percent"]
    if percent >= 80:
        verdict = T.VERDICT["top"]
    elif percent >= 60:
        verdict = T.VERDICT["good"]
    elif percent >= 40:
        verdict = T.VERDICT["mid"]
    else:
        verdict = T.VERDICT["low"]
    await call.message.edit_text(
        T.RESULTS_PUBLISHED_USER.format(
            title=exam["title"], score=att["score"], total=att["total"],
            percent=percent, taraz=round(att["taraz"], 0), rank=att["rank_pos"],
            participants=participants, duration=fmt_duration(att["duration"]),
            verdict=verdict,
        ),
        reply_markup=K.exam_info_kb(exam_id, "published"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ex:lb:"))
async def exam_lb_from_result(call: CallbackQuery):
    exam_id = int(call.data.split(":")[-1])
    from .leaderboard import show_exam_leaderboard
    await show_exam_leaderboard(call, exam_id)
