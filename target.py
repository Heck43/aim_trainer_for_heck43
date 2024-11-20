from panda3d.core import Point3, Vec3, NodePath, CollisionNode, CollisionBox, CollisionSphere, BitMask32
from panda3d.core import TextureStage, Texture, CardMaker
import random
import os

class Target:
    # Список путей к текстурам
    TARGET_TEXTURES = [
        'images/target1.png',
        'images/target2.jpg',
        'images/target3.png',
        'images/target4.jpg',
        'images/target5.png'
    ]

    def __init__(self, game, pos):
        self.game = game
        self.position = pos
        self.max_hp = 100
        self.current_hp = self.max_hp
        self.is_active = True
        
        # Выбираем случайную текстуру
        self.texture_path = random.choice(self.TARGET_TEXTURES)
        
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
        
        # Load and apply texture
        if os.path.exists(self.texture_path):
            tex = self.game.loader.loadTexture(self.texture_path)
            self.visual.setTexture(tex)
            self.visual.setTransparency(1)  # 1 = M_alpha
            self.visual.setBin("transparent", 0)
            self.visual.setDepthWrite(False)
            
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
        
        # Выбираем новую случайную текстуру
        self.texture_path = random.choice(self.TARGET_TEXTURES)
        if os.path.exists(self.texture_path):
            tex = self.game.loader.loadTexture(self.texture_path)
            self.visual.setTexture(tex)
            # Настраиваем правильную прозрачность
            self.visual.setTransparency(1)  # 1 = M_alpha
            self.visual.setBin("transparent", 0)
            self.visual.setDepthWrite(False)
        
        # Показываем все части и включаем коллизии
        self.visual.show()
        for np in [self.head_np, self.body_np, self.left_arm_np, self.right_arm_np, self.legs_np]:
            np.show()
        self.enable_collisions()
        
        self.update_visibility()  # Обновляем видимость после респавна
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
