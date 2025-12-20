"""
3D модель для отображения других игроков
"""
from panda3d.core import NodePath, TextNode, Point3, Vec3
from direct.gui.OnscreenText import OnscreenText

class RemotePlayerModel:
    """3D модель удаленного игрока"""
    
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
    
    def __init__(self, game, player_id: str, player_name: str):
        self.game = game
        self.player_id = player_id
        self.player_name = player_name
        
        # Позиция и поворот
        self.target_pos = Point3(0, 0, 0)
        self.target_heading = 0
        self.target_pitch = 0
        self.current_pos = Point3(0, 0, 0)
        self.current_heading = 0
        self.current_pitch = 0
        
        # Состояние
        self.weapon = "pistol"
        self.shooting = False
        self.score = 0
        
        # Выбираем цвет
        self.color = RemotePlayerModel.PLAYER_COLORS[
            RemotePlayerModel.color_index % len(RemotePlayerModel.PLAYER_COLORS)
        ]
        RemotePlayerModel.color_index += 1
        
        # Создаем модель
        self.create_model()
    
    def create_model(self):
        """Создает 3D модель игрока"""
        # Корневой узел
        self.model = NodePath(f"remote_player_{self.player_id}")
        self.model.reparentTo(self.game.render)
        
        # Тело (капсула из цилиндра + сфера)
        try:
            # Тело - цилиндр
            body = self.game.loader.loadModel("models/cylinder")
            if body:
                body.setScale(0.3, 0.3, 0.8)
                body.setPos(0, 0, 0.8)
                body.setColor(*self.color, 1)
                body.reparentTo(self.model)
                self.body = body
            else:
                # Fallback - используем box
                body = self.game.loader.loadModel("models/box")
                body.setScale(0.3, 0.2, 0.8)
                body.setPos(0, 0, 0.8)
                body.setColor(*self.color, 1)
                body.reparentTo(self.model)
                self.body = body
        except:
            # Если нет моделей, создаем простой box
            body = self.game.loader.loadModel("models/box")
            if body:
                body.setScale(0.3, 0.2, 0.8)
                body.setPos(0, 0, 0.8)
                body.setColor(*self.color, 1)
                body.reparentTo(self.model)
                self.body = body
        
        # Голова - сфера (или box как fallback)
        try:
            head = self.game.loader.loadModel("models/box")
            if head:
                head.setScale(0.2, 0.2, 0.2)
                head.setPos(0, 0, 1.7)
                head.setColor(*self.color, 1)
                head.reparentTo(self.model)
                self.head = head
        except:
            pass
        
        # Контейнер для оружия (поворачивается по pitch)
        self.weapon_pivot = NodePath("weapon_pivot")
        self.weapon_pivot.reparentTo(self.model)
        self.weapon_pivot.setPos(0, 0, 1.3)
        
        # Создаем модель оружия
        self.weapon_model = NodePath("weapon")
        self.weapon_model.reparentTo(self.weapon_pivot)
        self.create_weapon("pistol")
        
        # Имя игрока над головой
        self.name_text = TextNode(f"name_{self.player_id}")
        self.name_text.setText(self.player_name)
        self.name_text.setAlign(TextNode.ACenter)
        self.name_text.setTextColor(1, 1, 1, 1)
        
        self.name_np = self.model.attachNewNode(self.name_text)
        self.name_np.setPos(0, 0, 2.2)
        self.name_np.setScale(0.3)
        self.name_np.setBillboardPointEye()  # Всегда смотрит на камеру
    
    def create_weapon(self, weapon_type: str):
        """Создает модель оружия"""
        # Очищаем старое оружие
        self.weapon_model.getChildren().detach()
        
        try:
            if weapon_type == "pistol":
                # Простой пистолет
                barrel = self.game.loader.loadModel("models/box")
                if barrel:
                    barrel.setScale(0.03, 0.15, 0.03)
                    barrel.setPos(0.15, 0.3, 0)
                    barrel.setColor(0.2, 0.2, 0.2, 1)
                    barrel.reparentTo(self.weapon_model)
                    
            elif weapon_type == "rifle":
                # Винтовка
                barrel = self.game.loader.loadModel("models/box")
                if barrel:
                    barrel.setScale(0.03, 0.35, 0.03)
                    barrel.setPos(0.15, 0.4, 0)
                    barrel.setColor(0.2, 0.2, 0.2, 1)
                    barrel.reparentTo(self.weapon_model)
                    
                stock = self.game.loader.loadModel("models/box")
                if stock:
                    stock.setScale(0.04, 0.15, 0.06)
                    stock.setPos(0.15, 0.0, 0)
                    stock.setColor(0.4, 0.3, 0.2, 1)
                    stock.reparentTo(self.weapon_model)
                    
            elif weapon_type == "sniper":
                # Снайперка
                barrel = self.game.loader.loadModel("models/box")
                if barrel:
                    barrel.setScale(0.025, 0.5, 0.025)
                    barrel.setPos(0.15, 0.5, 0)
                    barrel.setColor(0.15, 0.15, 0.15, 1)
                    barrel.reparentTo(self.weapon_model)
                    
                scope = self.game.loader.loadModel("models/box")
                if scope:
                    scope.setScale(0.03, 0.08, 0.05)
                    scope.setPos(0.15, 0.3, 0.05)
                    scope.setColor(0.1, 0.1, 0.1, 1)
                    scope.reparentTo(self.weapon_model)
        except Exception as e:
            print(f"[PlayerModel] Error creating weapon: {e}")
    
    def update(self, player_data: dict, dt: float):
        """Обновляет состояние модели"""
        # Обновляем целевые значения
        pos = player_data.get("pos", [0, 0, 0])
        self.target_pos = Point3(pos[0], pos[1], pos[2])
        self.target_heading = player_data.get("heading", 0)
        self.target_pitch = player_data.get("pitch", 0)
        
        # Интерполяция позиции (плавное движение)
        lerp_speed = 15.0  # Скорость интерполяции
        
        # Позиция
        diff = self.target_pos - self.current_pos
        if diff.length() > 0.01:
            self.current_pos += diff * min(lerp_speed * dt, 1.0)
        else:
            self.current_pos = self.target_pos
        
        # Поворот (heading)
        heading_diff = self.target_heading - self.current_heading
        # Нормализуем угол
        while heading_diff > 180:
            heading_diff -= 360
        while heading_diff < -180:
            heading_diff += 360
        
        if abs(heading_diff) > 0.1:
            self.current_heading += heading_diff * min(lerp_speed * dt, 1.0)
        else:
            self.current_heading = self.target_heading
        
        # Pitch
        pitch_diff = self.target_pitch - self.current_pitch
        if abs(pitch_diff) > 0.1:
            self.current_pitch += pitch_diff * min(lerp_speed * dt, 1.0)
        else:
            self.current_pitch = self.target_pitch
        
        # Применяем к модели
        self.model.setPos(self.current_pos)
        self.model.setH(self.current_heading + 180)  # +180 чтобы смотреть в правильную сторону
        self.weapon_pivot.setP(-self.current_pitch)  # Pitch для оружия
        
        # Обновляем оружие если изменилось
        new_weapon = player_data.get("weapon", "pistol")
        if new_weapon != self.weapon:
            self.weapon = new_weapon
            self.create_weapon(new_weapon)
        
        # Эффект стрельбы
        new_shooting = player_data.get("shooting", False)
        if new_shooting and not self.shooting:
            self.show_muzzle_flash()
        self.shooting = new_shooting
        
        # Обновляем счет
        self.score = player_data.get("score", 0)
        self.name_text.setText(f"{self.player_name}\n{self.score}")
    
    def show_muzzle_flash(self):
        """Показывает вспышку выстрела"""
        # Можно добавить эффект вспышки здесь
        pass
    
    def destroy(self):
        """Удаляет модель"""
        if self.model:
            self.model.removeNode()
            self.model = None
