import time
import random
from panda3d.core import TextNode, Point3, Vec4
from direct.interval.IntervalGlobal import LerpColorScaleInterval, Parallel
from direct.task import Task

class CollisionManager:
    def __init__(self, game):
        self.game = game

        self.combo_window = 2.0
        self.combo_multiplier = 1.0
        self.last_hit_time = 0

        self.damage_multipliers = {
            "target_head": 2.0,
            "target_body": 1.0,
            "target_legs": 0.75
        }

    def handle_collision(self, entry):
        if self.game.is_multiplayer:
            return

        hit_node = entry.getIntoNode()
        if not hit_node.getName().startswith('target_'):
            return

        target_np = entry.getIntoNodePath().getParent()
        while target_np.getName() != "target_root":
            target_np = target_np.getParent()
            if target_np is None:
                return

        damage = self.get_damage_for_part(hit_node.getName())

        if damage <= 0:
            return

        self.game.activate_hit_effects()

        self.game.hit_sound.play()

        current_time = time.time()
        if current_time - self.last_hit_time < self.combo_window:
            self.combo_multiplier = min(2.0, self.combo_multiplier + 0.2)
        else:
            self.combo_multiplier = 1.0
        self.last_hit_time = current_time

        points = int(damage * self.combo_multiplier)

        self.game.score += points

        if hasattr(self.game, 'score_text') and self.game.show_score:
            self.game.hud_manager.score_text.setText(f"Score: {self.game.score}")

        hit_pos = entry.getSurfacePoint(self.game.render)

        if self.game.settings.get('damage_numbers', True):
            self.spawn_damage_text(f"+{points}", hit_pos)

        target_obj = None
        for active_target in self.game.targets:
            if hasattr(active_target, 'model') and active_target.model == target_np:
                target_obj = active_target
                break

        if target_obj:
            self.game.shader_system.mark_target_hit(target_obj)
            if target_obj in self.game.targets:
                self.game.targets.remove(target_obj)
            target_obj.destroy()
        elif not target_np.isEmpty():
            target_np.removeNode()

        delay = random.uniform(0.5, 2.0)
        self.game.taskMgr.doMethodLater(delay, self.game.spawn_target, f"spawn_target_{time.time_ns()}")

        if self.game.settings.get('killfeed', True):
            self.game.create_killfeed_message("Training Bot")

    def get_damage_for_part(self, part_name):
        base_damage = self.game.weapons[self.game.current_weapon]["damage"]
        multiplier = self.damage_multipliers.get(part_name, 0)
        return int(base_damage * multiplier)

    def spawn_damage_text(self, text, pos):
        damage_text = TextNode('damage')
        damage_text.setText(text)
        damage_text.setAlign(TextNode.ACenter)

        text_node_path = self.game.aspect2d.attachNewNode(damage_text)

        offset_x = random.uniform(-0.15, 0.15)
        offset_y = random.uniform(-0.15, 0.15)

        text_node_path.setPos(offset_x, 0, offset_y)

        text_node_path.setScale(0.07 * self.game.get_hud_ui_scale())

        if int(text) >= 100:
            text_node_path.setColor(1, 0, 0, 1)
        elif int(text) >= 60:
            text_node_path.setColor(1, 0.5, 0, 1)
        else:
            text_node_path.setColor(1, 1, 1, 1)

        fade_interval = LerpColorScaleInterval(
            text_node_path,
            0.5,
            Vec4(1, 1, 1, 0),
            Vec4(1, 1, 1, 1)
        )

        pos_interval = text_node_path.posInterval(
            0.5,
            Point3(offset_x, 0, offset_y + 0.2),
            Point3(offset_x, 0, offset_y)
        )

        Parallel(fade_interval, pos_interval).start()

        self.game.taskMgr.doMethodLater(
            0.5,
            lambda task: text_node_path.removeNode(),
            'remove_damage_text'
        )
