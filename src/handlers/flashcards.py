"""🃏 زمین فلش‌کارت — دسته‌بندی پایه/درس/موضوع + چرخاندن کارت‌ها."""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..context import get_db
from .. import keyboards as K, texts as T
from ..utils import (
    BOOK_NAMES, CATEGORY_ICON, LESSONS, POINTS_CARD_VIEW,
)

router = Router()


class FlashSession(StatesGroup):
    running = State()


# ── شروع ───────────────────────────────────────

@router.message(F.text == K.BTN_FLASH)
async def flash_entry(message: Message, state: FSMContext):
    get_db().touch(message.from_user.id)
    await state.clear()
    await message.answer(T.FLASH_MENU, reply_markup=K.flash_grade_kb())


# ── انتخاب پایه ────────────────────────────────

@router.callback_query(F.data.startswith("fl:g:"))
async def flash_pick_grade(call: CallbackQuery, state: FSMContext):
    grade = call.data.split(":")[-1]
    await state.update_data(f_grade=grade)
    await call.message.edit_text(
        T.FLASH_PICK_LESSON.format(book=BOOK_NAMES[grade]),
        reply_markup=K.flash_lesson_kb(grade),
    )
    await call.answer()


# ── انتخاب درس ─────────────────────────────────

@router.callback_query(F.data.startswith("fl:l:"))
async def flash_pick_lesson(call: CallbackQuery, state: FSMContext):
    _, _, grade, lesson = call.data.split(":")
    await state.update_data(f_grade=grade, f_lesson=int(lesson))
    await call.message.edit_text(
        T.FLASH_PICK_CATEGORY.format(
            lesson=lesson, title=LESSONS[grade][int(lesson) - 1]["en"],
        ),
        reply_markup=K.flash_category_kb(grade, int(lesson)),
    )
    await call.answer()


# ── حالت ترکیبی (همهٔ درس‌ها) ─────────────────

@router.callback_query(F.data.startswith("fl:all:"))
async def flash_mixed(call: CallbackQuery, state: FSMContext):
    grade = call.data.split(":")[-1]
    await state.update_data(f_grade=grade, f_lesson=None)
    await call.message.edit_text(
        f"🎲 <b>ترکیبی از همهٔ درس‌های {grade}</b>\n\nحالا بگو روی چی تمرکز کنیم؟ 👇",
        reply_markup=K.flash_category_kb(grade, None),
    )
    await call.answer()


# ── بازگشت مرحله‌ای ────────────────────────────

@router.callback_query(F.data == "fl:back:g")
async def flash_back_grade(call: CallbackQuery):
    await call.message.edit_text(T.FLASH_MENU, reply_markup=K.flash_grade_kb())
    await call.answer()


@router.callback_query(F.data.startswith("fl:back:l:"))
async def flash_back_lesson(call: CallbackQuery):
    grade = call.data.split(":")[-1]
    await call.message.edit_text(
        T.FLASH_PICK_LESSON.format(book=BOOK_NAMES[grade]),
        reply_markup=K.flash_lesson_kb(grade),
    )
    await call.answer()


# ── انتخاب دسته و ساخت دک ──────────────────────

@router.callback_query(F.data.startswith("fl:c:"))
async def flash_start_deck(call: CallbackQuery, state: FSMContext):
    _, _, grade, lesson, category = call.data.split(":")
    db = get_db()

    if lesson == "all":
        deck = db.deck_random(grade, category)
    else:
        deck = db.get_deck(grade, int(lesson), category)

    if not deck:
        await call.message.edit_text(
            T.FLASH_EMPTY,
            reply_markup=K.flash_category_kb(grade, None if lesson == "all" else int(lesson)),
        )
        await call.answer()
        return

    deck_ids = [c["id"] for c in deck]
    await state.update_data(
        deck_ids=deck_ids, idx=0, flipped=False,
        f_grade=grade, f_lesson=None if lesson == "all" else int(lesson),
        f_category=category,
        s_viewed=0, s_known=0, s_review=0, s_points=0,
    )
    await state.set_state(FlashSession.running)
    await _render_card(call.message, state, edit=True)
    await call.answer()


# ── رندر کارت ──────────────────────────────────

