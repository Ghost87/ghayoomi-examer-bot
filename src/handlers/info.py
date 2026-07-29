"""📖 راهنما و ℹ️ درباره ما / تماس با ما."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ..context import get_db
from .. import keyboards as K, texts as T

router = Router()


@router.message(F.text == K.BTN_HELP)
async def help_section(message: Message):
    """🆕 راهنما — دیگر ادمین را از پنل بیرون نمی‌اندازد."""
    db = get_db()
    guide = db.get_content("guide") or T.HELP_TEXT
    u = db.get_user(message.from_user.id)
    is_adm = bool(u) and u["role"] in ("owner", "admin")
    in_panel = is_adm and bool(u["in_panel"])   # 🆕 داخل پنل بود؟ کیبورد پنل برگرده
    await message.answer(guide, reply_markup=K.main_menu(is_admin=is_adm, in_admin_panel=in_panel))


@router.message(F.text == K.BTN_ABOUT)
async def about_section(message: Message):
    """🆕 یک پیام واحد: درباره ما + تماس با ما + سفارش ربات ARIAMIR همه با هم."""
    db = get_db()
    text = db.get_content("about") or db.get_content("contact") or T.ABOUT_CONTACT_DEFAULT
    await message.answer(text, reply_markup=K.about_kb(), disable_web_page_preview=True)


@router.callback_query(F.data == "lb:menu")
@router.callback_query(F.data == "fl:menu")
@router.callback_query(F.data == "ex:menu")
@router.callback_query(F.data == "ad:menu")
async def back_home_cb(call: CallbackQuery):
    from ..handlers.start import is_admin
    get_db().set_user_field(call.from_user.id, "in_panel", 0)
    await call.message.answer(T.MAIN_MENU_HINT,
                              reply_markup=K.main_menu(is_admin(call.from_user.id)))
    await call.answer()
