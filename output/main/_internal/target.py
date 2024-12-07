from panda3d.core import Point3, Vec3, NodePath, CollisionNode, CollisionBox, CollisionSphere, BitMask32
from panda3d.core import TextureStage, Texture, CardMaker
import random
import os
import sys
import threading

class Target:
    # Кэш для текстур
    texture_cache = {}
    # Флаг, указывающий загружена ли категория
    category_loaded = False
    # Текущая загруженная категория
    current_category = None
    
    # Базовые текстуры для обычного режима - манекены без текстур
    TARGET_TEXTURES = []

    @staticmethod
    def normalize_path(path):
        """Преобразует путь в формат, который понимает Panda3D"""
        # Заменяем обратные слеши на прямые
        path = path.replace('\\', '/')
        # Если путь начинается с буквы диска (например, c:/), 
        # преобразуем его в формат /c/
        if len(path) > 1 and path[1] == ':':
            path = '/' + path[0].lower() + path[2:]
        return path
    
    @staticmethod
    def get_base_path():
        """Get the base path for resources, handling both development and compiled environments"""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Если запущено как exe
            base = os.path.dirname(sys.executable)
        else:
            # Если запущено в режиме разработки
            base = os.path.dirname(os.path.abspath(__file__))
        # Сразу нормализуем базовый путь
        return Target.normalize_path(base)
    
    @staticmethod
    def get_images_from_category(category):
        # Получаем базовый путь (уже нормализованный)
        base_path = Target.get_base_path()
        # Собираем путь к категории, используя прямые слеши
        category_path = f"{base_path}/images/nsfw/{category}"
        print(f"Ищем изображения в: {category_path}")
        
        # Для проверки существования используем Windows-путь
        windows_path = category_path
        if windows_path.startswith('/'):
            windows_path = windows_path[1].upper() + ':' + windows_path[2:]
        
        if not os.path.exists(windows_path):
            print(f"Путь к категории не существует: {category_path}")
            # Попробуем поискать в родительской директории
            parent_path = os.path.dirname(os.path.dirname(base_path))
            category_path = f"{Target.normalize_path(parent_path)}/images/nsfw/{category}"
            windows_path = category_path
            if windows_path.startswith('/'):
                windows_path = windows_path[1].upper() + ':' + windows_path[2:]
            
            print(f"Пробуем альтернативный путь: {category_path}")
            if not os.path.exists(windows_path):
                print(f"Альтернативный путь тоже не существует")
                return []
            
        valid_extensions = ['.png', '.jpg', '.jpeg']
        images = []
        
        try:
            files = os.listdir(windows_path)
            print(f"Найдено {len(files)} файлов в категории")
            for file in files:
                if any(file.lower().endswith(ext) for ext in valid_extensions):
                    # Создаем путь в формате Panda3D
                    full_path = f"{category_path}/{file}"
                    images.append(full_path)
                    print(f"Добавлено изображение: {full_path}")
        except Exception as e:
            print(f"Ошибка при чтении директории {category_path}: {e}")
                
        return images if images else []

    @staticmethod
    def preload_category(game, category):
        """Предварительно загружает все текстуры из категории"""
        if Target.current_category == category and Target.category_loaded:
            return

        Target.category_loaded = False
        Target.current_category = category
        
        # Очищаем старый кэш
        Target.texture_cache.clear()
        
        # Загружаем текстуры из NSFW категории
        category_images = Target.get_images_from_category(category)
        for image_path in category_images:
            try:
                tex = game.loader.loadTexture(Target.normalize_path(image_path))
                if tex:
                    Target.texture_cache[Target.normalize_path(image_path)] = tex
            except:
                print(f"Error preloading texture: {image_path}")
        
        Target.category_loaded = True
        print(f"Preloaded {len(Target.texture_cache)} textures for category: {category}")

    def load_texture(self, texture_path):
        """Загружает текстуру с использованием кэша"""
        normalized_path = Target.normalize_path(texture_path)
        
        if normalized_path in Target.texture_cache:
            return Target.texture_cache[normalized_path]
        
        try:
            tex = self.game.loader.loadTexture(normalized_path)
            if tex:
                Target.texture_cache[normalized_path] = tex
                return tex
        except Exception as e:
            print(f"Ошибка загрузки текстуры {normalized_path}: {e}")
        return None

    def __init__(self, game, pos):
        self.game = game
        self.position = pos
        self.max_hp = 100
        self.current_hp = self.max_hp
        self.is_active = True
        self.texture_path = None
        
        # Проверяем режим отображения
        show_images = self.game.settings.get('show_target_images', True)
        if show_images:
            category = self.game.settings.get('nsfw_category', 'furry')
            if not Target.category_loaded or Target.current_category != category:
                Target.preload_category(game, category)
            
            # Выбираем текстуру из NSFW категории
            category_images = self.get_images_from_category(category)
            if category_images:
                self.texture_path = random.choice(category_images)
                
        self.create_model()
        self.update_visibility()

    def update_visibility(self):
        """Обновляет видимость манекена в зависимости от настроек"""
        show_images = self.game.settings.get('show_target_images', True)
        
        if show_images:
            # Показываем картинку
            if hasattr(self, 'visual'):
                self.visual.show()
                self.visual.setTransparency(1)
                self.visual.setColor(1, 1, 1, 1)  # Полностью непрозрачная картинка
            
            # Скрываем части манекена
            for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
                np.setColor(1, 1, 1, 0)  # Полностью прозрачный
        else:
            # Скрываем картинку
            if hasattr(self, 'visual'):
                self.visual.hide()
            
            # Показываем части манекена красным цветом
            for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
                np.show()
                np.setColor(0.8, 0.2, 0.2, 1)  # Красный цвет, полностью непрозрачный
                # Настраиваем прозрачность для правильного отображения
                np.setTransparency(1)
                np.setBin("transparent", 0)
                np.setDepthWrite(True)  # Включаем запись в буфер глубины

    def create_model(self):
        # Create root node
        self.model = NodePath("target_root")
        self.model.setPos(self.position)
        self.model.reparentTo(self.game.render)
        
        # Create visual representation (card with texture)
        cm = CardMaker('card')
        cm.setFrame(-0.8, 0.8, 0, 3.0)  # 1.6x3.0 meters
        self.visual = self.model.attachNewNode(cm.generate())
        
        # Load and apply texture only if we have one
        if self.texture_path:
            try:
                tex = self.load_texture(self.texture_path)
                if tex:
                    self.visual.setTexture(tex)
                    self.visual.setTransparency(1)  # 1 = M_alpha
                    self.visual.setBin("transparent", 0)
                    self.visual.setDepthWrite(False)
            except:
                print(f"Error loading texture: {self.texture_path}")
        
        # Create collision geometry
        # Head (sphere)
        head_node = CollisionNode('target_head')
        head_sphere = CollisionSphere(0, 0, 2.6, 0.6)
        head_node.addSolid(head_sphere)
        head_node.setIntoCollideMask(BitMask32.bit(1))
        self.head_np = self.model.attachNewNode(head_node)
        
        # Body (box)
        body_node = CollisionNode('target_body')
        body_box = CollisionBox(Point3(0, 0, 1.5), 0.7, 0.4, 0.6)
        body_node.addSolid(body_box)
        body_node.setIntoCollideMask(BitMask32.bit(1))
        self.body_np = self.model.attachNewNode(body_node)
        
        # Arms (boxes)
        left_arm_node = CollisionNode('target_left_arm')
        left_arm_box = CollisionBox(Point3(-1.0, 0, 1.5), 0.3, 0.3, 0.6)
        left_arm_node.addSolid(left_arm_box)
        left_arm_node.setIntoCollideMask(BitMask32.bit(1))
        self.left_arm_np = self.model.attachNewNode(left_arm_node)
        
        right_arm_node = CollisionNode('target_right_arm')
        right_arm_box = CollisionBox(Point3(1.0, 0, 1.5), 0.3, 0.3, 0.6)
        right_arm_node.addSolid(right_arm_box)
        right_arm_node.setIntoCollideMask(BitMask32.bit(1))
        self.right_arm_np = self.model.attachNewNode(right_arm_node)
        
        # Legs (box)
        legs_node = CollisionNode('target_legs')
        legs_box = CollisionBox(Point3(0, 0, 0.6), 0.7, 0.4, 1.0)
        legs_node.addSolid(legs_box)
        legs_node.setIntoCollideMask(BitMask32.bit(1))
        self.legs_np = self.model.attachNewNode(legs_node)
        
        # Настраиваем начальную видимость
        self.update_visibility()
        
        # Поворачиваем манекен лицом к игроку
        self.model.lookAt(0, 0, 0)
        self.model.setH(self.model.getH() + 180)  # Разворачиваем на 180 градусов

    def destroy(self):
        if hasattr(self, 'model') and self.model:
            self.model.removeNode()

    def respawn(self):
        self.is_active = False
        # Скрываем все части манекена и отключаем коллизии
        self.visual.hide()
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            np.hide()
        self.disable_collisions()
        
        # Через 3 секунды восстанавливаем манекен
        taskMgr.doMethodLater(3.0, self.restore_target, 'restore_target')

    def restore_target(self, task):
        self.current_hp = self.max_hp
        self.is_active = True
        
        # Выбираем новую текстуру только если включен режим изображений
        show_images = self.game.settings.get('show_target_images', True)
        if show_images:
            category = self.game.settings.get('nsfw_category', 'furry')
            category_images = self.get_images_from_category(category)
            
            if category_images:
                self.texture_path = random.choice(category_images)
                tex = self.load_texture(self.texture_path)
                if tex:
                    self.visual.setTexture(tex)
                    self.visual.setTransparency(1)
                    self.visual.setBin("transparent", 0)
                    self.visual.setDepthWrite(False)
        
        # Показываем все части и включаем коллизии
        self.visual.show()
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            np.show()
        self.enable_collisions()
        
        self.update_visibility()
        return task.done

    def take_damage(self, damage):
        if not self.is_active:
            return
            
        self.current_hp -= damage
        if self.current_hp <= 0:
            self.respawn()
        else:
            # Change color based on remaining health
            health_fraction = self.current_hp / self.max_hp
            self.visual.setColorScale(1, health_fraction, health_fraction, 1)

    def disable_collisions(self):
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            np.node().setIntoCollideMask(BitMask32.allOff())

    def enable_collisions(self):
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            np.node().setIntoCollideMask(BitMask32.bit(1))

    def get_damage_for_part(self, part_name):
        """Возвращает урон в зависимости от части тела"""
        damages = {
            'target_head': 100,      # Голова - мгновенное убийство
            'target_body': 60,       # Тело - средний урон
            'target_left_arm': 40,   # Руки - малый урон
            'target_right_arm': 40,
            'target_legs': 40        # Ноги - малый урон
        }
        return damages.get(part_name, 0)

    def check_hit(self, from_point, direction):
        """Проверяет попадание в манекен и возвращает информацию о попадании"""
        if not self.is_active:
            return False, None, 0

        # Создаем луч для проверки попадания
        self.game.picker.setFromLens(self.game.camNode, from_point.x, from_point.y)
        
        if self.game.cQueue.getNumEntries() > 0:
            self.game.cQueue.sortEntries()
            entry = self.game.cQueue.getEntry(0)
            
            hit_node = entry.getIntoNode()
            hit_name = hit_node.getName()
            
            # Получаем точку попадания в мировых координатах
            hit_pos = entry.getSurfacePoint(self.game.render)
            
            # Получаем урон в зависимости от части тела
            damage = self.get_damage_for_part(hit_name)
            
            if damage > 0:  # Если попали в валидную часть тела
                self.take_damage(damage)
                return True, hit_pos, damage
                
        return False, None, 0
