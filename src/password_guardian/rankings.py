"""Local-only storage. Connections are owned by the calling worker thread."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import os
import sqlite3

from .config import RULESET
from .session import Result

ORDER = "score DESC, correct_count DESC, revive_count ASC, id ASC"
SCHEMA_VERSION = 1


def default_data_dir():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share"))
    return base / "PasswordGuardian"


@dataclass(frozen=True)
class Board:
    rows: tuple[dict, ...]
    total: int
    own: dict | None


class RankingRepository:
    def __init__(self, path):
        self.path = Path(path)

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=0.35)
        try:
            con.row_factory = sqlite3.Row
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ValueError("지원하지 않는 랭킹 DB 버전입니다. 원본을 보존합니다.")
            if version == 0:
                if con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise ValueError("알 수 없는 DB 구조입니다. 원본을 보존합니다.")
                with con:
                    con.execute('''CREATE TABLE rankings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL UNIQUE,
                        ruleset_version TEXT NOT NULL,
                        score INTEGER NOT NULL CHECK(score >= 0),
                        correct_count INTEGER NOT NULL CHECK(correct_count BETWEEN 0 AND 3),
                        revive_count INTEGER NOT NULL CHECK(revive_count >= 0),
                        enemy_kills INTEGER NOT NULL CHECK(enemy_kills >= 0),
                        boss_defeated INTEGER NOT NULL CHECK(boss_defeated IN (0, 1)),
                        completed_at TEXT NOT NULL
                    )''')
                    con.execute(f"CREATE INDEX rank_order ON rankings(ruleset_version, {ORDER})")
                    con.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            return con
        except Exception:
            con.close()
            raise

    def record(self, result: Result):
        if not result.eligible:
            return self.board(result.ruleset_version)
        con = self.connect()
        try:
            with con:
                con.execute('''INSERT INTO rankings
                    (session_id,ruleset_version,score,correct_count,revive_count,enemy_kills,boss_defeated,completed_at)
                    VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(session_id) DO NOTHING''',
                    (result.session_id, result.ruleset_version, result.score, result.correct_count,
                     result.revive_count, result.enemy_kills, int(result.boss_defeated), result.completed_at))
        finally:
            con.close()
        return self.board(result.ruleset_version, result.session_id)

    def board(self, ruleset=RULESET, session_id=None):
        con = self.connect()
        try:
            # The same read transaction keeps count, TOP 10 and own rank consistent.
            con.execute("BEGIN")
            total = con.execute("SELECT COUNT(*) FROM rankings WHERE ruleset_version=?", (ruleset,)).fetchone()[0]
            query = f'''WITH ranked AS (
                SELECT *, ROW_NUMBER() OVER (ORDER BY {ORDER}) AS rank
                FROM rankings WHERE ruleset_version=?
            ) SELECT * FROM ranked'''
            rows = tuple(dict(row) for row in con.execute(query + " ORDER BY rank LIMIT 10", (ruleset,)))
            own = con.execute(query + " WHERE session_id=?", (ruleset, session_id)).fetchone() if session_id else None
            return Board(rows, total, dict(own) if own else None)
        finally:
            con.close()

    def backup(self, destination):
        destination = Path(destination).resolve()
        if destination == self.path.resolve() or destination.exists():
            raise ValueError("백업은 기존 파일이 없는 별도 경로를 지정하세요.")
        source = self.connect()
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("백업 검증에 실패했습니다.")
        finally:
            target.close()
            source.close()

    def reset(self, backup_path):
        self.backup(backup_path)
        con = self.connect()
        try:
            with con:
                con.execute("DELETE FROM rankings")
        finally:
            con.close()


class RankingWorker:
    def __init__(self, path):
        self.repository = RankingRepository(path)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="guardian-ranking")

    def submit(self, result=None):
        def work():
            for attempt in range(2):
                try:
                    return self.repository.record(result) if result else self.repository.board()
                except sqlite3.OperationalError as exc:
                    if attempt or not any(word in str(exc).lower() for word in ("locked", "busy")):
                        raise
            raise RuntimeError("기록 저장에 실패했습니다.")
        return self.executor.submit(work)

    def close(self):
        self.executor.shutdown(wait=False, cancel_futures=False)


def participant_code(record_id):
    return f"수호자-{record_id:06d}"
