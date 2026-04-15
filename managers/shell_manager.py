import random
from panda3d.core import Vec3
from direct.showbase.ShowBaseGlobal import globalClock

class ShellManager:
    def __init__(self, game):
        self.game = game
        self.active_shells = []
        self.shell_model = None
        self.gravity = Vec3(0, 0, -9.8)

    def initialize(self, shell_model):
        self.shell_model = shell_model

    def create_shell_casing(self):
        if self.game.is_splash_screen_active:
            return

        if not self.shell_model:
            return

        current_weapon_model = self.game.weapon_models[self.game.current_weapon]

        shell = self.shell_model.copyTo(self.game.render)

        if self.game.current_weapon == "pistol":
            eject_offset = Vec3(0.1, 0.9, -0.1)
        elif self.game.current_weapon == "rifle":
            eject_offset = Vec3(0.1, 0.9, -0.05)
        else:  # sniper
            eject_offset = Vec3(0.1, 1.1, -0.05)

        shell_parent = self.game.render.attachNewNode("shell_parent")
        shell_parent.setPos(current_weapon_model.getPos(self.game.render))
        shell_parent.setHpr(current_weapon_model.getHpr(self.game.render))

        shell.reparentTo(shell_parent)
        shell.setPos(eject_offset)

        shell.wrtReparentTo(self.game.render)

        weapon_quat = current_weapon_model.getQuat(self.game.render)
        right = weapon_quat.getRight()
        up = weapon_quat.getUp()

        ejection_speed = 3.0
        vertical_speed = 1.0

        initial_velocity = Vec3()
        initial_velocity += right * ejection_speed
        initial_velocity += up * vertical_speed

        initial_velocity += Vec3(
            random.uniform(-0.2, 0.2),
            random.uniform(-0.2, 0.2),
            random.uniform(0, 0.5)
        )

        angular_velocity = Vec3(
            random.uniform(-720, 720),
            random.uniform(-720, 720),
            random.uniform(-720, 720)
        )

        shell_data = {
            'model': shell,
            'velocity': initial_velocity,
            'angular_velocity': angular_velocity,
            'time': 0
        }
        self.active_shells.append(shell_data)

        self.game.taskMgr.doMethodLater(2.0, self.remove_shell, 'remove_shell',
                            extraArgs=[shell_data], appendTask=True)

    def update_shells(self, task):
        if self.game.is_splash_screen_active:
            return task.cont

        dt = globalClock.getDt()

        for shell in self.active_shells:
            shell['time'] += dt

            current_pos = shell['model'].getPos()
            shell['velocity'] += self.gravity * dt
            new_pos = current_pos + shell['velocity'] * dt
            shell['model'].setPos(new_pos)

            current_hpr = shell['model'].getHpr()
            rotation = shell['angular_velocity'] * dt
            new_hpr = current_hpr + rotation
            shell['model'].setHpr(new_hpr)

            if new_pos.getZ() < 0:
                new_pos.setZ(0)
                shell['velocity'] = Vec3(0, 0, 0)
                shell['angular_velocity'] = Vec3(0, 0, 0)
                shell['model'].setPos(new_pos)

        return task.cont

    def remove_shell(self, shell_data, task):
        if shell_data in self.active_shells:
            self.active_shells.remove(shell_data)
            shell_data['model'].removeNode()
        return task.done
