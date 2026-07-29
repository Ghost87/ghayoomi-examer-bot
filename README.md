# 🎓 Ghayoomi Examer — ربات آموزش زبان انگلیسی

> انگلیسی به سبک استاد قیومی ✨ | فلش‌کارت 🃏 | آزمون 🧪 | لیدربورد 🏆

ربات تلگرامی آموزشی برای دانش‌آموزان پایه‌های **دهم، یازدهم و دوازدهم**
کتاب‌های **Vision 1 / 2 / 3** — متعلق به **کالج آموزش زبان علی قیومی**.

## ✨ قابلیت‌ها

| فیچر | توضیح |
|---|---|
| 📝 Onboarding | ثبت‌نام مرحله‌ای: نام → پایه → رشته |
| 🃏 فلش‌کارت | دسته‌بندی پایه → درس → موضوع (لغات/گرامر/عبارات) با چرخاندن کارت، امتیازدهی روزانه |
| 🧪 آزمون | چهارگزینه‌ای، زمان‌دار/بدون زمان، تحلیل درصد + تراز + رتبه — **با تأیید ادمین منتشر می‌شود** |
| 🏆 لیدربورد | مجزا برای هر آزمون + هفتگی + ماهانه |
| 👤 پروفایل | آمار کامل، ویرایش اطلاعات، یادآور روزانه 🔔 |
| 🛠 پنل ادمین | آزمون‌سازی دستی/ایمپورت، مدیریت فلش‌کارت، انتشار نتایج، مدیریت کاربران، پیام همگانی، ویرایش متن‌ها |
| 📥 ایمپورت | CSV / XLSX / JSON / لینک Google Sheet |

## 🚀 شروع سریع

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # توکن و OWNER_ID را پر کن

python scripts/seed_database.py        # ۸۷ کارت + ۷ آزمون نمونه
python scripts/setup_bot_profile.py    # تنظیم اسم/بیو/دستورات پروفایل ربات
python bot.py                          # روشن شدن ربات 🚀
```

راهنمای کامل: 📖 [docs/SETUP.md](docs/SETUP.md) | 🛠 [docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md)

## 🧪 تست

```bash
python -m unittest discover -s tests -v
```

## 🏗 ساختار پروژه

```
ghayoomi_examer_bot/
├── bot.py                  # 🤖 نقطهٔ ورود
├── src/
│   ├── config.py           # ⚙️ تنظیمات از .env
│   ├── context.py          # 🔗 آبجکت‌های سراسری
│   ├── db.py               # 🗄 SQLite + کامل CRUD
│   ├── texts.py            # ✍️ همهٔ متن‌های فارسی
│   ├── keyboards.py        # ⌨️ کیبوردها
│   ├── states.py           # 🧠 FSM
│   ├── filters.py          # 🛡 نقش‌ها
│   ├── utils.py            # 🧪 ابزارها (تراز، زمان، ثابت‌ها)
│   ├── importer.py         # 📥 CSV/XLSX/JSON/G-Sheet
│   ├── scheduler.py        # 🔔 یادآور روزانه
│   └── handlers/           # 🕹 start / flashcards / exams / leaderboard / profile / info / admin
├── data/seed_content.json  # 🌱 محتوای اولیهٔ واقعی از کتاب‌ها
├── scripts/                # 🛠 seed + تنظیم پروفایل ربات
├── docs/                   # 📖 راهنماها
├── tests/                  # 🧪 تست واحد
└── deploy/                 # 🐳 Docker & systemd
```

## 🔐 امنیت

- توکن فقط داخل `.env` (گیت‌ایگنر شده)
- `OWNER_ID` و `ADMIN_IDS` از env خوانده می‌شوند
- نتایج آزمون تا **تأیید ادمین** منتشر نمی‌شود

---

ساخته‌شده با ❤️ برای [کالج آموزش زبان علی قیومی](https://alighayoomi.com)
👨‍💻 توسعه: **ARIAMIR**
