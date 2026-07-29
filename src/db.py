"""🗄 لایه دیتابیس (SQLite) — اسکیما، CRUD و توابع آماری ربات Ghayoomi Examer."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .utils import (
    compute_taraz, days_ago_str, now_str, rank_key, today_str,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    username        TEXT,
    name            TEXT NOT NULL DEFAULT '',
    grade           TEXT DEFAULT '',
    major           TEXT DEFAULT '',
    role            TEXT NOT NULL DEFAULT 'student',   -- owner / admin / student
    is_blocked      INTEGER NOT NULL DEFAULT 0,
    reminder_on     INTEGER NOT NULL DEFAULT 0,
    reminder_hour   INTEGER NOT NULL DEFAULT 8,
    last_reminded   TEXT DEFAULT '',
    created_at      TEXT NOT NULL,
    last_active     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    grade       TEXT NOT NULL,
    lesson      INTEGER NOT NULL,
    category    TEXT NOT NULL,          -- لغات / گرامر / عبارات
    front       TEXT NOT NULL,
    back        TEXT NOT NULL DEFAULT '',
    example     TEXT NOT NULL DEFAULT '',
    tip         TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS card_views (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    day     TEXT NOT NULL,
    UNIQUE (user_id, card_id, day)
);

CREATE TABLE IF NOT EXISTS exams (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    title              TEXT NOT NULL,
    grade              TEXT NOT NULL,
    lessons            TEXT NOT NULL DEFAULT 'همه',   -- مثل: 1,3 یا همه
    time_limit         INTEGER NOT NULL DEFAULT 0,    -- ثانیه؛ 0 = بدون زمان
    is_active          INTEGER NOT NULL DEFAULT 1,
    results_published  INTEGER NOT NULL DEFAULT 0,
    created_by         INTEGER,
    created_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id     INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    idx         INTEGER NOT NULL,
    text        TEXT NOT NULL,
    opt1        TEXT NOT NULL,
    opt2        TEXT NOT NULL,
    opt3        TEXT NOT NULL,
    opt4        TEXT NOT NULL,
    correct     INTEGER NOT NULL,       -- 1..4
    explanation TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    exam_id      INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    order_json   TEXT NOT NULL DEFAULT '[]',
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    duration     INTEGER NOT NULL DEFAULT 0,
    score        INTEGER NOT NULL DEFAULT 0,
    total        INTEGER NOT NULL DEFAULT 0,
    percent      REAL NOT NULL DEFAULT 0,
    taraz        REAL NOT NULL DEFAULT 0,
    rank_pos     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (user_id, exam_id)
);

CREATE TABLE IF NOT EXISTS attempt_answers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id  INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    chosen      INTEGER NOT NULL,
    is_correct  INTEGER NOT NULL,
    answered_at TEXT NOT NULL,
    UNIQUE (attempt_id, question_id)
);

CREATE TABLE IF NOT EXISTS points_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    points     INTEGER NOT NULL,
    source     TEXT NOT NULL,          -- flashcard / exam
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_texts (
    key     TEXT PRIMARY KEY,          -- about / contact / guide
    value   TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS broadcasts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    sent       INTEGER NOT NULL DEFAULT 0,
    failed     INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cards_glc       ON cards(grade, lesson, category);
CREATE INDEX IF NOT EXISTS idx_q_exam          ON questions(exam_id, idx);
CREATE INDEX IF NOT EXISTS idx_att_exam        ON attempts(exam_id);
CREATE INDEX IF NOT EXISTS idx_points_user     ON points_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_card_views      ON card_views(user_id, day);
"""


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def init_db(db_path: str) -> None:
    con = connect(db_path)
    with con:
        con.executescript(_SCHEMA)
    con.close()


