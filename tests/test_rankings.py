from dataclasses import replace
from datetime import datetime
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from password_guardian.rankings import RankingRepository, RankingWorker, default_data_dir
from password_guardian.session import Session

TODAY = datetime(2026, 10, 24, 14, 0)


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.path = self.folder / "data" / "ranking.json"
        self.now = TODAY
        self.repo = RankingRepository(self.path, clock=lambda: self.now)
        self.minute = 0

    def tearDown(self):
        self.temp.cleanup()

    def result(self, score=100, correct=1, revives=1, day="2026-10-24", **kwargs):
        self.minute += 1  # later results complete later
        stamp = f"{day}T10:{self.minute:02}:00+09:00"
        return replace(Session().finish(), score=score, correct_count=correct, revive_count=revives,
                       completed_at=stamp, **kwargs)

    def test_zero_score_persists_and_duplicate_is_idempotent(self):
        result = self.result(score=0)
        first = self.repo.record(result, "ABC")
        again = RankingRepository(self.path, clock=lambda: self.now).record(result, "ABC")
        self.assertEqual(again.total, 1)
        self.assertEqual(first.own, again.own)
        self.assertEqual(first.own["name"], "ABC")

    def test_ties_correct_revives_then_earlier_first(self):
        a = self.result(100, 1, 0)
        b = self.result(100, 2, 2)
        c = self.result(100, 2, 1)
        d = self.result(100, 2, 1)
        for result in (d, a, c, b):  # saving order does not matter; completion time does
            self.repo.record(result)
        self.assertEqual([r["session_id"] for r in self.repo.board().rows],
                         [c.session_id, d.session_id, b.session_id, a.session_id])

    def test_top_ten_and_own_position_outside_ten(self):
        target = self.result(0)
        self.repo.record(target)
        for score in range(1, 13):
            self.repo.record(self.result(score))
        board = self.repo.board(session_id=target.session_id)
        self.assertEqual((len(board.rows), board.total, board.own["rank"]), (10, 13, 13))
        self.assertEqual([r["rank"] for r in board.rows], list(range(1, 11)))

    def test_only_today_counts(self):
        self.repo.record(self.result(900, day="2026-10-23"))
        self.repo.record(self.result(100))
        board = self.repo.board()
        self.assertEqual((board.total, [r["score"] for r in board.rows]), (1, [100]))
        self.now = datetime(2026, 10, 25, 9, 0)  # the next morning starts empty
        self.assertEqual(self.repo.board().total, 0)
        self.assertEqual(len(self.repo.load()), 2)  # older days stay in the file

    def test_unsaved_candidate_rank(self):
        for score in (300, 200, 100):
            self.repo.record(self.result(score))
        self.assertEqual(self.repo.board(candidate=self.result(200)).own["rank"], 3)  # behind the earlier 200
        self.assertEqual(self.repo.board(candidate=self.result(250)).own["rank"], 2)
        self.assertEqual(self.repo.board().total, 3)

    def test_practice_not_saved_and_rulesets_separate(self):
        self.repo.record(self.result(eligible=False))
        self.assertFalse(self.path.exists())
        self.repo.record(self.result(ruleset_version="other"))
        self.assertEqual(self.repo.board().total, 0)
        self.assertEqual(self.repo.board("other").total, 1)

    def test_invalid_score_rejected(self):
        with self.assertRaises(ValueError):
            self.repo.record(self.result(score=-1))
        self.assertEqual(self.repo.board().total, 0)

    def test_broken_file_moved_aside_and_bad_rows_skipped(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{ not json", encoding="utf-8")
        self.assertEqual(self.repo.board().total, 0)
        broken = list(self.path.parent.glob("ranking_broken_*.json"))
        self.assertEqual([p.read_text(encoding="utf-8") for p in broken], ["{ not json"])
        good = self.result(50)
        self.repo.record(good)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["records"].append({"name": "ZZZ", "score": "lots"})  # hand-edited by mistake
        self.path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual([r["session_id"] for r in self.repo.board().rows], [good.session_id])

    def test_save_keeps_previous_file(self):
        self.repo.record(self.result(10))
        self.repo.record(self.result(20))
        previous = json.loads(self.path.with_name("ranking.json.bak").read_text(encoding="utf-8"))
        self.assertEqual(len(previous["records"]), 1)

    def test_backup_reset_and_restore(self):
        self.repo.record(self.result())
        backup = self.folder / "backup.json"
        self.repo.reset(backup)
        self.assertEqual(self.repo.board().total, 0)
        self.assertEqual(RankingRepository(backup, clock=lambda: self.now).board().total, 1)

    def test_existing_backup_refused_without_resetting(self):
        self.repo.record(self.result())
        backup = self.folder / "backup.json"
        backup.write_bytes(b"existing backup")
        with self.assertRaises(ValueError):
            self.repo.reset(backup)
        self.assertEqual(self.repo.board().total, 1)
        self.assertEqual(backup.read_bytes(), b"existing backup")

    def test_default_folder_is_data_beside_the_game(self):
        self.assertEqual(default_data_dir(), Path(__file__).resolve().parents[1] / "data")

    def test_background_worker_commits_results(self):
        worker = RankingWorker(self.path)
        try:
            result = replace(Session().finish())
            board = worker.submit(result).result(timeout=5)
            self.assertEqual(board.own["session_id"], result.session_id)
            self.assertEqual(worker.submit(result).result(timeout=5).total, 1)
        finally:
            worker.close()


if __name__ == "__main__":
    unittest.main()
