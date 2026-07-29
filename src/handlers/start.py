"""🚀 هندلر شروع، Onboarding و برگشت به منو."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..context import get_db
from .. import keyboards as K, texts as T
from ..config import ADMIN_LOGIN, ADMIN_PASSWORD, OWNER_ID, ADMIN_IDS
from ..states import AdminLogin, Onboarding
from ..utils import BOOK_NAMES, GRADE_ICON

router = Router()


def is_admin(uid: int) -> bool:
    db = get_db()
    user = db.get_user(uid)
    return bool(user) and user["role"] in ("owner", "admin")


async def _send_main_menu(message: Message, uid: int, first_name: str):
    db = get_db()
    user = db.get_user(uid)
    points = db.user_points(uid)
    await message.answer(
        T.WELCOME_BACK.format(
            name=user["name"] or first_name,
            grade=user["grade"], major=user["major"], points=points,
        ),
        reply_markup=K.main_menu(is_admin(uid)),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    db = get_db()
    uid = message.from_user.id
    username = message.from_user.username

    # ثبت/به‌روزرسانی کاربر
    db.upsert_user(uid, username)

    # اعطای نقش owner/admin بر اساس env
    user = db.get_user(uid)
    if uid == OWNER_ID and user["role"] != "owner":
        db.set_user_field(uid, "role", "owner")
        user = db.get_user(uid)
    elif uid in ADMIN_IDS and user["role"] == "student":
        db.set_user_field(uid, "role", "admin")
        user = db.get_user(uid)

    if user["is_blocked"]:
        await message.answer(T.BLOCKED_MSG)
        return

    if user["grade"] and user["name"]:
        await state.clear()
        await _send_main_menu(message, uid, message.from_user.first_name)
        return

    # شروع onboarding
    await state.clear()
    await state.set_state(Onboarding.name)
    await message.answer(T.WELCOME.format(name=message.from_user.first_name))


@router.message(Onboarding.name)
async def onboarding_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not (1 < len(name) < 60):
        await message.answer(T.INVALID_NAME)
        return
    await state.update_data(name=name)
    get_db().set_user_field(message.from_user.id, "name", name)
    await state.set_state(Onboarding.grade)
    await message.answer(T.ASK_GRADE.format(name=name), reply_markup=K.grade_kb())


@router.callback_query(F.data.startswith("onb:grade:"), Onboarding.grade)
async def onboarding_grade(call: CallbackQuery, state: FSMContext):
    grade = call.data.split(":")[-1]
    await state.update_data(grade=grade)
    get_db().set_user_field(call.from_user.id, "grade", grade)
    await state.set_state(Onboarding.major)
    await call.message.edit_text(
        T.ASK_MAJOR.format(grade=grade, book=BOOK_NAMES[grade]),
        reply_markup=K.major_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("onb:major:"), Onboarding.major)
async def onboarding_major(call: CallbackQuery, state: FSMContext):
    major = call.data.split(":")[-1]
    db = get_db()
    db.set_user_field(call.from_user.id, "major", major)
    data = await state.get_data()
    await state.clear()
    name = data.get("name", call.from_user.first_name)
    grade = data.get("grade", "")
    await call.message.edit_text(
        T.ONBOARDING_DONE.format(
            name=name, grade=grade,
            grade_icon=GRADE_ICON.get(grade, "📚"),
            major=major, book=BOOK_NAMES.get(grade, ""),
        )
    )
    await call.message.answer(T.MAIN_MENU_HINT, reply_markup=K.main_menu(is_admin(call.from_user.id)))
    await call.answer("🎉 ثبت‌نام کامل شد — خوش اومدی!")


@router.message(F.text.in_({"منو", "🏠 منوی اصلی", "/menu"}))
@router.message(Command("menu"))
async def back_to_menu(message: Message, state: FSMContext):
    db = get_db()
    db.upsert_user(message.from_user.id, message.from_user.username)
    db.touch(message.from_user.id)
    await state.clear()
    user = db.get_user(message.from_user.id)
    if not user or not user["grade"]:
        await cmd_start(message, state)
        return
    await message.answer(T.MAIN_MENU_HINT, reply_markup=K.main_menu(is_admin(message.from_user.id)))


# 🆕 دکمهٔ «پنل مدیریت» در منوی اصلی (فقط برای ادمین‌ها نمایش داده می‌شه)
@router.message(F.text == K.BTN_ADMIN)
async def admin_menu_button(message: Message, state: FSMContext):
    """🆕 کیبورد ادمین فعال می‌شه + پیام منوی اصلی میاد."""
    if not is_admin(message.from_user.id):
        await message.answer("🚧 این دکمه فقط برای ادمین‌هاست.")
        return
    await state.clear()
    # 🆕 منوی اصلی + کیبورد ادمین (هر دو باهم)
    await message.answer(
        T.MAIN_MENU_HINT,
        reply_markup=K.main_menu(is_admin=True, in_admin_panel=True),
    )


@router.callback_query(F.data == "gen:menu")
async def generic_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(T.MAIN_MENU_HINT, reply_markup=K.main_menu(is_admin(call.from_user.id)))
    await call.answer()


# ── ورود مخفی ادمین 🔐 (فقط ادمین جریانش رو می‌دونه) ────────

@router.message(Command("admin"))
async def admin_hidden_login(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminLogin.username)
    await message.answer(T.ADMIN_LOGIN_ASK_USER)


@router.message(AdminLogin.username)
async def admin_login_username(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text != ADMIN_LOGIN:
        await state.clear()
        await message.answer(T.ADMIN_LOGIN_FAIL)
        return
    await state.set_state(AdminLogin.password)
    await message.answer(T.ADMIN_LOGIN_ASK_PASS)


@router.message(AdminLogin.password)
async def admin_login_password(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text != ADMIN_PASSWORD:
        await state.clear()
        await message.answer(T.ADMIN_LOGIN_FAIL)
        return
    # 🆕 ورود موفق: کیبورد ادمین فعال بشه + منوی اصلی هم بیاد
    await state.clear()
    await message.answer(
        T.ADMIN_LOGIN_OK,
        reply_markup=K.main_menu(is_admin=True, in_admin_panel=True),
    )
