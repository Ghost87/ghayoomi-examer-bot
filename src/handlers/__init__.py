"""📦 ثبت همهٔ روترها.

🔧 نکتهٔ مهم: فیلتر IsAdminRole() حذف شد چون در بعضی موارد
نقش owner رو از env می‌خوند ولی db نقش admin داشت یا برعکس،
و باعث می‌شد دکمه‌های ادمین کار نکنن.
حالا چک دستی توی خود هندلرها انجام می‌شه (is_admin در start.py).
"""
from aiogram import Dispatcher

from . import admin, exams, flashcards, info, leaderboard, profile, start


def register_all(dp: Dispatcher) -> None:
    # 🆕 بدون فیلتر IsAdminRole — همهٔ هندلرها قابل دسترسی
    # (هر هندلر خودش چک می‌کنه)
    #
    # ⚠️ نکتهٔ حیاتی: admin.router آخرین روتریه که ثبت می‌شه.
    # چون توی admin.py دو تا handler بدون فیلتر (@router.message() و
    # @router.callback_query()) وجود داره که catch-all هستن — یعنی هر
    # پیام/دکمه‌ای که بهشون برسه رو "می‌بلعن" و جلوی رسیدنش به روترهای
    # بعدی رو می‌گیرن. اگه admin.router اول ثبت بشه، حتی /start هم به
    # start.py نمی‌رسه (چون قبلش توسط این catch-all قورت می‌شه).
    # با گذاشتنش در آخر، بقیهٔ روترها اول فرصت جواب دادن رو می‌گیرن و
    # این catch-all فقط برای پیام/دکمه‌های واقعاً بی‌صاحب فعال می‌شه.
    dp.include_router(start.router)
    dp.include_router(flashcards.router)
    dp.include_router(exams.router)
    dp.include_router(leaderboard.router)
    dp.include_router(profile.router)
    dp.include_router(info.router)
    dp.include_router(admin.router)
