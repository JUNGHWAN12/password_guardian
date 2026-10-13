"""Deterministic simulation. No graphics or filesystem side effects."""
from collections import deque
from dataclasses import dataclass
import itertools
import math
import random

from .config import (FIELD, PLAYER_START, STEP, PLAYER_SPEED, PRECISE_SPEED, PLAYER_HIT_RADIUS, TUTORIAL_SECONDS, CHOICE_SECONDS,
                     ANSWER_SECONDS, COMBAT_SECONDS, RESULT_SECONDS,
                     MAX_ENEMIES, MAX_ENEMY_BULLETS, MAX_PLAYER_BULLETS)
from .content import load_content
from .session import Session

# kind: (hp, hit radius, entry speed, seconds between attacks)
ENEMY_STATS = {"bot": (2, 25, -55, 1.5), "drone": (4, 31, -36, 2.0), "swarm": (2, 21, -85, 1.8),
               "boss": (400, 95, 0, 1.8), "phish": (3, 22, -40, 1.6), "keylogger": (3, 24, -35, 1.4),
               "mfa": (5, 30, -60, 3.0), "sprayer": (6, 28, -60, 4.0),
               "surfer": (4, 30, -60, math.inf), "gift": (6, 30, -35, math.inf)}
HOLD = {"mfa": (760, 14), "sprayer": (870, 16), "surfer": (820, 16)}  # stop at this height, leave upward after these seconds
PHISH_REVEAL = 1.2  # seconds a phishing lure looks like a guardian before its mask drops
KEYLOGGER_DELAY = 1.2  # a keylogger shoots where the player was this long ago
SIGHT_HALF, SIGHT_SWING, SIGHT_PERIOD = math.radians(15), math.radians(40), 4.0  # shoulder surfer's view cone
SIGHT_STARE, SIGHT_BLINK = 0.8, 0.3  # seconds in view before the lens blinks, then the shot
# weapon level: (x offset, degrees off straight up) per shot; level 4 adds two homing locks every other volley
WEAPON_PATTERNS = {1: [(0, 0)], 2: [(-11, 0), (11, 0)], 3: [(-11, 0), (11, 0), (-18, -12), (18, 12)],
                   4: [(-16, 0), (0, 0), (16, 0), (-20, -12), (20, 12)]}
HOMING_TURN = 5.0  # rad/s
FORMATION_GAP = 75  # px between ships in a line or V
# Every DROP_EVERY-th defeat drops the next item of DROP_CYCLE, so drops never depend on luck.
DROP_EVERY = 3
DROP_CYCLE = ("patch", "badge", "backup", "patch", "badge", "vaccine", "badge", "firewall")
BOSS_DROPS = ("patch", "backup", "vaccine")
ITEM_FALL, ITEM_PULL, ITEM_PULL_LINE, ITEM_MAGNET = -110, 900, 720, 90  # px/s, px/s, auto-collect height, px
FIREWALL_SECONDS, SHIELD_MAX = 5.0, 3
# what each item says when picked up; the habit behind it is the point
ITEM_NOTICES = {"patch": "패치 업데이트 · 무기 강화", "backup": "백업 완료 · 보호막 +1", "vaccine": "백신 실행 · 방어 스킬 +1",
                "badge": "보안 배지 +100", "firewall": "방화벽 가동 · 적 탄 감속", "bonus": "이미 최대 · +100"}
GIFT_OPEN_Y, GIFT_OPEN_AGE = 560, 6.0  # a trojan gift opens at this height or age unless destroyed first


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
    burst: int = 0  # shots left in a burst or sweep
    burst_in: float = 0
    aim: float = 0
    spin: int = 1
    watch: float = 0  # seconds the player has stayed in a shoulder surfer's view
    warn: float = 0  # lens blink before its shot


def overlaps(a, b):
    return (a.x-b.x)**2 + (a.y-b.y)**2 <= (a.radius+b.radius)**2


