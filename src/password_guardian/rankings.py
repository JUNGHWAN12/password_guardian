"""Today's TOP 10 on this PC, kept in data/ranking.json beside the game like the booth's other two games.

File access runs on a worker thread. A save writes a temporary file and swaps it in, so a power cut never
leaves half a file, and the previous file stays as ranking.json.bak.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import os
import shutil
import sys

from .config import ROOT, RULESET
from .session import Result

TOP = 10
FILE_VERSION = 1
ANONYMOUS = "???"
FIELDS = {"session_id": str, "ruleset_version": str, "name": str, "score": int, "correct_count": int,
          "revive_count": int, "enemy_kills": int, "boss_defeated": bool, "completed_at": str}


def default_data_dir():
    # Beside PasswordGuardian.exe in a build, the project folder otherwise. One folder to clear after the event.
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else ROOT
    return base / "data"


def sort_key(row):
    # Score, then more correct answers, then fewer revivals, then whoever got there first.
    return (-row["score"], -row["correct_count"], row["revive_count"], row["completed_at"])


def valid(row):
    return (isinstance(row, dict) and all(isinstance(row.get(k), t) for k, t in FIELDS.items())
            and row["score"] >= 0 and 0 <= row["correct_count"] <= 3 and row["revive_count"] >= 0)


def row_for(result: Result, name):
    return {"session_id": result.session_id, "ruleset_version": result.ruleset_version, "name": name,
            "score": result.score, "correct_count": result.correct_count, "revive_count": result.revive_count,
            "enemy_kills": result.enemy_kills, "boss_defeated": result.boss_defeated,
            "completed_at": result.completed_at}


@dataclass(frozen=True)
class Board:
    rows: tuple[dict, ...]  # today's TOP 10, each with its "rank"
    total: int  # records today
    own: dict | None  # the record asked about, with its rank today


class RankingRepository:
    def __init__(self, path, clock=datetime.now):
        self.path = Path(path)
        self.clock = clock

    def stamp(self):
        return self.clock().strftime("%Y%m%d_%H%M%S")

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            # Rows an operator mistyped while editing by hand are skipped, not fatal.
            return [row for row in data["records"] if valid(row)]
        except (ValueError, KeyError, TypeError):
            # A broken file is moved aside, never deleted, and the game carries on with an empty board.
            os.replace(self.path, self.path.with_name(f"ranking_broken_{self.stamp()}.json"))
            return []

    def save(self, rows):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            shutil.copy2(self.path, self.path.with_name(self.path.name + ".bak"))
        temp = self.path.with_name(self.path.name + ".tmp")
        temp.write_text(json.dumps({"version": FILE_VERSION, "records": rows}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        os.replace(temp, self.path)

    def today(self, rows, ruleset=RULESET):
        day = self.clock().date().isoformat()
        return sorted((r for r in rows if r["completed_at"][:10] == day and r["ruleset_version"] == ruleset),
                      key=sort_key)

    def board(self, ruleset=RULESET, session_id=None, candidate: Result | None = None):
        today = self.today(self.load(), ruleset)
        ranked = [dict(row, rank=i+1) for i, row in enumerate(today)]
        own = next((row for row in ranked if row["session_id"] == session_id), None) if session_id else None
        if candidate is not None and own is None:
            # Where an unsaved result would land: behind every equal record, since those came first.
            row = row_for(candidate, None)
            own = dict(row, rank=1 + sum(sort_key(r) <= sort_key(row) for r in today))
        return Board(tuple(ranked[:TOP]), len(today), own)

    def record(self, result: Result, name):
        if not result.eligible:
            return self.board(result.ruleset_version)
        row = row_for(result, name)
        if not valid(row):
            raise ValueError("기록 형식이 올바르지 않습니다.")
        rows = self.load()
        if not any(r["session_id"] == result.session_id for r in rows):
            self.save(rows + [row])
        return self.board(result.ruleset_version, result.session_id)

    def backup(self, destination):
        destination = Path(destination).resolve()
        if destination == self.path.resolve() or destination.exists():
            raise ValueError("백업은 기존 파일이 없는 별도 경로를 지정하세요.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({"version": FILE_VERSION, "records": self.load()}, ensure_ascii=False,
                                          indent=1), encoding="utf-8")

    def reset(self, backup_path):
        self.backup(backup_path)
        self.save([])


class RankingWorker:
    def __init__(self, path):
        self.repository = RankingRepository(path)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="guardian-ranking")

    def submit(self, result=None, name=None):
        # No result: today's board. A result without a name: where it would rank, unsaved. Both: save it.
        def work():
            if result is None:
                return self.repository.board()
            if name is None:
                return self.repository.board(result.ruleset_version, candidate=result)
            return self.repository.record(result, name)
        return self.executor.submit(work)

    def close(self):
        self.executor.shutdown(wait=False, cancel_futures=False)
