"""Deterministic simulation. No graphics or filesystem side effects."""
from dataclasses import dataclass
import itertools
import math
import random

from .config import (FIELD, PLAYER_START, STEP, TUTORIAL_SECONDS, CHOICE_SECONDS,
                     ANSWER_SECONDS, COMBAT_SECONDS, RESULT_SECONDS,
                     MAX_ENEMIES, MAX_ENEMY_BULLETS, MAX_PLAYER_BULLETS)
from .content import load_content
from .session import Session


@dataclass
class Entity:
    id: int
    kind: str
    x: float
    y: float
    radius: float
    vx: float = 0
    vy: float = 0
    hp: int = 1
    fire_in: float = 1
    age: float = 0
    ttl: float = 18
    damage: int = 1


def overlaps(a, b):
    return (a.x-b.x)**2 + (a.y-b.y)**2 <= (a.radius+b.radius)**2


class Engine:
    def __init__(self, seed=None, practice=False):
        self.questions, self.wave_specs = load_content()
        self.rng = random.Random(seed)
        self.ids = itertools.count(1)
        self.practice = practice
        self.state = "TITLE"
        self.stage = 0
        self.elapsed = 0.0
        self.revision = 0
        self.session = Session()
        self.result = None
        self.events = []
        self.event_index = 0
        self.player = Entity(0, "player", *PLAYER_START, 18)
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.invulnerable = 0.0
        self.shot_in = 0.0
        self.skill_cooldown = 0.0
        self.skill_flash = 0.0
        self.damage_flash = 0.0
        self.skill_center = PLAYER_START
        self.reinforcement_in = 4.0

    def start(self):
        if self.state != "TITLE":
            return
        self.session = Session()
        self.result = None
        self.stage = 0
        self.reset_arena()
        self.enter("TUTORIAL")

    def reset_arena(self):
        self.enemies.clear()
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.player.x, self.player.y = PLAYER_START
        self.invulnerable = 0
        self.shot_in = 0
        self.skill_cooldown = 0
        self.skill_flash = 0
        self.damage_flash = 0

    def enter(self, state):
        self.state = state
        self.elapsed = 0.0
        self.revision += 1
        if state == "CHOICE":
            self.enemies.clear()
            self.player_bullets.clear()
            self.enemy_bullets.clear()
            # The boss path overrides spawn relocation, so every stage starts from a safe spot.
            self.player.x, self.player.y = PLAYER_START
        elif state == "COMBAT":
            self.events = []
            self.event_index = 0
            for spec in self.wave_specs:
                if spec["stage"] != self.stage:
                    continue
                t, i = float(spec["start"]), 0
                while t < spec["end"]:
                    self.events.append((t, spec["kinds"][i % len(spec["kinds"])], spec["count"]))
                    i += 1
                    t = spec["start"] + i * spec["interval"]
            self.events.sort()
            if self.stage == 2:
                self.spawn_enemy("boss")
                self.reinforcement_in = 4
        elif state == "RESULT":
            self.result = self.session.finish(eligible=not self.practice)
            self.player_bullets.clear()
            self.enemy_bullets.clear()
        elif state == "TITLE":
            self.reset_arena()

    @property
    def duration(self):
        return {"TUTORIAL": TUTORIAL_SECONDS, "CHOICE": CHOICE_SECONDS,
                "COMBAT": COMBAT_SECONDS, "RESULT": RESULT_SECONDS}.get(self.state, 0)

    @property
    def remaining(self):
        return max(0, self.duration-self.elapsed)

    @property
    def game_remaining(self):
        offset = self.elapsed + (CHOICE_SECONDS if self.state == "COMBAT" else 0)
        return max(0, 180 - self.stage*60 - offset)

    def choose(self, selection):
        if self.state != "CHOICE" or self.elapsed >= ANSWER_SECONDS or selection not in (1, 2):
            return False
        return self.session.choose(self.stage, selection, self.questions[self.stage]["correct"])

    def update(self, dt, movement=(0, 0)):
        if dt < 0 or not math.isfinite(dt):
            raise ValueError("delta_time must be finite and nonnegative")
        while dt > 1e-9 and self.state != "TITLE":
            step = min(STEP, dt, self.remaining)
            if step > 1e-9:
                self.tick(step, movement)
                self.elapsed += step
                dt -= step
            if self.state == "CHOICE" and self.elapsed >= ANSWER_SECONDS-1e-9:
                self.session.choose(self.stage, None, self.questions[self.stage]["correct"])
            if self.remaining < 1e-8:
                self.advance()
                movement = (0, 0)  # held keys never carry through a stage boundary

    def advance(self):
        if self.state == "TUTORIAL":
            self.session = Session()
            self.reset_arena()
            self.enter("CHOICE")
        elif self.state == "CHOICE":
            self.enter("COMBAT")
        elif self.state == "COMBAT":
            if self.stage < 2:
                self.stage += 1
                self.enter("CHOICE")
            else:
                self.enter("RESULT")
        elif self.state == "RESULT":
            self.enter("TITLE")

    def tick(self, dt, movement):
        if self.state not in ("COMBAT", "TUTORIAL"):
            return
        self.invulnerable = max(0, self.invulnerable-dt)
        self.skill_cooldown = max(0, self.skill_cooldown-dt)
        self.skill_flash = max(0, self.skill_flash-dt)
        self.damage_flash = max(0, self.damage_flash-dt)
        dx, dy = movement
        length = math.hypot(dx, dy)
        if length:
            self.player.x += dx / length * 300 * dt
            self.player.y += dy / length * 300 * dt
        left, right, bottom, top = FIELD
        self.player.x = max(left+30, min(right-30, self.player.x))
        self.player.y = max(bottom+30, min(top-40, self.player.y))
        self.shot_in -= dt
        if self.shot_in <= 0:
            self.shot_in += 0.25
            if len(self.player_bullets) < MAX_PLAYER_BULLETS:
                self.player_bullets.append(Entity(next(self.ids), "player_bullet", self.player.x,
                                                 self.player.y+32, 5, vy=700,
                                                 damage=self.session.damage, ttl=3))
        if self.state == "COMBAT":
            while self.event_index < len(self.events) and self.events[self.event_index][0] <= self.elapsed+1e-9:
                _, kind, count = self.events[self.event_index]
                for _ in range(count):
                    self.spawn_enemy(kind)
                self.event_index += 1
            if self.stage == 2 and self.session.boss_defeated:
                self.reinforcement_in -= dt
                if self.reinforcement_in <= 0:
                    self.spawn_enemy("bot")
                    self.reinforcement_in += 4
        elif int(self.elapsed / 4) != int((self.elapsed+dt) / 4):
            self.spawn_enemy("bot")

        for e in self.enemies[:]:
            e.age += dt
            if e.kind == "boss":
                e.x = 780 + math.sin(e.age*0.45)*340
                e.y = 795 + math.sin(e.age*0.8)*20
            else:
                e.x += e.vx*dt
                e.y += e.vy*dt
            e.fire_in -= dt
            if e.fire_in <= 0:
                self.fire_enemy(e)
                e.fire_in += 1.5 if e.kind == "bot" else 2.0 if e.kind == "drone" else 1.8
            if e.y < bottom-60 or e.x < left-100 or e.x > right+100 or e.age > e.ttl:
                self.enemies.remove(e)
        for bullets in (self.player_bullets, self.enemy_bullets):
            for b in bullets[:]:
                b.x += b.vx*dt
                b.y += b.vy*dt
                b.age += dt
                if b.age > b.ttl or b.x < left-50 or b.x > right+50 or b.y < bottom-60 or b.y > top+100:
                    bullets.remove(b)
        self.collisions()

    def spawn_enemy(self, kind):
        if len(self.enemies) >= MAX_ENEMIES:
            return
        left, right, _, top = FIELD
        hp = {"bot": 3, "drone": 5, "swarm": 2, "boss": 100}[kind]
        x, y = self.rng.uniform(left+100, right-100), top-20
        vx, vy, radius = 0, -42, 25
        if kind == "drone":
            vy, radius = -32, 31
        elif kind == "swarm":
            side = self.rng.choice((-1, 0, 1))
            if side:
                x, y = (left+20 if side < 0 else right-20), self.rng.uniform(580, 830)
                vx, vy = -side*75, -36
            else:
                vy = -85
            radius = 21
        elif kind == "boss":
            x, y, radius, vy = 780, 795, 95, 0
        if math.hypot(x-self.player.x, y-self.player.y) < 150:
            x = right-100 if self.player.x < 780 else left+100
        self.enemies.append(Entity(next(self.ids), kind, x, y, radius, vx, vy, hp,
                                   fire_in=1.0, ttl=60 if kind == "boss" else 25))

    def fire_enemy(self, e):
        angle = math.atan2(self.player.y-e.y, self.player.x-e.x)
        kind, speed = "round", 170
        angles = [angle]
        if e.kind == "drone":
            angles = [angle + math.radians(v) for v in (-30, -15, 0, 15, 30)]
            kind, speed = "wedge", 150
        elif e.kind == "swarm":
            speed = 160
        elif e.kind == "boss":
            if e.age % 8 < 0.6:
                return
            pattern = int(e.age/8) % 3
            if pattern == 0:
                angles = [angle-0.12, angle, angle+0.12]
            elif pattern == 1:
                angles = [angle + math.radians(v) for v in range(-45, 46, 15)]
                kind = "wedge"
            else:
                angles = [math.tau*i/12 + e.age*0.2 for i in range(12)]
            speed = 180
        for a in angles:
            if len(self.enemy_bullets) >= MAX_ENEMY_BULLETS:
                break
            self.enemy_bullets.append(Entity(next(self.ids), kind, e.x, e.y-15, 8,
                                             math.cos(a)*speed, math.sin(a)*speed, ttl=12))

    def collisions(self):
        for b in self.player_bullets[:]:
            for e in self.enemies[:]:
                if overlaps(b, e):
                    self.player_bullets.remove(b)
                    e.hp -= b.damage
                    if e.hp <= 0:
                        self.defeat(e)
                    break
        for b in self.enemy_bullets[:]:
            # Membership matters only on contact: a revival may clear other bullets.
            if overlaps(self.player, b) and b in self.enemy_bullets:
                self.enemy_bullets.remove(b)
                self.hurt()
        for e in self.enemies:
            if overlaps(self.player, e):
                self.hurt()

    def defeat(self, enemy):
        if enemy not in self.enemies:
            return
        self.enemies.remove(enemy)
        if self.state != "COMBAT":
            return
        if enemy.kind == "boss":
            if not self.session.boss_defeated:
                self.session.boss_defeated = True
                self.session.add_score(500)
                self.enemy_bullets.clear()
        else:
            self.session.enemy_kills += 1
            self.session.add_score(50)

    def hurt(self):
        if self.state not in ("COMBAT", "TUTORIAL") or self.invulnerable > 0:
            return
        self.damage_flash = 0.25
        self.invulnerable = 1.0
        if self.session.shield:
            self.session.shield -= 1
        else:
            self.session.hp -= 1
            if self.session.hp <= 0:
                self.session.hp = 3
                if self.state == "COMBAT":
                    self.session.revive_count += 1
                    self.session.add_score(-100)
                self.player.x, self.player.y = PLAYER_START
                self.invulnerable = 2.0
                self.clear_nearby(140)

    def clear_nearby(self, radius):
        self.enemy_bullets[:] = [b for b in self.enemy_bullets
                                if math.hypot(b.x-self.player.x, b.y-self.player.y) > radius]

    def skill(self):
        if self.state not in ("COMBAT", "TUTORIAL") or self.session.skills <= 0 or self.skill_cooldown > 0:
            return False
        self.session.skills -= 1
        self.skill_cooldown = 0.3
        self.skill_flash = 0.45
        self.skill_center = (self.player.x, self.player.y)
        self.clear_nearby(180)
        return True
