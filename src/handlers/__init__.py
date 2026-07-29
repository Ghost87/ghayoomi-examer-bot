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
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(flashcards.router)
    dp.include_router(exams.router)
    dp.include_router(leaderboard.router)
    dp.include_router(profile.router)
    dp.include_router(info.router)
