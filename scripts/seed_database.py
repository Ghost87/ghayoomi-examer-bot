#!/usr/bin/env python3
"""🌱 پر کردن دیتابیس با محتوای اولیه (data/seed_content.json).

اجرا:
    python scripts/seed_database.py            # فقط اگر خالی باشد کارت/آزمون می‌گذارد
    python scripts/seed_database.py --force    # سیید تازه اضافه می‌کند (بدون پاک کردن قبلی‌ها)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config import DB_PATH  # noqa: E402
from src.db import DB  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    seed_path = BASE_DIR / "data" / "seed_content.json"
    data = json.loads(seed_path.read_text(encoding="utf-8"))

    db = DB(DB_PATH)

    if db.cards_total() > 0 and not args.force:
        print("ℹ️  دیتابیس از قبل کارت دارد — برای سیید مجدد از --force استفاده کن.")
        db.close()
        return

    n_cards = 0
    for c in data["cards"]:
        db.add_card(c["grade"], c["lesson"], c["category"],
                    c["front"], c["back"], c["example"], c["tip"])
        n_cards += 1

    n_exams = 0
    for e in data["exams"]:
        exam_id = db.create_exam(
            title=e["title"], grade=e["grade"], lessons=e["lessons"],
            time_limit=e["time_limit"], created_by=0,
        )
        for i, q in enumerate(e["questions"], start=1):
            db.add_question(
                exam_id, i, q["text"], q["options"][0], q["options"][1],
                q["options"][2], q["options"][3], q["correct"],
                q.get("explanation", ""),
            )
        n_exams += 1

    db.close()
    print(f"✅ {n_cards} کارت و {n_exams} آزمون نمونه به دیتابیس اضافه شد! 🎉")


if __name__ == "__main__":
    main()
