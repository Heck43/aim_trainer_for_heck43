from panda3d.core import Point3, Vec3


class Weapon:
    """Базовый класс для всех типов оружия"""

    def __init__(self, game, weapon_data):
        self.game = game
        self.data = weapon_data
        self.name = ""

    def get_muzzle_position(self, camera_pos, camera_mat):
        """Возвращает позицию дула оружия в мировых координатах"""
        raise NotImplementedError("Subclass must implement get_muzzle_position")

    def get_spread(self, is_moving, is_jumping, current_spread):
        """Вычисляет разброс с учетом движения и прыжка"""
        spread_params = self.data["spread"]
        final_spread = current_spread

        if is_moving:
            final_spread *= spread_params["moving_mult"]
        if is_jumping:
            final_spread *= spread_params["jumping_mult"]

        return min(final_spread, spread_params["max"])
