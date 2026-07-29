"""🏆 لیدربورد — هفتگی، ماهانه و مجزا برای هر آزمون."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ..context import get_db
from .. import keyboards as K, texts as T
from ..utils import medal

router = Router()


def _render_rows(rows, me_id: int) -> str:
    lines = []
    for i, r in enumerate(rows):
        row = T.LB_ROW_ME.format(
            medal=medal(i), name=r["name"], grade=r["grade"] or "📚", pts=r["pts"],
        ) if r["id"] == me_id else T.LB_ROW.format(
            medal=medal(i), name=r["name"], grade=r["grade"] or "📚", pts=r["pts"],
        )
        lines.append(row)
    return "\n".join(lines)


@router.message(F.text == K.BTN_LB)
async def lb_menu(message: Message):
    get_db().touch(message.from_user.id)
    await message.answer(T.LEADERBOARD_MENU, reply_markup=K.leaderboard_menu_kb())


@router.callback_query(F.data == "lb:back")
async def lb_back(call: CallbackQuery):
    await call.message.edit_text(T.LEADERBOARD_MENU, reply_markup=K.leaderboard_menu_kb())
    await call.answer()


@router.callback_query(F.data == "lb:week")
async def lb_week(call: CallbackQuery):
    db = get_db()
    rows = db.leaderboard(days=7)
    pts = db.user_points(call.from_user.id, days=7)
    pos = db.leaderboard_user_pos(call.from_user.id, days=7)
    me_line = T.LB_ME_LINE.format(pos=pos, pts=pts) if pos else ""
    text = T.LB_WEEKLY.format(rows=_render_rows(rows, call.from_user.id) or T.LB_EMPTY, me_line=me_line)
    await call.message.edit_text(text, reply_markup=K.back_to_lb_menu_kb())
    await call.answer()


@router.callback_query(F.data == "lb:month")
async def lb_month(call: CallbackQuery):
    db = get_db()
    rows = db.leaderboard(days=30)
    pts = db.user_points(call.from_user.id, days=30)
    pos = db.leaderboard_user_pos(call.from_user.id, days=30)
    me_line = T.LB_ME_LINE.format(pos=pos, pts=pts) if pos else ""
    text = T.LB_MONTHLY.format(rows=_render_rows(rows, call.from_user.id) or T.LB_EMPTY, me_line=me_line)
    await call.message.edit_text(text, reply_markup=K.back_to_lb_menu_kb())
    await call.answer()


@router.callback_query(F.data == "lb:exams")
async def lb_exams(call: CallbackQuery):
    db = get_db()
    exams = [e for e in db.list_exams() if e["results_published"]]
    if not exams:
        await call.answer("🏜 هنوز نتیجهٔ هیچ آزمونی منتشر نشده.", show_alert=True)
        return
    lines = [f"🧪 {i}. {e['title']}" for i, e in enumerate(exams, 1)]
    await call.message.edit_text(
        T.LB_PICK_EXAM.format(exams="\n".join(lines)),
        reply_markup=K.leaderboard_exams_kb([(e["id"], e["title"]) for e in exams]),
    )
    await call.answer()


@router.callback_query(F.data.startswith("lb:exam:"))
async def lb_exam(call: CallbackQuery):
    exam_id = int(call.data.split(":")[-1])
    await show_exam_leaderboard(call, exam_id)


async def show_exam_leaderboard(call: CallbackQuery, exam_id: int):
    db = get_db()
    exam = db.get_exam(exam_id)
    if not exam:
        await call.answer("😕 آزمون پیدا نشد.", show_alert=True)
        return
    if not exam["results_published"]:
        await call.answer("🔒 نتایج این آزمون هنوز منتشر نشده.", show_alert=True)
        return
    rows = db.exam_leaderboard(exam_id)
    lines = []
    for i, r in enumerate(rows):
        taraz_line = f"| ⭐ تراز {round(r['taraz'],0)}" if r["taraz"] else ""
        row_class = T.LB_ROW_ME_EXAM if r["user_id"] == call.from_user.id else T.LB_ROW_EXAM
        lines.append(row_class.format(
            medal=medal(i), name=r["name"], grade=r["grade"] or "📚",
            percent=r["percent"], taraz_line=taraz_line,
        ))
    att = db.get_attempt(call.from_user.id, exam_id)
    me_line = T.LB_ME_LINE_EXAM.format(pos=att["rank_pos"]) if (att and att["rank_pos"]) else ""
    text = T.LB_EXAM.format(title=exam["title"], rows="\n".join(lines) or T.LB_EMPTY, me_line=me_line)
    kb = K.leaderboard_exams_kb([(e["id"], e["title"]) for e in db.list_exams() if e["results_published"]])
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()
