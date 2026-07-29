"""🛡 فیلترهای نقش کاربران (ادمین / صاحب)."""
from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from .context import get_db


class IsAdminRole(BaseFilter):
    def __init__(self, owner_only: bool = False):
        self.owner_only = owner_only

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        uid = event.from_user.id
        user = get_db().get_user(uid)
        if not user:
            return False
        if self.owner_only:
            return user["role"] == "owner"
        return user["role"] in ("owner", "admin")


class IsNotBlocked(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = get_db().get_user(event.from_user.id)
        return bool(user) and not user["is_blocked"]
