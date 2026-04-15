import time
from panda3d.core import Vec3

class MovementManager:
    def __init__(self, game):
        self.game = game

        # movement parameters
        self.move_speed = 10.0
        self.sprint_speed = 15.0
        self.jump_power = 15.0
        self.gravity = -50.0
        self.vertical_velocity = 0.0
        self.horizontal_velocity = Vec3(0, 0, 0)
        self.is_jumping = False
        self.is_sprinting = False
        self.jump_speed_boost = 1.0

        # bhop/combo parameters
        self.jump_combo_time = 1.0
        self.jump_combo_multiplier = 1.0
        self.max_combo_multiplier = 5.0
        self.combo_stages = [
            {'jumps': 1, 'multiplier': 1.0},
            {'jumps': 2, 'multiplier': 1.4},
            {'jumps': 3, 'multiplier': 1.8},
            {'jumps': 4, 'multiplier': 2.2},
            {'jumps': 5, 'multiplier': 2.6},
            {'jumps': 6, 'multiplier': 3.0},
            {'jumps': 7, 'multiplier': 3.2}
        ]
        self.current_combo_jumps = 0
        self.last_jump_time = 0
        self.combo_task = None

    def start_jump(self):
        if self.game.is_splash_screen_active:
            return
        if self.game.chat_manager.is_chat_active:
            return

        if not self.is_jumping:
            current_time = time.time()

            if self.game.settings.get('bhop_enabled', True):
                if current_time - self.last_jump_time < self.jump_combo_time:
                    self.current_combo_jumps += 1
                    for stage in self.combo_stages:
                        if stage['jumps'] == self.current_combo_jumps:
                            self.jump_combo_multiplier = stage['multiplier']
                            break
                else:
                    self.current_combo_jumps = 1
                    self.jump_combo_multiplier = 1.0
            else:
                self.jump_combo_multiplier = 1.0
                self.current_combo_jumps = 0

            self.vertical_velocity = self.jump_power

            move_vec = Vec3(0, 0, 0)
            if self.game.keyMap["w"]: move_vec.setY(move_vec.getY() + 1)
            if self.game.keyMap["s"]: move_vec.setY(move_vec.getY() - 1)
            if self.game.keyMap["a"]: move_vec.setX(move_vec.getX() - 1)
            if self.game.keyMap["d"]: move_vec.setX(move_vec.getX() + 1)

            if move_vec.length() > 0:
                move_vec.normalize()
                base_speed = self.sprint_speed if self.game.keyMap["shift"] else self.move_speed
                self.horizontal_velocity = move_vec * base_speed * self.jump_combo_multiplier
            else:
                self.horizontal_velocity = Vec3(0, 0, 0)

            self.is_jumping = True
            self.last_jump_time = current_time

            if self.combo_task:
                self.game.taskMgr.remove(self.combo_task)
            self.combo_task = self.game.taskMgr.doMethodLater(
                self.jump_combo_time,
                self.reset_jump_combo,
                'reset_jump_combo'
            )

    def reset_jump_combo(self, task):
        self.jump_combo_multiplier = 1.0
        self.current_combo_jumps = 0
        self.horizontal_velocity = Vec3(0, 0, 0)
        return task.done
