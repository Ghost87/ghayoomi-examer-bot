#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 ابزار حذف داده‌های کاربران — Ghayoomi Examer
ساخته‌شده توسط ARIAMIR (@ARIAMIR_IR)

سه حالت دارد:
  wipe_users     → حذف همه‌ی کاربران + فعالیت‌هایشان (محتوا دست نمی‌خورد)
  delete_one_user → حذف فقط یک کاربر با آیدی عددی + فعالیت‌هایش
  reset_stats    → صفرکردن آمار (آزمون‌ها/امتیازها/مرورها) ولی حفظ کاربران

جدول‌های محتوایی (cards, exams, questions, content_texts, broadcasts)
در هیچ حالتی پاک نمی‌شوند.

استفاده:
  python scripts/admin_tools.py --action wipe_users
  python scripts/admin_tools.py --action delete_one_user --user-id 8975757230
  python scripts/admin_tools.py --action reset_stats
  (مسیر دیتابیس با --db قابل تغییر است؛ پیش‌فرض: data/ghayoomi.db)
"""
import argparse
import os
import sqlite3
import sys

TRACKED_TABLES = ["users", "attempts", "attempt_answers", "points_log", "card_views"]


def count(cur: sqlite3.Cursor, table: str) -> int:
    try:
        return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.Error:
        return -1  # جدول هنوز ساخته نشده


def snapshot(cur: sqlite3.Cursor, label: str) -> None:
    print(f"\n📊 {label}")
    for t in TRACKED_TABLES:
        c = count(cur, t)
        print(f"   {t:<16} : {'—' if c < 0 else f'{c} ردیف'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="حذف داده‌های کاربران ربات قیمی")
    parser.add_argument("--action", required=True,
                        choices=["wipe_users", "delete_one_user", "reset_stats"])
    parser.add_argument("--user-id", default="", help="آیدی عددی کاربر (فقط برای delete_one_user)")
    parser.add_argument("--db", default=os.environ.get("DB_PATH", "data/ghayoomi.db"))
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"❌ دیتابیس پیدا نشد: {args.db} — چیزی برای پاک‌سازی نیست.")
        return 1

    con = sqlite3.connect(args.db)
    cur = con.cursor()

    print(f"🧹 ابزار مدیریتی قیمی | حالت: {args.action}")
    snapshot(cur, "قبل از پاک‌سازی:")

    if args.action == "wipe_users":
        cur.execute("DELETE FROM attempt_answers")
        cur.execute("DELETE FROM attempts")
        cur.execute("DELETE FROM points_log")
        cur.execute("DELETE FROM card_views")
        cur.execute("DELETE FROM users")
        print("\n🗑️ همه‌ی کاربران و فعالیت‌هایشان حذف شد.")

    elif args.action == "delete_one_user":
        uid_raw = (args.user_id or "").strip()
        if not uid_raw.isdigit():
            print("\n❌ برای delete_one_user باید --user-id عددی بدهی (مثل: 8975757230).")
            return 1
        uid = int(uid_raw)
        row = cur.execute("SELECT name, username FROM users WHERE id = ?", (uid,)).fetchone()
        if not row:
            print(f"\n❌ کاربری با آیدی {uid} پیدا نشد.")
            return 1
        print(f"\n👤 کاربر پیدا شد: {row[0] or '—'} (@{row[1] or '—'})")
        cur.execute("DELETE FROM attempt_answers WHERE attempt_id IN "
                    "(SELECT id FROM attempts WHERE user_id = ?)", (uid,))
        cur.execute("DELETE FROM attempts WHERE user_id = ?", (uid,))
        cur.execute("DELETE FROM points_log WHERE user_id = ?", (uid,))
        cur.execute("DELETE FROM card_views WHERE user_id = ?", (uid,))
        cur.execute("DELETE FROM users WHERE id = ?", (uid,))
        print(f"🗑️ کاربر {uid} و فعالیت‌هایش حذف شد.")

    elif args.action == "reset_stats":
        cur.execute("DELETE FROM attempt_answers")
        cur.execute("DELETE FROM attempts")
        cur.execute("DELETE FROM points_log")
        cur.execute("DELETE FROM card_views")
        print("\n📊 آمار فعالیت‌ها صفر شد (کاربران حفظ شدند).")

    con.commit()
    snapshot(cur, "بعد از پاک‌سازی:")
    cur.execute("VACUUM")
    con.close()
    print("\n✅ پاک‌سازی با موفقیت انجام شد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
