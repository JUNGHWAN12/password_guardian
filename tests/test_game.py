from collections import Counter
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from password_guardian.config import (FIELD, PLAYER_START, STEP, PLAYER_SPEED, PRECISE_SPEED, PLAYER_HIT_RADIUS,
                                      MAX_ENEMIES, MAX_ENEMY_BULLETS)
from password_guardian.engine import (Engine, Entity, KEYLOGGER_DELAY, PHISH_REVEAL, DROP_CYCLE, FIREWALL_SECONDS,
                                      SHIELD_MAX, overlaps)
from password_guardian.session import Session, grade_for


class TimelineTests(unittest.TestCase):
    def test_full_240_second_session_without_input(self):
        engine = Engine(seed=12)
        engine.start()
        for delta, state, stage in [(20, "CHOICE", 0), (8, "COMBAT", 0),
                                    (52, "CHOICE", 1), (8, "COMBAT", 1),
                                    (52, "CHOICE", 2), (8, "COMBAT", 2),
                                    (52, "RESULT", 2)]:
            engine.update(delta)
            self.assertEqual((engine.state, engine.stage), (state, stage))
        self.assertIsNotNone(engine.result)
        self.assertTrue(all(c.selection is None for c in engine.result.choices))
        engine.update(40)
        self.assertEqual(engine.state, "TITLE")

    def test_large_update_carries_remainder_and_runs_events_once(self):
        engine = Engine(seed=1)
        engine.start()
        engine.update(29.25)
        self.assertEqual(engine.state, "COMBAT")
        self.assertAlmostEqual(engine.elapsed, 1.25, places=6)
        self.assertEqual(engine.event_index, 1)
        self.assertEqual(len(engine.enemies) + engine.session.enemy_kills, 3)  # the opening line of three

    def test_choice_early_answer_waits_for_fixed_boundary(self):
        engine = Engine()
        engine.start()
        engine.update(20)
        self.assertTrue(engine.choose(2))
        self.assertFalse(engine.choose(1))
        engine.update(7.5)
        self.assertEqual(engine.state, "CHOICE")
        self.assertEqual(engine.session.score, 200)
        engine.update(0.5)
        self.assertEqual(engine.state, "COMBAT")

    def test_timeout_records_missing_not_wrong_choice(self):
        engine = Engine()
        engine.start()
        engine.update(26)
        self.assertIsNone(engine.session.choices[0].selection)
        self.assertFalse(engine.choose(2))
        self.assertEqual(engine.session.score, 0)

    def test_tutorial_consumables_do_not_leak(self):
        engine = Engine()
        engine.start()
        engine.skill()
        engine.session.hp = 1
        engine.update(20)
        self.assertEqual((engine.session.hp, engine.session.skills), (3, 3))

    def test_new_session_resets_all_rewards_and_id(self):
        engine = Engine(seed=2)
        engine.start()
        engine.update(20)
        engine.choose(2)
        first_id = engine.session.session_id
        engine.update(220)
        engine.start()
        self.assertNotEqual(engine.session.session_id, first_id)
        self.assertEqual((engine.session.score, engine.session.shield, engine.session.skills), (0, 0, 3))
        self.assertIsNone(engine.result)

    def test_result_is_frozen_and_no_postgame_rewards(self):
        engine = Engine(seed=5)
        engine.start()
        engine.update(200)
        result = engine.result
        engine.session.add_score(5000)
        engine.choose(2)
        engine.hurt()
        self.assertEqual(engine.session.score, result.score)
        self.assertIs(engine.result, result)

    def test_boss_never_spawns_on_player(self):
        engine = Engine(seed=3)
        engine.start()
        engine.update(139.99)
        engine.player.x, engine.player.y = 780, FIELD[3]-40  # top centre, inside the boss path
        engine.update(0.02)
        self.assertEqual((engine.state, engine.stage), ("CHOICE", 2))
        self.assertEqual((engine.player.x, engine.player.y), PLAYER_START)
        engine.session.hp, engine.session.shield, engine.invulnerable = 3, 0, 0
        engine.update(8)
        boss = next(e for e in engine.enemies if e.kind == "boss")
        self.assertFalse(overlaps(engine.player, boss))
        self.assertEqual(engine.session.hp, 3)

    def test_invalid_delta_rejected(self):
        for delta in (-1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                Engine().update(delta)


class CombatTests(unittest.TestCase):
    def combat(self):
        engine = Engine(seed=8)
        engine.state = "COMBAT"
        engine.events = []
        return engine

    def test_normalized_diagonal_and_field_clamp(self):
        a, b = self.combat(), self.combat()
        a.update(0.5, (1, 0))
        b.update(0.5, (1, 1))
        self.assertAlmostEqual(math.dist(PLAYER_START, (a.player.x, a.player.y)),
                               math.dist(PLAYER_START, (b.player.x, b.player.y)))
        a.update(10, (1, 1))
        self.assertLessEqual(a.player.x, FIELD[1]-30)
        self.assertLessEqual(a.player.y, FIELD[3]-40)

    def test_auto_fire_and_damage_upgrade(self):
        engine = self.combat()
        engine.session.choose(1, 2)
        engine.update(0.76)
        self.assertEqual(len(engine.player_bullets), 4)
        self.assertTrue(all(b.damage == 2 for b in engine.player_bullets))

    def test_shield_then_health_and_invulnerability(self):
        engine = self.combat()
        engine.session.shield = 1
        engine.hurt()
        engine.hurt()
        self.assertEqual((engine.session.shield, engine.session.hp), (0, 3))
        engine.update(1.01)
        engine.hurt()
        self.assertEqual(engine.session.hp, 2)

    def test_revive_preserves_upgrades_and_score_floor(self):
        engine = self.combat()
        engine.session.hp = 1
        engine.session.score = 50
        engine.session.damage = 2
        engine.session.skills = 1
        engine.enemy_bullets = [Entity(99, "guess", *PLAYER_START, 8)]
        engine.hurt()
        self.assertEqual((engine.session.score, engine.session.hp, engine.session.damage, engine.session.skills), (0, 3, 2, 1))
        self.assertEqual(engine.session.revive_count, 1)
        self.assertEqual(engine.invulnerable, 2)
        self.assertEqual(len(engine.enemy_bullets), 0)

    def test_skill_radius_cooldown_and_exhaustion(self):
        engine = self.combat()
        x, y = PLAYER_START
        engine.enemy_bullets = [Entity(1, "guess", x+100, y, 8), Entity(2, "guess", x+200, y, 8)]
        self.assertTrue(engine.skill())
        self.assertEqual([b.id for b in engine.enemy_bullets], [2])
        self.assertFalse(engine.skill())
        engine.session.skills = 0
        engine.skill_cooldown = 0
        self.assertFalse(engine.skill())

    def test_non_piercing_shot_and_single_kill_reward(self):
        engine = self.combat()
        engine.enemies = [Entity(1, "bot", 500, 500, 25), Entity(2, "bot", 500, 500, 25)]
        dead = engine.enemies[0]
        engine.player_bullets = [Entity(3, "player_bullet", 500, 500, 5)]
        engine.collisions()
        engine.defeat(dead)
        self.assertEqual((engine.session.score, engine.session.enemy_kills, len(engine.enemies)), (50, 1, 1))

    def test_boss_reward_is_not_normal_enemy_reward(self):
        engine = self.combat()
        engine.spawn_enemy("boss")
        boss = engine.enemies[0]
        engine.defeat(boss)
        engine.defeat(boss)
        self.assertEqual(engine.session.score, 500)
        self.assertEqual(engine.session.enemy_kills, 0)
        self.assertTrue(engine.session.boss_defeated)
        self.assertEqual(engine.state, "COMBAT")

    def test_spawn_and_bullet_caps(self):
        engine = self.combat()
        for _ in range(50):
            engine.spawn_enemy("drone")
        self.assertEqual(len(engine.enemies), MAX_ENEMIES)
        for _ in range(100):
            engine.fire_enemy(engine.enemies[0])
        self.assertEqual(len(engine.enemy_bullets), MAX_ENEMY_BULLETS)

    def test_shift_switches_to_precise_speed(self):
        engine = self.combat()
        engine.update(0.5, (1, 0))
        self.assertAlmostEqual(engine.player.x, PLAYER_START[0] + PLAYER_SPEED*0.5)
        engine.update(0.5, (-1, 0), precise=True)
        self.assertAlmostEqual(engine.player.x, PLAYER_START[0] + (PLAYER_SPEED-PRECISE_SPEED)*0.5)
        self.assertTrue(engine.precise)
        self.assertEqual(engine.player.radius, PLAYER_HIT_RADIUS)

    def test_weapon_levels_widen_the_volley(self):
        engine = self.combat()
        counts = []
        for level in range(1, 5):
            engine.session.weapon = level
            engine.player_bullets.clear()
            engine.volley = 1  # the next volley is even: no homing locks
            engine.fire_player()
            counts.append(len(engine.player_bullets))
        self.assertEqual(counts, [1, 2, 4, 5])
        engine.player_bullets.clear()
        engine.fire_player()
        self.assertEqual([b.kind for b in engine.player_bullets].count("player_homing"), 2)

    def test_power_up_caps_and_survives_hits(self):
        engine = self.combat()
        self.assertEqual([engine.session.power_up() for _ in range(4)], [True, True, True, False])
        engine.hurt()
        engine.invulnerable = 0
        engine.hurt(); engine.invulnerable = 0
        engine.hurt()  # revive
        self.assertEqual((engine.session.revive_count, engine.session.weapon), (1, 4))

    def test_homing_lock_turns_toward_the_nearest_enemy(self):
        engine = self.combat()
        engine.shot_in = 1e9
        engine.spawn_enemy("drone")
        drone = engine.enemies[0]
        drone.x, drone.y, drone.vy, drone.fire_in = 300, 700, 0, 1e9
        lock = Entity(99, "player_homing", 780, 300, 5, 0, 520, ttl=3)
        engine.player_bullets.append(lock)
        engine.update(0.3)
        self.assertLess(lock.vx, 0)  # bending left toward the drone
        self.assertAlmostEqual(math.hypot(lock.vx, lock.vy), 520)

    def test_choice_freezes_combat(self):
        engine = self.combat()
        engine.spawn_enemy("bot")
        enemy = engine.enemies[0]
        engine.state = "CHOICE"
        before = (enemy.x, enemy.y, enemy.fire_in)
        engine.update(1, (1, 1))
        self.assertEqual((enemy.x, enemy.y, enemy.fire_in), before)
        self.assertEqual((engine.player.x, engine.player.y), PLAYER_START)


class AttackTests(unittest.TestCase):
    def combat(self):
        engine = Engine(seed=8)
        engine.state = "COMBAT"
        engine.events = []
        engine.shot_in = 1e9  # keep the guardian from shooting the attacker under test
        return engine

    def test_phishing_lure_waits_until_unmasked(self):
        engine = self.combat()
        engine.spawn_enemy("phish")
        engine.update(PHISH_REVEAL + 0.25)
        self.assertEqual(engine.enemy_bullets, [])
        engine.update(0.1)
        self.assertEqual([b.kind for b in engine.enemy_bullets], ["hook"])

    def test_alert_bomber_holds_bursts_eight_and_leaves(self):
        engine = self.combat()
        engine.spawn_enemy("mfa")
        bomber = engine.enemies[0]
        engine.update(3.7)  # 210 px glide at 60 px/s, then 0.3 s of warning
        self.assertEqual((bomber.y, len(engine.enemy_bullets)), (760, 0))
        engine.update(1.4)
        self.assertEqual([b.kind for b in engine.enemy_bullets], ["bell"] * 8)
        engine.update(15)
        self.assertNotIn(bomber, engine.enemies)  # withdrew upward after its stay

    def test_sprayer_sweeps_thirteen_shots_then_rests(self):
        engine = self.combat()
        engine.spawn_enemy("sprayer")
        sprayer = engine.enemies[0]
        engine.update(1.9)
        self.assertEqual((sprayer.y, len(engine.enemy_bullets)), (870, 0))
        engine.update(1.6)
        angles = [math.atan2(b.vy, b.vx) for b in engine.enemy_bullets]
        self.assertEqual(len(angles), 13)
        self.assertAlmostEqual(abs(angles[-1]-angles[0]), math.radians(120), places=5)
        self.assertTrue(all(b.vy < 0 and b.kind == "guess" for b in engine.enemy_bullets))
        engine.update(2.0)
        self.assertEqual(sprayer.burst, 0)
        self.assertGreater(sprayer.fire_in, 0)

    def test_keylogger_shoots_where_the_player_was(self):
        engine = self.combat()
        engine.spawn_enemy("keylogger")
        logger = engine.enemies[0]
        logger.x, logger.y, logger.vy = 780, 800, 0
        engine.update(0.5, (1, 0), precise=True)   # creep right to x=900
        engine.update(1.4)                          # wait there
        engine.update(0.55, (-1, 0), precise=True)  # creep back left; the 2.4 s shot uses the 1.2 s position
        self.assertLess(engine.player.x, 800)
        shot = engine.enemy_bullets[-1]
        expected = math.atan2(PLAYER_START[1]-800, 900-780)
        self.assertAlmostEqual(math.atan2(shot.vy, shot.vx), expected, places=2)
        self.assertEqual((len(engine.enemy_bullets), shot.kind), (2, "keycap"))
        self.assertEqual(KEYLOGGER_DELAY, 1.2)

    def test_new_attacks_join_each_stage_once(self):
        engine = Engine()
        for stage, expected in ((0, {"sprayer": 1, "keylogger": 1}), (1, {"phish": 2, "gift": 1, "surfer": 1}),
                                (2, {"mfa": 1, "surfer": 1})):
            engine.stage = stage
            engine.enter("COMBAT")
            counts = Counter(kind for _, kind, _, _ in engine.events)
            self.assertEqual({k: counts[k] for k in expected}, expected)
            self.assertTrue(all(kind in engine.intros or kind in ("bot", "drone", "swarm") for kind in counts))

    def test_shoulder_surfer_shoots_only_after_a_long_look(self):
        engine = self.combat()
        engine.spawn_enemy("surfer")
        surfer = engine.enemies[0]
        surfer.x, surfer.y, surfer.vy, surfer.age = 300, 820, 0, 0
        engine.player.x = 1400  # 61 degrees off straight down: beyond the 40 degree sweep plus the 15 degree half width
        engine.update(3.0)
        self.assertEqual(engine.enemy_bullets, [])
        surfer.age, surfer.ttl = 0, 1e9
        engine.player.x, engine.player.y = 780, 220
        for _ in range(240):  # keep the player under the lens whatever the sweep does
            engine.player.x = surfer.x + math.cos(surfer.aim)*600
            engine.player.y = max(140, surfer.y + math.sin(surfer.aim)*600)
            engine.update(STEP)
        self.assertEqual([b.kind for b in engine.enemy_bullets], ["peek"])
        self.assertAlmostEqual(math.hypot(engine.enemy_bullets[0].vx, engine.enemy_bullets[0].vy), 260)

    def test_trojan_gift_opens_unless_destroyed_first(self):
        engine = self.combat()
        engine.spawn_enemy("gift")
        gift = engine.enemies[0]
        engine.update(5.9)
        self.assertEqual((engine.enemies, engine.enemy_bullets), ([gift], []))
        engine.update(0.2)
        self.assertEqual(sorted(e.kind for e in engine.enemies), ["swarm"] * 3)
        self.assertEqual([b.kind for b in engine.enemy_bullets], ["leak"] * 8)

        engine = self.combat()
        engine.spawn_enemy("gift")
        engine.defeat(engine.enemies[0])
        engine.update(7)
        self.assertEqual((engine.enemies, engine.enemy_bullets, engine.session.score), ([], [], 50))

    def test_formations_place_ships_in_shape(self):
        engine = Engine(seed=3)
        engine.state = "COMBAT"
        engine.spawn_group("bot", 3, "line")
        line = engine.enemies[:]
        self.assertEqual({e.y for e in line}, {line[0].y})
        self.assertEqual([round(b.x-a.x) for a, b in zip(line, line[1:])], [75, 75])
        self.assertEqual([round(e.fire_in, 2) for e in line], [1.0, 1.2, 1.4])
        engine.enemies.clear()
        engine.spawn_group("bot", 5, "v")
        self.assertEqual(min(engine.enemies, key=lambda e: e.y).x, engine.enemies[2].x)  # leader in front
        engine.enemies.clear()
        engine.spawn_group("swarm", 4, "sides")
        self.assertEqual([e.vx > 0 for e in engine.enemies], [True, False, True, False])

    def test_alert_bombers_reinforce_after_the_boss(self):
        engine = self.combat()
        engine.stage = 2
        engine.session.boss_defeated = True
        engine.reinforcement_in = 0.05
        engine.update(0.1)
        self.assertEqual([e.kind for e in engine.enemies], ["mfa"])
        self.assertAlmostEqual(engine.reinforcement_in, 8 - 0.05, places=1)


class ItemTests(unittest.TestCase):
    def combat(self):
        engine = Engine(seed=8)
        engine.state = "COMBAT"
        engine.events = []
        engine.shot_in = 1e9
        return engine

    def kill(self, engine, n):
        for _ in range(n):
            engine.spawn_enemy("bot")
            enemy = engine.enemies[-1]
            enemy.x, enemy.y = 780, 600
            engine.defeat(enemy)

    def test_every_third_defeat_drops_the_next_item_in_order(self):
        engine = self.combat()
        self.kill(engine, 9)
        self.assertEqual([i.kind for i in engine.items], list(DROP_CYCLE[:3]))

    def test_items_are_collected_and_apply_their_effect(self):
        engine = self.combat()
        s = engine.session
        for kind in ("patch", "backup", "vaccine", "badge", "firewall"):
            engine.drop(kind, engine.player.x, engine.player.y+10)
        engine.update(STEP)
        self.assertEqual((engine.items, s.weapon, s.shield, s.skills, s.score), ([], 2, 1, 4, 100))
        self.assertEqual(engine.firewall, FIREWALL_SECONDS)
        self.assertEqual([n[0] for n in engine.notices], ["patch", "backup", "vaccine", "badge", "firewall"])

    def test_firewall_halves_enemy_bullet_speed(self):
        engine = self.combat()
        engine.enemy_bullets.append(Entity(50, "guess", 300, 800, 8, 0, -200, ttl=12))
        engine.firewall = 5
        engine.update(0.5)
        self.assertAlmostEqual(engine.enemy_bullets[0].y, 800 - 50)

    def test_items_fly_to_a_player_near_the_top(self):
        engine = self.combat()
        engine.drop("badge", 200, 500)
        engine.player.y = 800  # above the auto-collect line
        engine.update(1.0)
        self.assertEqual((engine.items, engine.session.score), ([], 100))

    def test_maxed_items_turn_into_points_and_boss_drops_three(self):
        engine = self.combat()
        engine.session.weapon, engine.session.shield = 4, SHIELD_MAX
        engine.drop("patch", engine.player.x, engine.player.y)
        engine.drop("backup", engine.player.x, engine.player.y)
        engine.update(STEP)
        self.assertEqual((engine.session.score, engine.session.weapon), (200, 4))
        engine.spawn_enemy("boss")
        engine.defeat(engine.enemies[-1])
        self.assertEqual([i.kind for i in engine.items], ["patch", "backup", "vaccine"])

    def test_stage_change_clears_items(self):
        engine = self.combat()
        engine.drop("badge", 300, 700)
        engine.enter("CHOICE")
        self.assertEqual((engine.items, engine.notices), ([], []))


class ScoreTests(unittest.TestCase):
    def test_penalties_applied_in_event_order(self):
        session = Session()
        session.add_score(-100)
        session.add_score(50)
        self.assertEqual(session.score, 50)

    def test_all_security_rewards_once(self):
        session = Session()
        for stage in range(3):
            session.choose(stage, 2)
            session.choose(stage, 2)
        self.assertEqual((session.score, session.shield, session.damage, session.skills), (600, 2, 2, 5))

    def test_grade_boundaries(self):
        self.assertEqual([grade_for(n) for n in (0, 2499, 2500, 4499, 4500, 6499, 6500)], list("CCBBAAS"))


if __name__ == "__main__":
    unittest.main()
