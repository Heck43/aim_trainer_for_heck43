"""
Утилита для автоматического вычисления хитбоксов из геометрии модели
Анализирует 3D модель и создаёт сферические хитбоксы для разных частей тела
"""
from panda3d.core import Point3, Vec3


class HitboxCalculator:
    """Вычисляет хитбоксы на основе геометрии модели"""

    # Зоны по высоте модели (в процентах от общей высоты)
    HEAD_ZONE_TOP = 1.0      # Верх головы
    HEAD_ZONE_BOTTOM = 0.80  # Низ головы (шея)

    BODY_ZONE_TOP = 0.78     # Верх тела (плечи)
    BODY_ZONE_BOTTOM = 0.35  # Низ тела (талия)

    ARM_ZONE_TOP = 0.75      # Верх рук (плечи)
    ARM_ZONE_BOTTOM = 0.40   # Низ рук (локти/кисти)

    LEG_ZONE_TOP = 0.38      # Верх ног (бёдра)
    LEG_ZONE_BOTTOM = 0.0    # Низ ног (стопы)

    @staticmethod
    def calculate_hitboxes_from_model(model_np, scale=1.0, eye_height=1.8):
        """
        Анализирует модель и возвращает хитбоксы в формате PLAYER_HITBOXES

        Args:
            model_np: NodePath модели игрока
            scale: Масштаб модели (например 2.0 если модель увеличена в 2 раза)
            eye_height: Высота глаз игрока (для корректировки координат)

        Returns:
            dict: {"target_head": (x, y, z, radius), ...}
        """
        try:
            # Получаем границы модели
            bounds = model_np.getTightBounds()
            if not bounds or bounds[0] is None or bounds[1] is None:
                print("[HitboxCalculator] Не удалось получить bounds модели, используем дефолтные хитбоксы")
                return HitboxCalculator._get_default_hitboxes()

            min_pt, max_pt = bounds

            # Вычисляем размеры модели (уже с учётом scale, так как bounds учитывает трансформации)
            width = max_pt.x - min_pt.x
            height = max_pt.z - min_pt.z
            depth = max_pt.y - min_pt.y

            # Центр модели по X и Y (обнуляем чтобы хитбоксы были относительно игрока)
            # Хитбоксы должны быть в локальных координатах относительно позиции игрока
            center_x = 0.0
            center_y = 0.0

            # Базовая высота (от земли)
            base_z = min_pt.z

            print(f"[HitboxCalculator] Размеры модели: W={width:.2f}, H={height:.2f}, D={depth:.2f}")
            print(f"[HitboxCalculator] Bounds центр: X={(min_pt.x + max_pt.x) / 2.0:.2f}, Y={(min_pt.y + max_pt.y) / 2.0:.2f}")
            print(f"[HitboxCalculator] Используем центр: X={center_x:.2f}, Y={center_y:.2f}, База Z={base_z:.2f}")

            # Вычисляем хитбоксы для каждой части тела
            hitboxes = {}

            # ГОЛОВА
            head_z_top = base_z + height * HitboxCalculator.HEAD_ZONE_TOP
            head_z_bottom = base_z + height * HitboxCalculator.HEAD_ZONE_BOTTOM
            head_z_center = (head_z_top + head_z_bottom) / 2.0
            head_radius = min(width, depth) * 0.18  # Уменьшили с 0.25 до 0.18

            # Корректируем относительно eye_height (позиция игрока = высота глаз)
            # Модель выровнена по земле, но игрок стоит на высоте eye_height
            head_offset_z = head_z_center - eye_height

            hitboxes["target_head"] = (
                center_x,
                center_y,
                head_offset_z,
                head_radius
            )

            # ТЕЛО
            body_z_top = base_z + height * HitboxCalculator.BODY_ZONE_TOP
            body_z_bottom = base_z + height * HitboxCalculator.BODY_ZONE_BOTTOM
            body_z_center = (body_z_top + body_z_bottom) / 2.0
            body_radius = max(width, depth) * 0.25  # Уменьшили с 0.35 до 0.25

            body_offset_z = body_z_center - eye_height

            hitboxes["target_body"] = (
                center_x,
                center_y,
                body_offset_z,
                body_radius
            )

            # ЛЕВАЯ РУКА
            arm_z_top = base_z + height * HitboxCalculator.ARM_ZONE_TOP
            arm_z_bottom = base_z + height * HitboxCalculator.ARM_ZONE_BOTTOM
            arm_z_center = (arm_z_top + arm_z_bottom) / 2.0
            arm_radius = width * 0.12  # Уменьшили с 0.15 до 0.12

            arm_offset_z = arm_z_center - eye_height
            arm_offset_x = -width * 0.45  # Левая рука слева от центра

            hitboxes["target_left_arm"] = (
                center_x + arm_offset_x,
                center_y,
                arm_offset_z,
                arm_radius
            )

            # ПРАВАЯ РУКА
            hitboxes["target_right_arm"] = (
                center_x - arm_offset_x,  # Правая рука справа
                center_y,
                arm_offset_z,
                arm_radius
            )

            # НОГИ
            leg_z_top = base_z + height * HitboxCalculator.LEG_ZONE_TOP
            leg_z_bottom = base_z + height * HitboxCalculator.LEG_ZONE_BOTTOM
            leg_z_center = (leg_z_top + leg_z_bottom) / 2.0
            leg_radius = max(width, depth) * 0.22  # Уменьшили с 0.30 до 0.22

            leg_offset_z = leg_z_center - eye_height

            hitboxes["target_legs"] = (
                center_x,
                center_y,
                leg_offset_z,
                leg_radius
            )

            # Логируем результаты
            print("[HitboxCalculator] Вычисленные хитбоксы:")
            for part, (x, y, z, r) in hitboxes.items():
                print(f"  {part}: pos=({x:.2f}, {y:.2f}, {z:.2f}), radius={r:.2f}")

            return hitboxes

        except Exception as e:
            print(f"[HitboxCalculator] Ошибка при вычислении хитбоксов: {e}")
            import traceback
            traceback.print_exc()
            return HitboxCalculator._get_default_hitboxes()

    @staticmethod
    def _get_default_hitboxes():
        """Возвращает дефолтные хитбоксы (текущие hardcoded значения)"""
        return {
            "target_head": (0.0, 0.0, 0.00, 0.32),
            "target_body": (0.0, 0.0, -0.70, 0.50),
            "target_left_arm": (-0.55, 0.0, -0.70, 0.26),
            "target_right_arm": (0.55, 0.0, -0.70, 0.26),
            "target_legs": (0.0, 0.0, -1.45, 0.42),
        }

    @staticmethod
    def validate_hitboxes(hitboxes, max_radius=2.0):
        """
        Проверяет что хитбоксы имеют разумные размеры (защита от читов)

        Args:
            hitboxes: dict с хитбоксами
            max_radius: максимально допустимый радиус сферы

        Returns:
            bool: True если хитбоксы валидны
        """
        if not isinstance(hitboxes, dict):
            return False

        required_parts = ["target_head", "target_body", "target_left_arm",
                         "target_right_arm", "target_legs"]

        for part in required_parts:
            if part not in hitboxes:
                return False

            hitbox = hitboxes[part]
            if not isinstance(hitbox, (list, tuple)) or len(hitbox) != 4:
                return False

            x, y, z, radius = hitbox

            # Проверяем что радиус разумный
            if radius <= 0 or radius > max_radius:
                return False

            # Проверяем что позиция не слишком далеко от центра
            if abs(x) > 5.0 or abs(y) > 5.0 or abs(z) > 5.0:
                return False

        return True
