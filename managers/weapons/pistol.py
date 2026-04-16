from panda3d.core import Point3
from managers.weapons.base_weapon import Weapon


class Pistol(Weapon):
    """Класс пистолета"""

    def __init__(self, game, weapon_data):
        super().__init__(game, weapon_data)
        self.name = "pistol"

    def get_muzzle_position(self, camera_pos, camera_mat):
        """Возвращает позицию дула пистолета"""
        local_pos = Point3(0.15, 0.6, -0.2)
        return camera_pos + camera_mat.xformVec(local_pos)