class DB:
    """کلاس اصلی کار با دیتابیس — در همه هندلرها استفاده می‌شود."""

    def __init__(self, db_path: str):
        init_db(db_path)
        self.con = connect(db_path)
        self._migrate_users_in_panel()

    def _migrate_users_in_panel(self) -> None:
        """🆕 افزودن ستون in_panel (۱ = کاربر الان داخل پنل مدیریت است)."""
        try:
            self.con.execute("ALTER TABLE users ADD COLUMN in_panel INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # ستون از قبل هست

    # ─────────────── کاربران ───────────────

    def users_total(self) -> int:
        """🆕 تعداد کل کاربران (برای صفحه‌بندی)."""
        return self.con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]

    def users_page(self, offset: int, limit: int) -> list[sqlite3.Row]:
        """🆕 یک صفحه از کاربران — جدیدترین‌ها اول (صاحب/ادمین هم داخل لیست می‌مانند)."""
        return self.con.execute(
            "SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()

    def upsert_user(self, uid: int, username: str | None) -> None:
        with self.con:
            self.con.execute(
                """INSERT INTO users (id, username, created_at, last_active)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET username = excluded.username,
                                                 last_active = excluded.last_active""",
                (uid, username, now_str(), now_str()),
            )

    def touch(self, uid: int) -> None:
        with self.con:
            self.con.execute(
                "UPDATE users SET last_active = ? WHERE id = ?", (now_str(), uid)
            )

    def get_user(self, uid: int) -> sqlite3.Row | None:
        cur = self.con.execute("SELECT * FROM users WHERE id = ?", (uid,))
        return cur.fetchone()

    def set_user_field(self, uid: int, field: str, value) -> None:
        allowed = {
            "name", "grade", "major", "role", "is_blocked",
            "reminder_on", "reminder_hour", "last_reminded", "in_panel",
        }
        if field not in allowed:
            raise ValueError(f"field not allowed: {field}")
        with self.con:
            self.con.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, uid))

    def all_users(self, only_active: bool = False) -> list[sqlite3.Row]:
        q = "SELECT * FROM users"
        if only_active:
            q += " WHERE is_blocked = 0 AND role != 'ghost'"
        return self.con.execute(q).fetchall()

    def filtered_users(
        self,
        grades: list[str] | None = None,
        majors: list[str] | None = None,
        only_active: bool = True,
    ) -> list[sqlite3.Row]:
        """🆕 فیلتر کاربران برای پیام همگانی: ترکیب پایه + رشته.
        - اگه هر دو خالی باشن: همه.
        - اگه فقط یکی پر باشه: همون شرط.
        - اگه هر دو پر باشن: AND."""
        where = []
        params: list = []
        if only_active:
            where.append("is_blocked = 0")
            where.append("role != 'ghost'")
        if grades:
            placeholders = ",".join("?" * len(grades))
            where.append(f"grade IN ({placeholders})")
            params.extend(grades)
        if majors:
            placeholders = ",".join("?" * len(majors))
            where.append(f"major IN ({placeholders})")
            params.extend(majors)
        q = "SELECT * FROM users"
        if where:
            q += " WHERE " + " AND ".join(where)
        return self.con.execute(q, params).fetchall()

    def search_users(self, term: str, role_filter: str | None = None) -> list[sqlite3.Row]:
        """جستجوی کاربر: آیدی، نام، یا نام کاربری (با یا بدون @).
        اگه role_filter داده بشه، فقط کاربران با اون نقش برمی‌گرده."""
        term = (term or "").strip()
        where_extra = ""
        params: list = []
        if role_filter:
            where_extra = " AND role = ?"
            params.append(role_filter)

        if term.isdigit():
            rows = self.con.execute(
                f"SELECT * FROM users WHERE id = ?{where_extra} ORDER BY id DESC LIMIT 20",
                (int(term), *params),
            ).fetchall()
            if rows:
                return rows
        # حذف @ اگه اولش باشه
        clean = term.lstrip("@").strip()
        like = f"%{clean}%"
        return self.con.execute(
            f"""SELECT * FROM users
                WHERE (name LIKE ? OR username LIKE ?){where_extra}
                ORDER BY id DESC LIMIT 20""",
            (like, like, *params),
        ).fetchall()

    def admin_ids(self) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT id, name FROM users WHERE role IN ('owner','admin')"
        ).fetchall()

    def user_counts(self) -> dict:
        total = self.con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        blocked = self.con.execute(
            "SELECT COUNT(*) c FROM users WHERE is_blocked = 1"
        ).fetchone()["c"]
        today = self.con.execute(
            "SELECT COUNT(*) c FROM users WHERE last_active >= ?", (days_ago_str(1),)
        ).fetchone()["c"]
        week = self.con.execute(
            "SELECT COUNT(*) c FROM users WHERE last_active >= ?", (days_ago_str(7),)
        ).fetchone()["c"]
        return {"total": total, "blocked": blocked, "today": today, "week": week}

    # ─────────────── فلش کارت ───────────────

    def add_card(self, grade, lesson, category, front, back, example, tip) -> int:
        with self.con:
            cur = self.con.execute(
                """INSERT INTO cards (grade, lesson, category, front, back, example, tip, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (grade, lesson, category, front, back, example, tip, now_str()),
            )
            return int(cur.lastrowid)

    def delete_card(self, card_id: int) -> None:
        with self.con:
            self.con.execute("DELETE FROM cards WHERE id = ?", (card_id,))

    def get_deck(self, grade: str, lesson: int, category: str) -> list[sqlite3.Row]:
        return self.con.execute(
            """SELECT * FROM cards WHERE grade=? AND lesson=? AND category=?
               ORDER BY id""",
            (grade, lesson, category),
        ).fetchall()

    def deck_random(self, grade: str, category: str, limit: int = 15) -> list[sqlite3.Row]:
        return self.con.execute(
            """SELECT * FROM cards WHERE grade=? AND category=?
               ORDER BY RANDOM() LIMIT ?""",
            (grade, category, limit),
        ).fetchall()

    def card_counts(self, grade: str | None = None) -> list[sqlite3.Row]:
        if grade:
            return self.con.execute(
                """SELECT lesson, category, COUNT(*) c FROM cards
                   WHERE grade=? GROUP BY lesson, category""",
                (grade,),
            ).fetchall()
        return self.con.execute(
            "SELECT grade, lesson, category, COUNT(*) c FROM cards GROUP BY grade, lesson, category"
        ).fetchall()

    def cards_total(self) -> int:
        return self.con.execute("SELECT COUNT(*) c FROM cards").fetchone()["c"]

    def log_card_view(self, uid: int, card_id: int) -> bool:
        """اگر اولین بار نیست False برمی‌گرداند."""
        try:
            with self.con:
                self.con.execute(
                    "INSERT INTO card_views (user_id, card_id, day) VALUES (?,?,?)",
                    (uid, card_id, today_str()),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def user_cards_viewed(self, uid: int) -> int:
        return self.con.execute(
            "SELECT COUNT(DISTINCT card_id) c FROM card_views WHERE user_id=?", (uid,)
        ).fetchone()["c"]

    # ─────────────── آزمون‌ها ───────────────

    def create_exam(self, title, grade, lessons, time_limit, created_by) -> int:
        with self.con:
            cur = self.con.execute(
                """INSERT INTO exams (title, grade, lessons, time_limit, created_by, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (title, grade, lessons, time_limit, created_by, now_str()),
            )
            return int(cur.lastrowid)

    def add_question(self, exam_id, idx, text, o1, o2, o3, o4, correct, explanation="") -> None:
        with self.con:
            self.con.execute(
                """INSERT INTO questions (exam_id, idx, text, opt1, opt2, opt3, opt4, correct, explanation)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (exam_id, idx, text, o1, o2, o3, o4, correct, explanation),
            )

    def get_exam(self, exam_id: int) -> sqlite3.Row | None:
        return self.con.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()

    def exam_questions(self, exam_id: int) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM questions WHERE exam_id=? ORDER BY idx", (exam_id,)
        ).fetchall()

    def list_exams(self, grade: str | None = None, active: bool | None = None) -> list[sqlite3.Row]:
        q, args = "SELECT * FROM exams WHERE 1=1", []
        if grade:
            q += " AND grade = ?"
            args.append(grade)
        if active is not None:
            q += " AND is_active = ?"
            args.append(1 if active else 0)
        q += " ORDER BY id DESC"
        return self.con.execute(q, args).fetchall()

    def set_exam_field(self, exam_id: int, field: str, value) -> None:
        allowed = {"is_active", "results_published", "title", "time_limit"}
        if field not in allowed:
            raise ValueError(field)
        with self.con:
            self.con.execute(f"UPDATE exams SET {field}=? WHERE id=?", (value, exam_id))

    def exam_question_count(self, exam_id: int) -> int:
        return self.con.execute(
            "SELECT COUNT(*) c FROM questions WHERE exam_id=?", (exam_id,)
        ).fetchone()["c"]

    def delete_exam(self, exam_id: int) -> None:
        with self.con:
            self.con.execute("DELETE FROM questions WHERE exam_id=?", (exam_id,))
            self.con.execute("DELETE FROM attempts WHERE exam_id=?", (exam_id,))
            self.con.execute("DELETE FROM exams WHERE id=?", (exam_id,))

    # ─────────────── تلاش‌ها (attempt) ───────────────

    def get_attempt(self, uid: int, exam_id: int) -> sqlite3.Row | None:
        return self.con.execute(
            "SELECT * FROM attempts WHERE user_id=? AND exam_id=?", (uid, exam_id)
        ).fetchone()

    def start_attempt(self, uid: int, exam_id: int, order: list[int], total: int) -> int:
        with self.con:
            self.con.execute(
                "DELETE FROM attempts WHERE user_id=? AND exam_id=?", (uid, exam_id)
            )
            cur = self.con.execute(
                """INSERT INTO attempts (user_id, exam_id, order_json, started_at, total)
                   VALUES (?,?,?,?,?)""",
                (uid, exam_id, json.dumps(order), now_str(), total),
            )
            return int(cur.lastrowid)

    def get_attempt_by_id(self, attempt_id: int) -> sqlite3.Row | None:
        return self.con.execute(
            "SELECT * FROM attempts WHERE id=?", (attempt_id,)
        ).fetchone()

    def save_answer(self, attempt_id: int, question_id: int, chosen: int, is_correct: bool) -> None:
        with self.con:
            self.con.execute(
                """INSERT INTO attempt_answers (attempt_id, question_id, chosen, is_correct, answered_at)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(attempt_id, question_id) DO UPDATE SET
                     chosen = excluded.chosen,
                     is_correct = excluded.is_correct,
                     answered_at = excluded.answered_at""",
                (attempt_id, question_id, chosen, 1 if is_correct else 0, now_str()),
            )

    def get_answer(self, attempt_id: int, question_id: int) -> sqlite3.Row | None:
        return self.con.execute(
            "SELECT * FROM attempt_answers WHERE attempt_id=? AND question_id=?",
            (attempt_id, question_id),
        ).fetchone()

    def attempt_answers(self, attempt_id: int) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM attempt_answers WHERE attempt_id=?", (attempt_id,)
        ).fetchall()

    def finish_attempt(self, attempt_id: int, duration: int) -> None:
        score = self.con.execute(
            "SELECT COUNT(*) c FROM attempt_answers WHERE attempt_id=? AND is_correct=1",
            (attempt_id,),
        ).fetchone()["c"]
        total = self.get_attempt_by_id(attempt_id)["total"]
        percent = round(score / total * 100, 1) if total else 0.0
        with self.con:
            self.con.execute(
                """UPDATE attempts SET finished_at=?, duration=?, score=?, percent=?
                   WHERE id=?""",
                (now_str(), duration, score, percent, attempt_id),
            )

    def exam_attempts(self, exam_id: int, finished_only: bool = True) -> list[sqlite3.Row]:
        q = "SELECT a.*, u.name FROM attempts a JOIN users u ON u.id = a.user_id WHERE a.exam_id=?"
        if finished_only:
            q += " AND a.finished_at IS NOT NULL"
        return self.con.execute(q, (exam_id,)).fetchall()

    def user_attempts(self, uid: int) -> list[sqlite3.Row]:
        return self.con.execute(
            """SELECT a.*, e.title, e.results_published FROM attempts a
               JOIN exams e ON e.id = a.exam_id WHERE a.user_id=? ORDER BY a.id DESC""",
            (uid,),
        ).fetchall()

    def publish_exam_results(self, exam_id: int) -> list[sqlite3.Row]:
        """تراز و رتبه را برای همه تلاش‌های تمام‌شده حساب می‌کند و نتایج را منتشر می‌کند."""
        atts = self.exam_attempts(exam_id, finished_only=True)
        percents = [a["percent"] for a in atts]
        tarazs = compute_taraz(percents)
        payload = [
            {"id": a["id"], "percent": a["percent"], "duration": a["duration"], "taraz": t}
            for a, t in zip(atts, tarazs)
        ]
        payload.sort(key=rank_key)
        with self.con:
            for pos, p in enumerate(payload, start=1):
                self.con.execute(
                    "UPDATE attempts SET taraz=?, rank_pos=? WHERE id=?",
                    (p["taraz"], pos, p["id"]),
                )
            self.con.execute("UPDATE exams SET results_published=1 WHERE id=?", (exam_id,))
        return atts

    # ─────────────── امتیاز و لیدربورد ───────────────

    def add_points(self, uid: int, points: int, source: str) -> None:
        with self.con:
            self.con.execute(
                "INSERT INTO points_log (user_id, points, source, created_at) VALUES (?,?,?,?)",
                (uid, points, source, now_str()),
            )

    def user_points(self, uid: int, days: int | None = None) -> int:
        if days:
            row = self.con.execute(
                "SELECT COALESCE(SUM(points),0) s FROM points_log WHERE user_id=? AND created_at>=?",
                (uid, days_ago_str(days)),
            ).fetchone()
        else:
            row = self.con.execute(
                "SELECT COALESCE(SUM(points),0) s FROM points_log WHERE user_id=?", (uid,)
            ).fetchone()
        return int(row["s"])

    def leaderboard(self, days: int | None = None, limit: int = 10) -> list[sqlite3.Row]:
        if days:
            return self.con.execute(
                """SELECT u.id, u.name, u.grade, COALESCE(SUM(p.points),0) pts
                   FROM points_log p JOIN users u ON u.id = p.user_id
                   WHERE p.created_at >= ? AND u.is_blocked = 0
                   GROUP BY u.id ORDER BY pts DESC LIMIT ?""",
                (days_ago_str(days), limit),
            ).fetchall()
        return self.con.execute(
            """SELECT u.id, u.name, u.grade, COALESCE(SUM(p.points),0) pts
               FROM points_log p JOIN users u ON u.id = p.user_id
               WHERE u.is_blocked = 0
               GROUP BY u.id ORDER BY pts DESC LIMIT ?""",
            (limit,),
        ).fetchall()

    def leaderboard_user_pos(self, uid: int, days: int | None = None) -> int:
        rows = self.leaderboard(days=days, limit=100000)
        for i, r in enumerate(rows, start=1):
            if r["id"] == uid:
                return i
        return 0

    def exam_leaderboard(self, exam_id: int, limit: int = 10) -> list[sqlite3.Row]:
        return self.con.execute(
            """SELECT a.user_id, u.name, u.grade, a.percent, a.taraz, a.duration, a.rank_pos
               FROM attempts a JOIN users u ON u.id = a.user_id
               WHERE a.exam_id=? AND a.finished_at IS NOT NULL
               ORDER BY a.percent DESC, a.duration ASC LIMIT ?""",
            (exam_id, limit),
        ).fetchall()

    def user_best_rank(self, uid: int) -> int:
        row = self.con.execute(
            """SELECT MIN(rank_pos) m FROM attempts
               WHERE user_id=? AND rank_pos > 0
               AND exam_id IN (SELECT id FROM exams WHERE results_published=1)""",
            (uid,),
        ).fetchone()
        return int(row["m"] or 0)

    def user_avg_percent(self, uid: int) -> float:
        row = self.con.execute(
            """SELECT AVG(percent) a FROM attempts
               WHERE user_id=? AND finished_at IS NOT NULL
               AND exam_id IN (SELECT id FROM exams WHERE results_published=1)""",
            (uid,),
        ).fetchone()
        return round(float(row["a"] or 0), 1)

    # ─────────────── متن‌های قابل ویرایش ───────────────

    def get_content(self, key: str) -> str:
        row = self.con.execute(
            "SELECT value FROM content_texts WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else ""

    def set_content(self, key: str, value: str) -> None:
        with self.con:
            self.con.execute(
                """INSERT INTO content_texts (key, value, updated_at) VALUES (?,?,?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                     updated_at=excluded.updated_at""",
                (key, value, now_str()),
            )

    # ─────────────── broadcast ───────────────

    def log_broadcast(self, text: str, sent: int, failed: int, by: int) -> None:
        with self.con:
            self.con.execute(
                "INSERT INTO broadcasts (text, sent, failed, created_by, created_at) VALUES (?,?,?,?,?)",
                (text, sent, failed, by, now_str()),
            )

    def broadcasts_count(self) -> int:
        return self.con.execute("SELECT COUNT(*) c FROM broadcasts").fetchone()["c"]

    def close(self) -> None:
        self.con.close()