async def _render_card(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    db = get_db()
    deck_ids: list[int] = data["deck_ids"]
    idx: int = data["idx"]
    flipped: bool = data.get("flipped", False)

    card = db.con.execute("SELECT * FROM cards WHERE id=?", (deck_ids[idx],)).fetchone()
    total = len(deck_ids)
    grade, category = data["f_grade"], data["f_category"]
    lesson = data.get("f_lesson") or card["lesson"]

    f_example = T.CARD_EXAMPLE.format(example=card["example"]) if card["example"] else "_بدون مثال 🙈_"
    b_tip = T.CARD_TIP.format(tip=card["tip"]) if card["tip"] else ""

    text = (T.CARD_BACK if flipped else T.CARD_FRONT).format(
        i=idx + 1, total=total,
        category_icon=CATEGORY_ICON.get(category, "🗂"),
        category=category,
        book=BOOK_NAMES[grade],
        lesson=lesson,
        front=card["front"],
        back=card["back"],
        f_example=f_example,
        b_tip=b_tip,
    )
    kb = K.card_kb(has_prev=idx > 0, has_next=idx < total - 1, is_flipped=flipped)
    if edit:
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb)


# ── چرخاندن کارت ───────────────────────────────

@router.callback_query(F.data == "fl:flip", FlashSession.running)
async def card_flip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    flipped = not data.get("flipped", False)
    await state.update_data(flipped=flipped)

    # ثبت مشاهده فقط دفعهٔ اول در روز
    if flipped:
        db = get_db()
        new_view = db.log_card_view(call.from_user.id, data["deck_ids"][data["idx"]])
        if new_view:
            s_points = data.get("s_points", 0) + POINTS_CARD_VIEW
            db.add_points(call.from_user.id, POINTS_CARD_VIEW, "flashcard")
            await state.update_data(s_points=s_points)
            await call.answer(f"🌟 +{POINTS_CARD_VIEW} امتیاز!", show_alert=False)
        else:
            await call.answer()
    else:
        await call.answer()
    await _render_card(call.message, state, edit=True)


# ── ناوبری ─────────────────────────────────────

@router.callback_query(F.data.startswith("fl:nav:"), FlashSession.running)
async def card_nav(call: CallbackQuery, state: FSMContext):
    direction = call.data.split(":")[-1]
    data = await state.get_data()
    idx = data["idx"] + (1 if direction == "next" else -1)
    idx = max(0, min(idx, len(data["deck_ids"]) - 1))
    await state.update_data(idx=idx, flipped=False, )
    await state.update_data(s_viewed=data.get("s_viewed", 0) + 1)
    await _render_card(call.message, state, edit=True)
    await call.answer()


# ── بلدم / مرور ────────────────────────────────

@router.callback_query(F.data.startswith("fl:mark:"), FlashSession.running)
async def card_mark(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[-1]
    data = await state.get_data()
    key = "s_known" if kind == "known" else "s_review"
    await state.update_data(**{key: data.get(key, 0) + 1})

    total = len(data["deck_ids"])
    if data["idx"] < total - 1:
        await state.update_data(idx=data["idx"] + 1, flipped=False)
        await state.update_data(s_viewed=data.get("s_viewed", 0) + 1)
        await _render_card(call.message, state, edit=True)
        await call.answer("✅ عالی، بریم سراغ بعدی!" if kind == "known" else "🔁 بعداً مرورش می‌کنی 😉")
    else:
        await _end_session(call.message, state, call.from_user.id)
        await call.answer()


# ── پایان جلسه ─────────────────────────────────

async def _end_session(message: Message, state: FSMContext, uid: int):
    data = await state.get_data()
    await state.clear()
    viewed = data.get("s_viewed", 0)
    known = data.get("s_known", 0)
    review = data.get("s_review", 0)
    points = data.get("s_points", 0)

    if viewed + known + review == 0:
        cheer = T.CHEER["low"]
    elif known >= review:
        cheer = T.CHEER["high"] if known >= 5 else T.CHEER["mid"]
    else:
        cheer = T.CHEER["low"]

    from ..handlers.start import is_admin
    await message.answer(
        T.FLASH_SESSION_END.format(viewed=viewed, known=known, review=review,
                                   points=points, cheer=cheer),
        reply_markup=K.main_menu(is_admin(uid)),
    )


@router.callback_query(F.data == "fl:end", FlashSession.running)
async def flash_end(call: CallbackQuery, state: FSMContext):
    await _end_session(call.message, state, call.from_user.id)
    await call.answer()
