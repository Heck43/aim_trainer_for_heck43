"""
3D модель для отображения других игроков
"""
from __future__ import annotations

import os
import sys
import glob
from panda3d.core import NodePath, TextNode, Point3, Vec3, Filename, loadPrcFileData

class RemotePlayerModel:
    """3D модель удаленного игрока"""

    # Настройки позиционирования:
# У тебя в сетевых данных pos похоже хранит позицию камеры (высота ~1.8).
# Тогда модель надо опускать на высоту глаз.
    POS_IS_EYE = True
    EYE_HEIGHT = 1.8

# Доп. сдвиг модели по Z (если после автоподгонки всё равно висит/утопает)
    MODEL_Z_OFFSET = 0.0

    # Цвета для разных игроков
    PLAYER_COLORS = [
        (0.2, 0.6, 1.0),   # Синий
        (1.0, 0.3, 0.3),   # Красный
        (0.3, 1.0, 0.3),   # Зеленый
        (1.0, 1.0, 0.3),   # Желтый
        (1.0, 0.5, 0.0),   # Оранжевый
        (0.8, 0.3, 1.0),   # Фиолетовый
        (0.3, 1.0, 1.0),   # Голубой
        (1.0, 0.5, 0.8),   # Розовый
    ]

    color_index = 0
    
    # Кэш для моделей (общий для всех экземпляров)
    _model_cache = {}
    _main_model_cache_key = "__remote_player_main_model__"

    def __init__(self, game, player_id: str, player_name: str):
        self.game = game
        self.player_id = player_id
        self.player_name = player_name

        # Позиция и поворот
        self.target_pos = Point3(0, 0, 0)
        self.target_heading = 0.0
        self.target_pitch = 0.0
        self.current_pos = Point3(0, 0, 0)
        self.current_heading = 0.0
        self.current_pitch = 0.0
        
        # Для предсказания движения (extrapolation)
        self.last_target_pos = Point3(0, 0, 0)
        self.velocity = Vec3(0, 0, 0)
        self.last_update_time = 0.0

        # Состояние
        self.weapon = "pistol"
        self.shooting = False
        self.score = 0
        
        # Для интерполяции и предсказания
        self.velocity = Vec3(0, 0, 0)
        self.last_target_pos = Point3(0, 0, 0)
        self.last_update_time = 0.0

        # Выбираем цвет
        self.color = RemotePlayerModel.PLAYER_COLORS[
            RemotePlayerModel.color_index % len(RemotePlayerModel.PLAYER_COLORS)
        ]
        RemotePlayerModel.color_index += 1

        # Корневой узел модели
        self.model = NodePath(f"remote_player_{self.player_id}")
        self.model.reparentTo(self.game.render)

        # Создаем визуал + оружие + имя
        self.create_model()

    @staticmethod
    def _get_project_root_static() -> str:
        if getattr(sys, "frozen", False):
            return os.path.abspath(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))

        here = os.path.abspath(os.path.dirname(__file__))
        if os.path.isdir(os.path.join(here, "model_textures")):
            return here

        parent = os.path.abspath(os.path.join(here, ".."))
        return parent

    @classmethod
    def _collect_model_candidates(cls) -> list[str]:
        base_path = cls._get_project_root_static()
        model_dir = os.path.join(base_path, "model_textures")
        candidates = [
            os.path.join(model_dir, "untitled.bam"),
            os.path.join(model_dir, "untitled.egg"),
            os.path.join(model_dir, "untitled.gltf"),
            os.path.join(model_dir, "untitled.glb"),
        ]
        candidates += sorted(glob.glob(os.path.join(model_dir, "*.bam")))
        return candidates

    @classmethod
    def preload_main_model(cls, game) -> bool:
        """Preloads the single multiplayer player model into class cache."""
        cached = cls._model_cache.get(cls._main_model_cache_key)
        if cached and not cached.isEmpty():
            return True

        for path in cls._collect_model_candidates():
            if not path or not os.path.exists(path):
                continue
            try:
                np = game.loader.loadModel(Filename.fromOsSpecific(path))
                if np and not np.isEmpty():
                    cls._model_cache[cls._main_model_cache_key] = np
                    print(f"[PlayerModel] Preloaded main MP model from {path}")
                    return True
            except Exception as e:
                print(f"[PlayerModel] Failed to preload model {path}: {e}")

        print("[PlayerModel] MP model preload skipped: no valid model file found")
        return False

    def _get_project_root(self) -> str:
        # Для запуска из исходников — обычно корень = папка, где лежит этот файл.
        # Если структура другая — попробуем родителя.
        if getattr(sys, "frozen", False):
            # PyInstaller: sys._MEIPASS чаще всего указывает на временную папку с ресурсами
            return os.path.abspath(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))

        here = os.path.abspath(os.path.dirname(__file__))
        if os.path.isdir(os.path.join(here, "model_textures")):
            return here

        parent = os.path.abspath(os.path.join(here, ".."))
        return parent

    def _load_player_model(self) -> NodePath | None:
        """Пытается загрузить модель из model_textures. Возвращает NodePath или None."""
        cached_main = RemotePlayerModel._model_cache.get(RemotePlayerModel._main_model_cache_key)
        if cached_main and not cached_main.isEmpty():
            return cached_main.copyTo(NodePath())

        if RemotePlayerModel.preload_main_model(self.game):
            cached_main = RemotePlayerModel._model_cache.get(RemotePlayerModel._main_model_cache_key)
            if cached_main and not cached_main.isEmpty():
                return cached_main.copyTo(NodePath())

        base_path = self._get_project_root()

        # Важно: добавим корень проекта в model-path, чтобы относительные пути работали стабильно.
        # (Даже если грузим по абсолютному пути — это не мешает, а часто помогает с текстурами.)
        loadPrcFileData("", f"model-path {base_path}")

        model_dir = os.path.join(base_path, "model_textures")

        # 1) Пытаемся по ожидаемому имени
        candidates = [
            os.path.join(model_dir, "untitled.bam"),
            os.path.join(model_dir, "untitled.egg"),
            os.path.join(model_dir, "untitled.gltf"),
            os.path.join(model_dir, "untitled.glb"),
        ]

        # 2) Если не нашли — берем первый *.bam в папке (удобно, если файл называется иначе)
        candidates += sorted(glob.glob(os.path.join(model_dir, "*.bam")))

        for path in candidates:
            if not path:
                continue
            if not os.path.exists(path):
                continue
            try:
                np = self.game.loader.loadModel(Filename.fromOsSpecific(path))
                if np and not np.isEmpty():
                    print(f"[PlayerModel] Загружена модель для {self.player_name} из {path}")
                    return np
            except Exception as e:
                print(f"[PlayerModel] Не смог загрузить {path}: {e}")

        # Диагностика: покажем, что реально лежит в папке
        try:
            if os.path.isdir(model_dir):
                print("[PlayerModel] model_textures содержит:", os.listdir(model_dir))
            else:
                print(f"[PlayerModel] Папка не найдена: {model_dir}")
        except Exception:
            pass

        return None


    def _align_model_to_ground(self, np: NodePath):
        """Сдвигает геометрию так, чтобы нижняя точка модели была на Z=0 (внутри self.model)."""
        try:
            bounds = np.getTightBounds()
            if bounds and bounds[0] is not None and bounds[1] is not None:
                min_pt, max_pt = bounds
                # Переносим модель так, чтобы ее низ оказался на уровне 0
                np.setPos(0, 0, -min_pt.z)
                if self.MODEL_Z_OFFSET:
                    np.setZ(np.getZ() + float(self.MODEL_Z_OFFSET))
        except Exception as e:
            print(f"[PlayerModel] Не смог выровнять модель по земле: {e}")

    def create_model(self):
        """Создает 3D модель игрока"""
        # Попытка загрузить модель
        player_model = self._load_player_model()

        if player_model:
            # Увеличиваем размер модели (примерно в 2 раза)
            player_model.setScale(2.0)
            # Сначала ставим в (0,0,0), затем опускаем геометрию до земли
            player_model.setPos(0, 0, 0)
            self._align_model_to_ground(player_model)
            player_model.reparentTo(self.model)
            self.body = player_model
        else:
            # Fallback на простую модель
            self._create_simple_model_body()

        # Контейнер для оружия (поворачивается по pitch) — должен существовать ВСЕГДА
        self.weapon_pivot = NodePath("weapon_pivot")
        self.weapon_pivot.reparentTo(self.model)
        self.weapon_pivot.setPos(0, 0, 1.3)

        # Создаем модель оружия
        self.weapon_model = NodePath("weapon")
        self.weapon_model.reparentTo(self.weapon_pivot)
        self.create_weapon(self.weapon)

        # Имя игрока над головой
        self.name_text = TextNode(f"name_{self.player_id}")
        self.name_text.setText(self.player_name)
        self.name_text.setAlign(TextNode.ACenter)
        self.name_text.setTextColor(1, 1, 1, 1)

        self.name_np = self.model.attachNewNode(self.name_text)
        # Поднимаем текст выше, так как модель увеличена в 2 раза
        # Высота модели примерно 2-3 единицы после масштабирования, поднимаем до 4.5
        self.name_np.setPos(0, 0, 4.5)
        self.name_np.setScale(0.3)
        self.name_np.setBillboardPointEye()  # Всегда смотрит на камеру

    def _load_any_builtin(self, names: list[str]) -> NodePath | None:
        """Загружает модель из списка с кэшированием"""
        # Проверяем кэш
        for name in names:
            if name in RemotePlayerModel._model_cache:
                cached = RemotePlayerModel._model_cache[name]
                if cached and not cached.isEmpty():
                    # Возвращаем копию модели
                    return cached.copyTo(NodePath())
        
        # Если не в кэше, пробуем загрузить
        for name in names:
            try:
                # Используем safe_load_model если доступен
                if hasattr(self.game, 'safe_load_model'):
                    np = self.game.safe_load_model(name)
                else:
                    np = self.game.loader.loadModel(name)
                
                if np and not np.isEmpty():
                    # Сохраняем в кэш
                    RemotePlayerModel._model_cache[name] = np
                    # Возвращаем копию
                    return np.copyTo(NodePath())
            except Exception:
                continue
        return None

    def _create_simple_model_body(self):
        """Создает простую модель из примитивов (fallback). Без cylinder (его часто нет в стандартных моделях)."""
        # Тело
        body = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
        if body:
            body.setScale(0.3, 0.2, 0.8)
            body.setPos(0, 0, 0.8)
            body.setColor(*self.color, 1)
            body.reparentTo(self.model)
            self.body = body

        # Голова
        head = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
        if head:
            head.setScale(0.2, 0.2, 0.2)
            head.setPos(0, 0, 1.7)
            head.setColor(*self.color, 1)
            head.reparentTo(self.model)
            self.head = head

    def create_weapon(self, weapon_type: str):
        """Создает модель оружия"""
        # Очищаем старое оружие
        self.weapon_model.getChildren().detach()

        try:
            if weapon_type == "pistol":
                barrel = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
                if barrel:
                    barrel.setScale(0.03, 0.15, 0.03)
                    barrel.setPos(0.15, 0.3, 0)
                    barrel.setColor(0.2, 0.2, 0.2, 1)
                    barrel.reparentTo(self.weapon_model)

            elif weapon_type == "rifle":
                barrel = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
                if barrel:
                    barrel.setScale(0.03, 0.35, 0.03)
                    barrel.setPos(0.15, 0.4, 0)
                    barrel.setColor(0.2, 0.2, 0.2, 1)
                    barrel.reparentTo(self.weapon_model)

                stock = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
                if stock:
                    stock.setScale(0.04, 0.15, 0.06)
                    stock.setPos(0.15, 0.0, 0)
                    stock.setColor(0.4, 0.3, 0.2, 1)
                    stock.reparentTo(self.weapon_model)

            elif weapon_type == "sniper":
                barrel = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
                if barrel:
                    barrel.setScale(0.025, 0.5, 0.025)
                    barrel.setPos(0.15, 0.5, 0)
                    barrel.setColor(0.15, 0.15, 0.15, 1)
                    barrel.reparentTo(self.weapon_model)

                scope = self._load_any_builtin(["models/box", "models/misc/rgbCube", "models/misc/box"])
                if scope:
                    scope.setScale(0.03, 0.08, 0.05)
                    scope.setPos(0.15, 0.3, 0.05)
                    scope.setColor(0.1, 0.1, 0.1, 1)
                    scope.reparentTo(self.weapon_model)
        except Exception as e:
            print(f"[PlayerModel] Error creating weapon: {e}")

    def _normalize_angle(self, angle: float) -> float:
        """Нормализует угол в диапазон [-180, 180]"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def update(self, player_data: dict, dt: float):
        """Обновляет состояние модели (оптимизированная версия)"""
        import time
        current_time = time.time()
        
        # Обновляем целевые значения
        pos = player_data.get("pos", [0, 0, 0])
        # pos в данных часто является позицией камеры. Тогда опускаем модель на высоту глаз.
        z = pos[2] - self.EYE_HEIGHT if self.POS_IS_EYE else pos[2]
        new_target_pos = Point3(pos[0], pos[1], z)
        new_target_heading = float(player_data.get("heading", 0.0))
        new_target_pitch = float(player_data.get("pitch", 0.0))
        
        # Нормализуем целевой heading сразу
        new_target_heading = self._normalize_angle(new_target_heading)
        
        # Вычисляем скорость движения (для предсказания) - только если прошло достаточно времени
        if self.last_update_time > 0:
            time_since_last = current_time - self.last_update_time
            if time_since_last > 0.001 and time_since_last < 1.0:  # Избегаем деления на ноль и больших задержек
                pos_delta = new_target_pos - self.last_target_pos
                self.velocity = Vec3(
                    pos_delta.getX() / time_since_last,
                    pos_delta.getY() / time_since_last,
                    pos_delta.getZ() / time_since_last
                )
                # Ограничиваем максимальную скорость (защита от скачков)
                max_speed = 50.0
                if self.velocity.length() > max_speed:
                    self.velocity.normalize()
                    self.velocity *= max_speed
            else:
                self.velocity = Vec3(0, 0, 0)
        
        self.last_target_pos = new_target_pos
        self.last_update_time = current_time
        
        # Защита от больших скачков позиции (возможно потеря пакетов или телепорт)
        pos_diff = (new_target_pos - self.current_pos).length()
        if pos_diff > 10.0:  # Если скачок больше 10 единиц - это явно ошибка
            # Убираем print для уменьшения лагов
            self.current_pos = new_target_pos
            self.velocity = Vec3(0, 0, 0)  # Сбрасываем скорость
        else:
            self.target_pos = new_target_pos
        
        self.target_heading = new_target_heading
        self.target_pitch = new_target_pitch

        # Оптимизированная интерполяция позиции
        lerp_speed = 25.0  # Уменьшили скорость интерполяции для плавности
        diff = self.target_pos - self.current_pos
        distance = diff.length()
        
        # Упрощенная интерполяция
        if distance > 0.1:
            lerp_factor = min(lerp_speed * dt, 0.8)  # Ограничиваем максимальный шаг
            self.current_pos += diff * lerp_factor
        elif distance > 0.01:
            lerp_factor = min(lerp_speed * dt, 1.0)
            self.current_pos += diff * lerp_factor
        else:
            # Если очень близко - сразу устанавливаем
            self.current_pos = self.target_pos

        # Упрощенная интерполяция поворота
        self.current_heading = self._normalize_angle(self.current_heading)
        heading_diff = self._normalize_angle(self.target_heading - self.current_heading)
        
        if abs(heading_diff) > 1.0:  # Увеличили порог для уменьшения вычислений
            heading_lerp_speed = 20.0
            heading_lerp_factor = min(heading_lerp_speed * dt, 0.8)
            self.current_heading += heading_diff * heading_lerp_factor
            self.current_heading = self._normalize_angle(self.current_heading)
        else:
            self.current_heading = self.target_heading

        # Упрощенная интерполяция pitch
        pitch_diff = self.target_pitch - self.current_pitch
        if abs(pitch_diff) > 1.0:  # Увеличили порог
            pitch_lerp_speed = 20.0
            pitch_lerp_factor = min(pitch_lerp_speed * dt, 0.8)
            self.current_pitch += pitch_diff * pitch_lerp_factor
        else:
            self.current_pitch = self.target_pitch

        # Применяем к модели (только если изменилось)
        if distance > 0.001 or abs(heading_diff) > 0.1 or abs(pitch_diff) > 0.1:
            self.model.setPos(self.current_pos)
            final_heading = self._normalize_angle(self.current_heading + 180)
            self.model.setH(final_heading)
            self.weapon_pivot.setP(-self.current_pitch)

        # Обновляем оружие если изменилось (только при изменении)
        new_weapon = player_data.get("weapon", "pistol")
        if new_weapon != self.weapon:
            self.weapon = new_weapon
            self.create_weapon(new_weapon)

        # Эффект стрельбы
        new_shooting = player_data.get("shooting", False)
        self.shooting = new_shooting

        # Обновляем счет (только если изменился)
        new_score = player_data.get("score", 0)
        if new_score != self.score:
            self.score = new_score
            self.name_text.setText(f"{self.player_name}\n{self.score}")

    def show_muzzle_flash(self):
        """Legacy hook; remote tracers are drawn from authoritative shot_result."""
        return

    def destroy(self):
        """Удаляет модель"""
        if self.model:
            self.model.removeNode()
            self.model = None



