"""🧪 تست‌های یکتای هستهٔ ربات — اجرا: python -m unittest discover -s tests -v"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.db import DB  # noqa: E402
from src import importer  # noqa: E402
from src.utils import (  # noqa: E402
    compute_taraz, fmt_time_limit, rank_key,
)


class TestUtils(unittest.TestCase):
    def test_taraz_single(self):
        self.assertEqual(compute_taraz([70.0]), [5000.0])

    def test_taraz_symmetric(self):
        tar = compute_taraz([50.0, 60.0, 40.0])
        self.assertAlmostEqual(sum(tar) / len(tar), 5000.0, places=1)
        self.assertGreater(tar[1], tar[0])
        self.assertGreater(tar[0], tar[2])

    def test_rank_key_order(self):
        a = {"percent": 80.0, "duration": 100}
        b = {"percent": 80.0, "duration": 50}
        c = {"percent": 90.0, "duration": 200}
        ordered = sorted([c, b, a], key=rank_key)
        self.assertEqual(ordered, [c, b, a])

    def test_fmt_time_limit(self):
        self.assertIn("بدون", fmt_time_limit(0))
        self.assertIn("۱۰", fmt_time_limit(600))


class TestDB(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = DB(self.tmp.name)

    def tearDown(self):
        self.db.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_user_flow(self):
        db = self.db
        db.upsert_user(1, "ali")
        self.assertIsNotNone(db.get_user(1))
        db.set_user_field(1, "name", "علی قیومی")
        db.set_user_field(1, "grade", "دهم")
        db.set_user_field(1, "major", "ریاضی فیزیک")
        u = db.get_user(1)
        self.assertEqual(u["name"], "علی قیومی")
        self.assertEqual(u["grade"], "دهم")

    def test_cards_and_views(self):
        db = self.db
        cid = db.add_card("دهم", 1, "لغات", "protect", "محافظت کردن", "Ex.", "")
        deck = db.get_deck("دهم", 1, "لغات")
        self.assertEqual(len(deck), 1)
        self.assertTrue(db.log_card_view(9, cid))
        self.assertFalse(db.log_card_view(9, cid))  # تکراری در همان روز
        self.assertEqual(db.user_cards_viewed(9), 1)

    def test_exam_attempt_flow(self):
        db = self.db
        db.upsert_user(7, "stu")
        eid = db.create_exam("🧪 تست", "دهم", "1", 600, 0)
        db.add_question(eid, 1, "سؤال؟", "الف", "ب", "ج", "د", 2, "")
        db.add_question(eid, 2, "سؤال ۲؟", "1", "2", "3", "4", 4, "")
        self.assertEqual(db.exam_question_count(eid), 2)

        order = [1, 2]
        aid = db.start_attempt(7, eid, order, 2)
        self.assertIsNotNone(db.get_attempt(7, eid))
        db.save_answer(aid, 1, 2, True)   # درست
        db.save_answer(aid, 2, 1, False)  # غلط
        db.finish_attempt(aid, 120)
        att = db.get_attempt_by_id(aid)
        self.assertEqual(att["score"], 1)
        self.assertAlmostEqual(att["percent"], 50.0)

    def test_publish_results(self):
        db = self.db
        eid = db.create_exam("🧪 تست", "دهم", "1", 0, 0)
        for q in range(4):
            db.add_question(eid, q + 1, f"Q{q}", "a", "b", "c", "d", 1, "")
        results = [(100, 100), (200, 50)]
        exp_ranks = {100: 1, 200: 2}
        for uid, score in results:
            db.upsert_user(uid, f"u{uid}")
            aid = db.start_attempt(uid, eid, [1, 2, 3, 4], 4)
            n_correct = score // 25
            for q in range(1, 5):
                db.save_answer(aid, q, 1, q <= n_correct)
            db.finish_attempt(aid, 300)
        atts = db.publish_exam_results(eid)
        self.assertEqual(len(atts), 2)
        exam = db.get_exam(eid)
        self.assertEqual(exam["results_published"], 1)
        for uid, _ in results:
            att = db.get_attempt(uid, eid)
            self.assertEqual(att["rank_pos"], exp_ranks[uid])

    def test_leaderboard(self):
        db = self.db
        db.upsert_user(1, "a")
        db.upsert_user(2, "b")
        db.set_user_field(1, "name", "الف")
        db.set_user_field(2, "name", "ب")
        db.add_points(1, 50, "exam")
        db.add_points(2, 100, "flashcard")
        lb = db.leaderboard(days=7)
        self.assertEqual(lb[0]["id"], 2)
        self.assertEqual(db.user_points(1), 50)


class TestImporter(unittest.TestCase):
    def test_csv_questions(self):
        raw = ("question,option1,option2,option3,option4,correct,explanation\n"
               "معنی protect؟,محافظت,تخریب,آلودگی,خطری,1,نکته\n").encode()
        rows = importer.parse_questions_csv(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["correct"], 1)

    def test_csv_questions_bad(self):
        raw = b"question,option1,option2,option3,option4,correct\nq,a,b,c,d,9\n"
        with self.assertRaises(importer.ImportError_):
            importer.parse_questions_csv(raw)

    def test_csv_cards(self):
        raw = "front,back,example,tip\nword,کلمه,He has a word.,tip1\n".encode()
        rows = importer.parse_cards_csv(raw)
        self.assertEqual(rows[0]["front"], "word")

    def test_json_cards(self):
        raw = json.dumps([{"front": "x", "back": "y", "example": "", "tip": ""}]).encode()
        rows = importer.parse_cards_json(raw)
        self.assertEqual(len(rows), 1)

    def test_json_questions(self):
        raw = json.dumps([{
            "text": "Q?", "options": ["a", "b", "c", "d"], "correct": 3,
        }]).encode()
        rows = importer.parse_questions_json(raw)
        self.assertEqual(rows[0]["correct"], 3)


if __name__ == "__main__":
    unittest.main()
