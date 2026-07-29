# 🚀 راهنمای کامل اجرای ربات Ghayoomi Examer

این راهنما تو را **قدم‌به‌قدم** از صفر تا روشن‌شدن کامل ربات می‌برد. ☕

---

## ۱️⃣ چیزهایی که لازم داری

| نیاز | از کجا | وضعیت |
|---|---|---|
| 🤖 **توکن ربات** | در تلگرام برو به [@BotFather](https://t.me/BotFather) ← دستور `/newbot` ← اسم و یوزرنیم بده ← توکن می‌دهد بهت | الزامی ✅ |
| 🆔 **آیدی عددی خودت** | به [@userinfobot](https://t.me/userinfobot) پیام بده ← عددت می‌گوید | الزامی ✅ |
| 🐍 پایتون ۳.۱۰+ | [python.org](https://python.org) | برای اجرا روی PC/VPS |

---

## ۲️⃣ نصب

```bash
# ۱. ورود به پوشهٔ پروژه
cd ghayoomi_examer_bot

# ۲. ساخت محیط مجازی (پیشنهادی)
python3 -m venv .venv

# فعال‌سازی — لینوکس/مک:
source .venv/bin/activate
# فعال‌سازی — ویندوز:
# .venv\Scripts\activate

# ۳. نصب کتابخانه‌ها
pip install -r requirements.txt
```

---

## ۳️⃣ تنظیم .env

```bash
cp .env.example .env
```

فایل `.env` را با هر ادیتوری باز کن و پر کن:

```ini
BOT_TOKEN=1234567890:AAA....دریافتی از BotFather
OWNER_ID=123456789
ADMIN_IDS=111111111,222222222      # اختیاری
DB_PATH=data/ghayoomi.db
```

> 📌 **توکن را به هیچ‌کس نده و داخل git هم نذار** — فایل `.env` به صورت پیش‌فرض gitignore شده.

---

## ۴️⃣ پر کردن محتوای اولیه

```bash
python scripts/seed_database.py
```

خروجی باید بگوید:
```
✅ 87 کارت و 7 آزمون نمونه به دیتابیس اضافه شد! 🎉
```

اگر قبلاً دیتابیس داشتی، از `--force` استفاده کن.

---

## ۵️⃣ خوشایندسازی پروفایل ربات ⭐

این اسکریپت اسم نمایشی، بیوگرافی (about)، متن پیش‌نمایش چت (description) و منوی دستورها را با متن‌های آمادهٔ برند خودکار می‌چیند:

```bash
python scripts/setup_bot_profile.py
```

> 🖼 فقط **عکس پروفایل** را دستی از @BotFather ← `/setuserpic` بذار 👌

---

## ۶️⃣ روشن کردن ربات

```bash
python bot.py
```

باید این لاگ را ببینی:

```
🗄 دیتابیس آماده شد
🔔 زمان‌بند یادآور روزانه فعال شد
🚀 ربات روشن شد: @GhayoomiARBot (Ghayoomi Examer)
```

حالا در تلگرام به رباتت برو و `/start` بزن — باید با لحن برند جواب بده! 🎉

---

## ۷️⃣ همیشه‌روشن نگه داشتن

### 🐳 با Docker (پیشنهادی برای VPS)

```bash
docker build -t ghayoomi-examer .
docker run -d --name ghayoomi --env-file .env -v $(pwd)/data:/app/data ghayoomi-examer
```

### 🛠 با systemd (روی VPS لینوکسی)

فایل `deploy/ghayoomi.service` را به `/etc/systemd/system/` کپی کن، مسیرها را اصلاح کن و:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ghayoomi
sudo systemctl status ghayoomi
```

### 💻 روی PC (موقت)

پنجرهٔ ترمینال را باز نگه دار — با بسته‌شدن ترمینال ربات خاموش می‌شود.

---

## ❓ مشکل داشتی؟

| خطا | علت احتمالی |
|---|---|
| `BOT_TOKEN خالی است` | .env پر نشده یا اسمش اشتباه است (حتماً `.env` باشد نه `env`) |
| `Unauthorized` / 401 | توکن اشتباه است — دوباره از BotFather بگیر |
| `Conflict: terminated by other getUpdates` | دو رانر همزمان دارند — فقط یکی را روشن نگه دار |
| ربات جواب نمی‌دهد | لاگ ترمینال را بخوان — اکثر مشکلات خودتش می‌گوید چی شده |

می‌خوای آنلاین بمونه ولی VPS نداری؟ گزینه‌ها: هاست always-on ایرانی، Railway، PythonAnywhere — برای راهنمایی بیشتر سر بزن به docs :) 🛠
