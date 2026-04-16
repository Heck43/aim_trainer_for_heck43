from panda3d.core import Point3
from managers.weapons.base_weapon import Weapon


class DualRevolvers(Weapon):
    """Класс двух револьверов"""

    def __init__(self, game, weapon_data):
        super().__init__(game, weapon_data)
        self.name = "dual_revolvers"
        self.active_revolver = "left"

    def get_muzzle_position(self, camera_pos, camera_mat):
        """Возвращает позицию дула активного револьвера"""
        if self.active_revolver == "left":
            local_pos = Point3(-2.0, 0.6, -0.2)
        else:
            local_pos = Point3(0.4, 0.6, -0.2)
        return camera_pos + camera_mat.xformVec(local_pos)

    def switch_revolver(self):
        """Переключает активный револьвер"""
        self.active_revolver = "right" if self.active_revolver == "left" else "left"