class Engine:
    def __init__(self, seed=None, practice=False):
        self.questions, self.wave_specs, self.intros = load_content()
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
        self.player = Entity(0, "player", *PLAYER_START, PLAYER_HIT_RADIUS)
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.items = []
        self.notices = []  # (text key, x, y, seconds left) for pickup captions
        self.drops = 0
        self.firewall = 0.0
        self.invulnerable = 0.0
        self.shot_in = 0.0
        self.skill_cooldown = 0.0
        self.skill_flash = 0.0
        self.damage_flash = 0.0
        self.skill_center = PLAYER_START
        self.volley = 0
        self.precise = False
        self.reinforcement_in = 4.0
        self.clock = 0.0
        self.trail = deque()  # recent player positions for keyloggers

    def start(self):
        if self.state != "TITLE":
            return
        self.session = Session()
        self.result = None
        self.stage = 0
        self.reset_arena()
        self.enter("TUTORIAL")

    def clear_field(self):
        self.enemies.clear()
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.items.clear()
        self.notices.clear()
        self.firewall = 0

    def reset_arena(self):
        self.clear_field()
        self.drops = 0
        self.player.x, self.player.y = PLAYER_START
        self.invulnerable = 0
        self.shot_in = 0
        self.skill_cooldown = 0
        self.skill_flash = 0
        self.damage_flash = 0
        self.trail.clear()

    def enter(self, state):
        self.state = state
        self.elapsed = 0.0
        self.revision += 1
        if state == "CHOICE":
            self.clear_field()
            self.trail.clear()
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
                    self.events.append((t, spec["kinds"][i % len(spec["kinds"])], spec["count"],
                                        spec.get("formation", "scatter")))
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

    def update(self, dt, movement=(0, 0), precise=False):
        if dt < 0 or not math.isfinite(dt):
            raise ValueError("delta_time must be finite and nonnegative")
        while dt > 1e-9 and self.state != "TITLE":
            step = min(STEP, dt, self.remaining)
            if step > 1e-9:
                self.tick(step, movement, precise)
                self.elapsed += step
                dt -= step
            if self.state == "CHOICE" and self.elapsed >= ANSWER_SECONDS-1e-9:
                self.session.choose(self.stage, None, self.questions[self.stage]["correct"])
            if self.remaining < 1e-8:
                self.advance()
                movement, precise = (0, 0), False  # held keys never carry through a stage boundary

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

    def tick(self, dt, movement, precise=False):
        if self.state not in ("COMBAT", "TUTORIAL"):
            return
        self.invulnerable = max(0, self.invulnerable-dt)
        self.skill_cooldown = max(0, self.skill_cooldown-dt)
        self.skill_flash = max(0, self.skill_flash-dt)
        self.damage_flash = max(0, self.damage_flash-dt)
        self.precise = precise
        dx, dy = movement
        length = math.hypot(dx, dy)
        if length:
            speed = PRECISE_SPEED if precise else PLAYER_SPEED
            self.player.x += dx / length * speed * dt
            self.player.y += dy / length * speed * dt
        left, right, bottom, top = FIELD
        self.player.x = max(left+30, min(right-30, self.player.x))
        self.player.y = max(bottom+30, min(top-40, self.player.y))
        self.clock += dt
        self.trail.append((self.clock, self.player.x, self.player.y))
        while self.trail[0][0] < self.clock - 2*KEYLOGGER_DELAY:
            self.trail.popleft()
        self.shot_in -= dt
        if self.shot_in <= 0:
            self.shot_in += 0.25
            self.fire_player()
        if self.state == "COMBAT":
            while self.event_index < len(self.events) and self.events[self.event_index][0] <= self.elapsed+1e-9:
                _, kind, count, formation = self.events[self.event_index]
                self.spawn_group(kind, count, formation)
                self.event_index += 1
            if self.stage == 2 and self.session.boss_defeated:
                self.reinforcement_in -= dt
                if self.reinforcement_in <= 0:
                    self.spawn_enemy("mfa")
                    self.reinforcement_in += 8
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
            if e.kind == "gift" and (e.y <= GIFT_OPEN_Y or e.age >= GIFT_OPEN_AGE):
                self.open_gift(e)
                continue
            leaving = False
            if e.kind in HOLD:
                hold_y, stay = HOLD[e.kind]
                if e.vy < 0 and e.y <= hold_y:
                    e.y, e.vy = hold_y, 0
                if e.age > stay:
                    e.vy, e.burst = 90, 0  # done; withdraw upward without firing
                leaving = e.vy > 0
            if e.kind == "surfer" and e.vy == 0:
                self.watch(e, dt)
            if not leaving:
                e.fire_in -= dt
                if e.fire_in <= 0:
                    self.fire_enemy(e)
                    e.fire_in += ENEMY_STATS[e.kind][3]
                e.burst_in -= dt
                while e.burst > 0 and e.burst_in <= 0:
                    self.burst_shot(e)
                    e.burst_in += 0.18 if e.kind == "mfa" else 0.12
            if (e.y < bottom-60 or e.y > top+140 or e.x < left-100 or e.x > right+100
                    or e.age > e.ttl):
                self.enemies.remove(e)
        self.firewall = max(0, self.firewall-dt)
        self.move_items(dt)
        for bullets in (self.player_bullets, self.enemy_bullets):
            slow = 0.5 if bullets is self.enemy_bullets and self.firewall else 1
            for b in bullets[:]:
                if b.kind == "player_homing":
                    self.steer(b, dt)
                b.x += b.vx*dt*slow
                b.y += b.vy*dt*slow
                b.age += dt
                if b.age > b.ttl or b.x < left-50 or b.x > right+50 or b.y < bottom-60 or b.y > top+100:
                    bullets.remove(b)
        self.collisions()

    def spawn_group(self, kind, count, formation):
        left, right, _, top = FIELD
        if formation == "scatter":
            for _ in range(count):
                self.spawn_enemy(kind)
            return
        gap = FORMATION_GAP
        center = self.rng.uniform(left + 100 + gap*(count-1)/2, right - 100 - gap*(count-1)/2)
        for i in range(count):
            before = len(self.enemies)
            offset = i - (count-1)/2
            if formation == "line":
                self.spawn_enemy(kind, (center + offset*gap, top-20))
            elif formation == "v":  # the leader comes first, wings trail behind
                self.spawn_enemy(kind, (center + offset*gap, top-20 + abs(offset)*45))
            else:  # "sides": alternate edges, sliding inward
                side = -1 if i % 2 == 0 else 1
                x = left+20 if side < 0 else right-20
                self.spawn_enemy(kind, (x, 820 - (i//2)*70), (-side*80, -40))
            if len(self.enemies) > before and math.isfinite(self.enemies[-1].fire_in):
                self.enemies[-1].fire_in += 0.2*i  # a ripple, not one wall of bullets

    def spawn_enemy(self, kind, at=None, velocity=None):
        if len(self.enemies) >= MAX_ENEMIES:
            return
        left, right, _, top = FIELD
        hp, radius, vy, _ = ENEMY_STATS[kind]
        x, y = self.rng.uniform(left+100, right-100), top-20
        vx, fire_in = 0, 1.0
        if kind == "swarm":
            side = self.rng.choice((-1, 0, 1))
            if side:
                x, y = (left+20 if side < 0 else right-20), self.rng.uniform(580, 830)
                vx, vy = -side*75, -36
        elif kind == "boss":
            x, y = 780, 795
        elif kind == "phish":
            fire_in = PHISH_REVEAL + 0.3  # the reveal flash is the warning
        elif kind in HOLD:
            x, y = self.rng.uniform(left+150, right-150), top+60  # glide in from above, then hold
            fire_in = (y - HOLD[kind][0]) / -vy + 0.3
        if at is not None:
            x, y = at
        if velocity is not None:
            vx, vy = velocity
        if ENEMY_STATS[kind][3] == math.inf:
            fire_in = math.inf  # attacks on its own terms (view cone, opening), never on a timer
        if math.hypot(x-self.player.x, y-self.player.y) < 150:
            x = right-100 if self.player.x < 780 else left+100
        self.enemies.append(Entity(next(self.ids), kind, x, y, radius, vx, vy, hp,
                                   fire_in=fire_in, ttl=60 if kind == "boss" else 25,
                                   spin=self.rng.choice((-1, 1)) if kind == "sprayer" else 1))

    def fire_player(self):
        self.volley += 1
        shots = [(dx, math.radians(deg), "player_bullet", 700) for dx, deg in WEAPON_PATTERNS[self.session.weapon]]
        if self.session.weapon >= 4 and self.volley % 2:
            shots += [(-24, math.radians(-35), "player_homing", 520), (24, math.radians(35), "player_homing", 520)]
        for dx, tilt, kind, speed in shots:
            if len(self.player_bullets) < MAX_PLAYER_BULLETS:
                self.player_bullets.append(Entity(next(self.ids), kind, self.player.x+dx, self.player.y+32, 5,
                                                  math.sin(tilt)*speed, math.cos(tilt)*speed,
                                                  damage=self.session.damage, ttl=3))

    def steer(self, b, dt):
        target = min(self.enemies, key=lambda e: (e.x-b.x)**2 + (e.y-b.y)**2, default=None)
        if target is None:
            return
        heading, speed = math.atan2(b.vy, b.vx), math.hypot(b.vx, b.vy)
        turn = (math.atan2(target.y-b.y, target.x-b.x) - heading + math.pi) % math.tau - math.pi
        heading += max(-HOMING_TURN*dt, min(HOMING_TURN*dt, turn))
        b.vx, b.vy = math.cos(heading)*speed, math.sin(heading)*speed

    def watch(self, e, dt):
        e.aim = -math.pi/2 + SIGHT_SWING*math.sin(math.tau*e.age/SIGHT_PERIOD)
        if e.warn > 0:
            e.warn -= dt
            if e.warn <= 0:
                self.shoot(e, "peek", math.atan2(self.player.y-e.y, self.player.x-e.x), 260)
            return
        to_player = math.atan2(self.player.y-e.y, self.player.x-e.x)
        seen = abs((to_player - e.aim + math.pi) % math.tau - math.pi) <= SIGHT_HALF
        e.watch = e.watch + dt if seen else 0
        if e.watch >= SIGHT_STARE:
            e.watch, e.warn = 0, SIGHT_BLINK

    def open_gift(self, e):
        self.enemies.remove(e)
        hp, radius, vy, _ = ENEMY_STATS["swarm"]
        for vx in (-70, 0, 70):
            if len(self.enemies) < MAX_ENEMIES:
                self.enemies.append(Entity(next(self.ids), "swarm", e.x + vx/2, e.y, radius, vx, vy, hp, ttl=25))
        for k in range(8):
            self.shoot(e, "leak", math.tau*k/8 + math.pi/8, 160)

    def fire_enemy(self, e):
        angle = math.atan2(self.player.y-e.y, self.player.x-e.x)
        kind, speed = "guess", 170
        angles = [angle]
        if e.kind == "mfa":  # a burst of login-approval prompts
            e.burst, e.burst_in, e.aim = 8, 0, angle
            return
        if e.kind == "sprayer":  # one common password swept across many accounts
            e.spin = -e.spin
            e.burst, e.burst_in, e.aim = 13, 0, -math.pi/2 - e.spin*math.radians(60)
            return
        if e.kind == "phish":
            kind, speed = "hook", 190
        elif e.kind == "keylogger":
            past = next((p for p in reversed(self.trail) if p[0] <= self.clock - KEYLOGGER_DELAY),
                        self.trail[0] if self.trail else (0, self.player.x, self.player.y))
            angles = [math.atan2(past[2]-e.y, past[1]-e.x)]
            kind, speed = "keycap", 200
        elif e.kind == "drone":
            angles = [angle + math.radians(v) for v in (-30, -15, 0, 15, 30)]
            kind, speed = "dict", 150
        elif e.kind == "swarm":
            kind, speed = "leak", 160
        elif e.kind == "boss":
            if e.age % 8 < 0.6:
                return
            pattern = int(e.age/8) % 3
            if pattern == 0:
                angles = [angle-0.12, angle, angle+0.12]
            elif pattern == 1:
                angles = [angle + math.radians(v) for v in range(-45, 46, 15)]
                kind = "dict"
            else:
                angles = [math.tau*i/12 + e.age*0.2 for i in range(12)]
                kind = "leak"
            speed = 180
        for a in angles:
            self.shoot(e, kind, a, speed)

    def burst_shot(self, e):
        if e.kind == "mfa":
            k = 8 - e.burst
            self.shoot(e, "bell", e.aim + math.radians(-20 + 40*k/7), 140)
        else:
            k = 13 - e.burst
            self.shoot(e, "guess", e.aim + e.spin*math.radians(120)*k/12, 160)
        e.burst -= 1

    def shoot(self, e, kind, angle, speed):
        if len(self.enemy_bullets) < MAX_ENEMY_BULLETS:
            self.enemy_bullets.append(Entity(next(self.ids), kind, e.x, e.y-15, 8,
                                             math.cos(angle)*speed, math.sin(angle)*speed, ttl=12))

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
                for i, kind in enumerate(BOSS_DROPS):
                    self.drop(kind, enemy.x + (i-1)*60, enemy.y)
        else:
            self.session.enemy_kills += 1
            self.session.add_score(50)
            if self.session.enemy_kills % DROP_EVERY == 0:
                self.drop(DROP_CYCLE[self.drops % len(DROP_CYCLE)], enemy.x, enemy.y)
                self.drops += 1

    def drop(self, kind, x, y):
        self.items.append(Entity(next(self.ids), kind, x, y, 22, vy=ITEM_FALL, ttl=12))

    def move_items(self, dt):
        for n in self.notices[:]:
            n[3] -= dt
            n[2] += 40*dt
            if n[3] <= 0:
                self.notices.remove(n)
        bottom = FIELD[2]
        pull = self.player.y >= ITEM_PULL_LINE
        for item in self.items[:]:
            item.age += dt
            dx, dy = self.player.x-item.x, self.player.y-item.y
            dist = math.hypot(dx, dy)
            if pull or dist < ITEM_MAGNET:
                step = min(dist, ITEM_PULL*dt)
                if dist:
                    item.x += dx/dist*step
                    item.y += dy/dist*step
            else:
                item.y += item.vy*dt
            if math.hypot(self.player.x-item.x, self.player.y-item.y) <= item.radius + 18:
                self.items.remove(item)
                self.collect(item)
            elif item.y < bottom-40 or item.age > item.ttl:
                self.items.remove(item)

    def collect(self, item):
        s, kind = self.session, item.kind
        if kind == "patch" and not s.power_up():
            kind = "bonus"
        elif kind == "backup":
            if s.shield < SHIELD_MAX:
                s.shield += 1
            else:
                kind = "bonus"
        elif kind == "vaccine":
            s.skills += 1
        elif kind == "firewall":
            self.firewall = FIREWALL_SECONDS
        if kind in ("badge", "bonus"):
            s.add_score(100)
        self.notices.append([kind, item.x, item.y + 30 + 30*len(self.notices), 1.2])  # stack, never overlap

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
