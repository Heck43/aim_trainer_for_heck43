from panda3d.core import Point3, Vec3, NodePath, CollisionNode, CollisionBox, CollisionSphere, BitMask32
from panda3d.core import TextureStage, Texture, CardMaker
import random
import os
import sys
import threading

class Target:
    texture_cache = {}
    category_loaded = False
    current_category = None
    images_cache = {}
    
    TARGET_TEXTURES = []

    @staticmethod
    def get_images_from_category(category):
        """Упрощенная загрузка изображений из категории с кэшированием"""
        if category in Target.images_cache:
            return Target.images_cache[category]
        
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            # Проверяем _internal папку (one-folder mode)
            internal_dir = os.path.join(exe_dir, '_internal')
            if os.path.exists(internal_dir):
                base_path = internal_dir
            elif hasattr(sys, '_MEIPASS'):
                # one-file mode
                base_path = sys._MEIPASS
            else:
                base_path = exe_dir
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        category_rel_path = os.path.join('images', 'nsfw', category)
        category_full_path = os.path.join(base_path, category_rel_path)
        
        if not os.path.exists(category_full_path):
            print(f"⚠️ Папка не найдена: {category_full_path}")
            Target.images_cache[category] = []
            return []
        
        valid_extensions = ('.png', '.jpg', '.jpeg')
        images = []
        
        try:
            for file in os.listdir(category_full_path):
                if file.lower().endswith(valid_extensions):
                    relative_path = os.path.join(category_rel_path, file).replace('\\', '/')
                    images.append(relative_path)
            
            print(f"✅ Загружено {len(images)} изображений из категории '{category}'")
        except Exception as e:
            print(f"❌ Ошибка при чтении папки {category_full_path}: {e}")
        
        Target.images_cache[category] = images
        return images

    @staticmethod
    def preload_category(game, category):
        """Предварительно загружает все текстуры из категории"""
        if Target.current_category == category and Target.category_loaded:
            return

        Target.category_loaded = False
        Target.current_category = category
        
        Target.texture_cache.clear()
        
        category_images = Target.get_images_from_category(category)
        for image_path in category_images:
            try:
                normalized_path = image_path.replace('\\', '/')
                tex = game.loader.loadTexture(normalized_path)
                if tex:
                    Target.texture_cache[normalized_path] = tex
            except Exception as e:
                print(f"⚠️ Ошибка предзагрузки текстуры {image_path}: {e}")
        
        Target.category_loaded = True
        print(f"✅ Предзагружено {len(Target.texture_cache)} текстур для категории '{category}'")

    @staticmethod
    def load_texture(texture_path):
        """Загружает текстуру с использованием кэша"""
        normalized_path = texture_path.replace('\\', '/')
        
        if normalized_path in Target.texture_cache:
            return Target.texture_cache[normalized_path]
        
        try:
            tex = self.game.loader.loadTexture(normalized_path)
            if tex:
                Target.texture_cache[normalized_path] = tex
                return tex
        except Exception as e:
            print(f"❌ Ошибка загрузки текстуры {normalized_path}: {e}")
        return None

    def __init__(self, game, pos=None, pooled=False):
        self.game = game
        self.position = pos if pos else Point3(0, 0, 0)
        self.max_hp = 100
        self.current_hp = self.max_hp
        self.is_active = True
        self.pooled = pooled
        self.texture_path = None
        
        show_images = self.game.settings.get('show_target_images', True)
        if show_images:
            category = self.game.settings.get('nsfw_category', 'furry')
            if not Target.category_loaded or Target.current_category != category:
                Target.preload_category(game, category)
            
            category_images = self.get_images_from_category(category)
            if category_images:
                self.texture_path = random.choice(category_images)
                
        self.create_model()
        self.update_visibility()

    def update_visibility(self):
        """Обновляет видимость манекена в зависимости от настроек"""
        show_images = self.game.settings.get('show_target_images', True)
        
        if show_images:
            if hasattr(self, 'visual'):
                self.visual.show()
                self.visual.setTransparency(1)
                self.visual.setColor(1, 1, 1, 1)
            
            for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
                np.hide()
        else:
            if hasattr(self, 'visual'):
                self.visual.hide()
            
            for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
                np.show()
                np.setColor(0.8, 0.2, 0.2, 1)
                np.setTransparency(1)
                np.setBin("transparent", 0)
                np.setDepthWrite(True)

    def create_model(self):
        self.model = NodePath("target_root")
        self.model.setPos(self.position)
        self.model.reparentTo(self.game.render)
        
        cm = CardMaker('card')
        cm.setFrame(-0.8, 0.8, 0, 3.0)
        self.visual = self.model.attachNewNode(cm.generate())
        
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
        
        head_node = CollisionNode('target_head')
        head_sphere = CollisionSphere(0, 0, 2.6, 0.6)
        head_node.addSolid(head_sphere)
        head_node.setIntoCollideMask(BitMask32.bit(1))
        self.head_np = self.model.attachNewNode(head_node)
        
        body_node = CollisionNode('target_body')
        body_box = CollisionBox(Point3(0, 0, 1.5), 0.7, 0.4, 0.6)
        body_node.addSolid(body_box)
        body_node.setIntoCollideMask(BitMask32.bit(1))
        self.body_np = self.model.attachNewNode(body_node)
        
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
        
        legs_node = CollisionNode('target_legs')
        legs_box = CollisionBox(Point3(0, 0, 0.6), 0.7, 0.4, 1.0)
        legs_node.addSolid(legs_box)
        legs_node.setIntoCollideMask(BitMask32.bit(1))
        self.legs_np = self.model.attachNewNode(legs_node)
        
        self.update_visibility()
        
        self.model.lookAt(0, 0, 0)
        self.model.setH(self.model.getH() + 180)

    def activate(self):
        """Активирует цель из пула (показывает, включает коллизии, новая позиция)"""
        self.is_active = True
        self.current_hp = self.max_hp
        
        if hasattr(self, 'model'):
            self.model.show()
        
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            if np.node().isOfType(CollisionNode.getClassType()):
                np.node().setIntoCollideMask(BitMask32.bit(1))
        
        self.reset_position()
        
        self.reset_texture()
        
        self.update_visibility()
    
    def deactivate(self):
        """Деактивирует цель (скрывает, выключает коллизии)"""
        self.is_active = False
        
        if hasattr(self, 'model'):
            self.model.hide()
        
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            if np.node().isOfType(CollisionNode.getClassType()):
                np.node().setIntoCollideMask(BitMask32.allOff())
    
    def reset_position(self):
        """Устанавливает новую случайную позицию"""
        min_distance = 15
        max_distance = 35
        arena_width = 30
        
        x = random.uniform(-arena_width/2, arena_width/2)
        y = random.uniform(min_distance, max_distance)
        z = 1
        
        self.position = Point3(x, y, z)
        if hasattr(self, 'model'):
            self.model.setPos(self.position)
            self.model.lookAt(0, 0, 0)
            self.model.setH(self.model.getH() + 180)
    
    def reset_texture(self):
        """Устанавливает новую случайную текстуру"""
        show_images = self.game.settings.get('show_target_images', True)
        if show_images:
            category = self.game.settings.get('nsfw_category', 'furry')
            
            if not Target.category_loaded or Target.current_category != category:
                Target.preload_category(self.game, category)
            
            category_images = self.get_images_from_category(category)
            if category_images:
                self.texture_path = random.choice(category_images)
                if hasattr(self, 'visual') and self.texture_path:
                    tex = self.load_texture(self.texture_path)
                    if tex:
                        self.visual.setTexture(tex)
        else:
            self.texture_path = None
    
    def destroy(self):
        """Уничтожает цель (возвращает в пул или реально уничтожает)"""
        if self.pooled and hasattr(self.game, 'target_pool'):
            self.game.target_pool.release(self)
        else:
            self.real_destroy()
    
    def real_destroy(self):
        """Реально уничтожает цель (удаляет из памяти)"""
        if hasattr(self, 'model') and self.model:
            self.model.removeNode()

    def respawn(self):
        self.is_active = False
        self.visual.hide()
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            np.hide()
        self.disable_collisions()
        
        taskMgr.doMethodLater(3.0, self.restore_target, 'restore_target')

    def restore_target(self, task):
        self.current_hp = self.max_hp
        self.is_active = True
        
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
            'target_head': 100,
            'target_body': 60,
            'target_left_arm': 40,
            'target_right_arm': 40,
            'target_legs': 40
        }
        return damages.get(part_name, 0)

    def check_hit(self, from_point, direction):
        """Проверяет попадание в манекен и возвращает информацию о попадании"""
        if not self.is_active:
            return False, None, 0

        self.game.picker.setFromLens(self.game.camNode, from_point.x, from_point.y)
        
        if self.game.cQueue.getNumEntries() > 0:
            self.game.cQueue.sortEntries()
            entry = self.game.cQueue.getEntry(0)
            
            hit_node = entry.getIntoNode()
            hit_name = hit_node.getName()
            
            hit_pos = entry.getSurfacePoint(self.game.render)
            
            damage = self.get_damage_for_part(hit_name)
            
            if damage > 0:
                self.take_damage(damage)
                return True, hit_pos, damage
                
        return False, None, 0
