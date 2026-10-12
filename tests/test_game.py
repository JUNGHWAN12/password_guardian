import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from password_guardian.config import FIELD, PLAYER_START
from password_guardian.engine import Engine, Entity, overlaps
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
        self.assertEqual(len(engine.enemies), 1)

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
        engine.enemy_bullets = [Entity(99, "round", *PLAYER_START, 8)]
        engine.hurt()
        self.assertEqual((engine.session.score, engine.session.hp, engine.session.damage, engine.session.skills), (0, 3, 2, 1))
        self.assertEqual(engine.session.revive_count, 1)
        self.assertEqual(engine.invulnerable, 2)
        self.assertEqual(len(engine.enemy_bullets), 0)

    def test_skill_radius_cooldown_and_exhaustion(self):
        engine = self.combat()
        x, y = PLAYER_START
        engine.enemy_bullets = [Entity(1, "round", x+100, y, 8), Entity(2, "round", x+200, y, 8)]
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
        self.assertEqual(len(engine.enemies), 20)
        for _ in range(100):
            engine.fire_enemy(engine.enemies[0])
        self.assertEqual(len(engine.enemy_bullets), 250)

    def test_choice_freezes_combat(self):
        engine = self.combat()
        engine.spawn_enemy("bot")
        enemy = engine.enemies[0]
        engine.state = "CHOICE"
        before = (enemy.x, enemy.y, enemy.fire_in)
        engine.update(1, (1, 1))
        self.assertEqual((enemy.x, enemy.y, enemy.fire_in), before)
        self.assertEqual((engine.player.x, engine.player.y), PLAYER_START)


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
        self.assertEqual([grade_for(n) for n in (0, 799, 800, 1399, 1400, 1999, 2000)], list("CCBBAAS"))


if __name__ == "__main__":
    unittest.main()
