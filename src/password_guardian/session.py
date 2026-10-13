from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from .config import RULESET

WEAPON_MAX = 4


@dataclass(frozen=True)
class ChoiceRecord:
    selection: int | None
    correct: bool


@dataclass(frozen=True)
class Result:
    session_id: str
    ruleset_version: str
    score: int
    correct_count: int
    revive_count: int
    enemy_kills: int
    boss_defeated: bool
    completed_at: str
    choices: tuple[ChoiceRecord, ...]
    eligible: bool

    @property
    def grade(self):
        return grade_for(self.score)


def grade_for(score):
    # Set from simulated runs after the density change: standing still ~1,000-4,700, steady movement 4,000-8,800.
    return "S" if score >= 6500 else "A" if score >= 4500 else "B" if score >= 2500 else "C"


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    score: int = 0
    hp: int = 3
    shield: int = 0
    damage: int = 1
    weapon: int = 1  # firing pattern level, 1 to WEAPON_MAX; kept after hits
    skills: int = 3
    revive_count: int = 0
    enemy_kills: int = 0
    boss_defeated: bool = False
    choices: list[ChoiceRecord | None] = field(default_factory=lambda: [None, None, None])
    frozen: bool = False

    def add_score(self, amount):
        if not self.frozen:
            self.score = max(0, self.score + amount)

    def choose(self, stage, selection, correct_number=2):
        if self.frozen or self.choices[stage] is not None:
            return False
        correct = selection == correct_number
        self.choices[stage] = ChoiceRecord(selection, correct)
        if correct:
            self.add_score(200)
            if stage == 0:
                self.shield += 2
            elif stage == 1:
                self.damage = 2
            else:
                self.skills += 2
        return True

    def power_up(self):
        if self.frozen or self.weapon >= WEAPON_MAX:
            return False
        self.weapon += 1
        return True

    def finish(self, eligible=True):
        self.frozen = True
        records = tuple(c or ChoiceRecord(None, False) for c in self.choices)
        return Result(self.session_id, RULESET, self.score, sum(c.correct for c in records),
                      self.revive_count, self.enemy_kills, self.boss_defeated,
                      datetime.now(timezone.utc).isoformat(), records, eligible)
