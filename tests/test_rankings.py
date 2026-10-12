from dataclasses import replace
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from password_guardian.rankings import RankingRepository, RankingWorker
from password_guardian.session import Session


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.path = self.folder / "rankings.sqlite3"
        self.repo = RankingRepository(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def result(self, score=100, correct=1, revives=1, **kwargs):
        return replace(Session().finish(), score=score, correct_count=correct, revive_count=revives, **kwargs)

    def test_zero_score_persists_and_duplicate_is_idempotent(self):
        result = self.result(score=0)
        first = self.repo.record(result)
        again = RankingRepository(self.path).record(result)
        self.assertEqual(again.total, 1)
        self.assertEqual(first.own, again.own)

    def test_ties_correct_revives_then_insertion_order(self):
        a = self.result(100, 1, 0)
        b = self.result(100, 2, 2)
        c = self.result(100, 2, 1)
        d = self.result(100, 2, 1)
        for result in (a, b, c, d):
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

    def test_practice_not_saved_and_rulesets_separate(self):
        self.repo.record(self.result(eligible=False))
        self.assertEqual(self.repo.board().total, 0)
        self.repo.record(self.result(ruleset_version="other"))
        self.assertEqual(self.repo.board().total, 0)
        self.assertEqual(self.repo.board("other").total, 1)

    def test_invalid_score_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.record(self.result(score=-1))
        self.assertEqual(self.repo.board().total, 0)

    def test_corrupt_database_is_not_replaced(self):
        content = b"not a sqlite database; preserve me"
        self.path.write_bytes(content)
        with self.assertRaises(sqlite3.DatabaseError):
            self.repo.board()
        self.assertEqual(self.path.read_bytes(), content)

    def test_unknown_version_is_not_replaced(self):
        self.repo.board()
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version=99")
        con.close()
        content = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.repo.board()
        self.assertEqual(self.path.read_bytes(), content)

    def test_backup_reset_and_restore(self):
        self.repo.record(self.result())
        backup = self.folder / "backup.sqlite3"
        self.repo.reset(backup)
        self.assertEqual(self.repo.board().total, 0)
        self.assertEqual(RankingRepository(backup).board().total, 1)

    def test_existing_backup_refused_without_resetting(self):
        self.repo.record(self.result())
        backup = self.folder / "backup.sqlite3"
        backup.write_bytes(b"existing backup")
        with self.assertRaises(ValueError):
            self.repo.reset(backup)
        self.assertEqual(self.repo.board().total, 1)
        self.assertEqual(backup.read_bytes(), b"existing backup")

    def test_background_worker_commits_results(self):
        worker = RankingWorker(self.path)
        try:
            result = self.result()
            board = worker.submit(result).result(timeout=5)
            self.assertEqual(board.own["session_id"], result.session_id)
            self.assertEqual(worker.submit(result).result(timeout=5).total, 1)
        finally:
            worker.close()


if __name__ == "__main__":
    unittest.main()
