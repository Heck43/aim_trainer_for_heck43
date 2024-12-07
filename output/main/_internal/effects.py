from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3, Vec3, Vec4, TransparencyAttrib, CardMaker, TextNode, Texture, TextureStage
import random
import math
from direct.task import Task

class SnowEffect:
    def __init__(self, base: ShowBase):
        self.base = base
        self.snowflakes = []
        self.active = False
        
        # Загружаем текстуру снежинки
        self.snowflake_texture = self.base.loader.loadTexture("models/snowflake.png")
        self.snowflake_texture.setMagfilter(Texture.FTLinear)
        self.snowflake_texture.setMinfilter(Texture.FTLinearMipmapLinear)
        
        self.setup_snow()
    
    def setup_snow(self):
        # Create snowflakes
        for _ in range(100):  # Number of snowflakes
            # Create a snowflake using CardMaker
            cm = CardMaker('snowflake')
            cm.setFrame(-0.02, 0.02, -0.02, 0.02)  # Увеличили размер в два раза
            snowflake = self.base.render2d.attachNewNode(cm.generate())
            
            # Применяем текстуру
            snowflake.setTexture(self.snowflake_texture)
            snowflake.setTransparency(TransparencyAttrib.MAlpha)
            snowflake.setColor(1, 1, 1, 0.8)  # White, slightly transparent
            
            # Random starting position at the top
            x = random.uniform(-1.5, 1.5)
            z = random.uniform(1.0, 1.5)
            snowflake.setPos(x, 0, z)
            
            # Добавляем случайное вращение
            snowflake.setR(random.uniform(0, 360))
            
            # Store snowflake data
            self.snowflakes.append({
                'node': snowflake,
                'speed': random.uniform(0.2, 0.5),
                'wobble': random.uniform(-0.2, 0.2),
                'wobble_speed': random.uniform(1.0, 2.0),
                'rotation_speed': random.uniform(-30, 30)  # Скорость вращения
            })
            
            snowflake.hide()  # Hide initially
    
    def update(self, task):
        if not self.active:
            return task.done
            
        dt = globalClock.getDt()
        
        for flake in self.snowflakes:
            node = flake['node']
            pos = node.getPos()
            
            # Update position
            new_z = pos[2] - flake['speed'] * dt
            new_x = pos[0] + flake['wobble'] * math.sin(task.time * flake['wobble_speed'])
            
            # Reset if below screen
            if new_z < -1.0:
                new_z = random.uniform(1.0, 1.5)
                new_x = random.uniform(-1.5, 1.5)
            
            node.setPos(new_x, 0, new_z)
            
            # Обновляем вращение
            current_r = node.getR()
            node.setR(current_r + flake['rotation_speed'] * dt)
            
        return task.cont
    
    def start(self):
        if not self.active:
            self.active = True
            for flake in self.snowflakes:
                flake['node'].show()
            self.base.taskMgr.add(self.update, 'snow_update')
    
    def stop(self):
        self.active = False
        for flake in self.snowflakes:
            flake['node'].hide()
        self.base.taskMgr.remove('snow_update')
    
    def cleanup(self):
        self.stop()
        for flake in self.snowflakes:
            flake['node'].removeNode()
        self.snowflakes.clear()

class ChristmasLights:
    def __init__(self, base: ShowBase):
        self.base = base
        self.lights = []
        self.wires = []  # Для хранения "проводов"
        self.setup_lights()
        
    def setup_lights(self):
        colors = [
            Vec4(1, 0, 0, 1),    # Красный
            Vec4(0, 1, 0, 1),    # Зеленый
            Vec4(0, 0.5, 1, 1),  # Голубой
            Vec4(1, 1, 0, 1),    # Желтый
        ]
        
        # Создаем гирлянду сверху
        self.create_garland_segment(-1.4, 1.0, 16, colors, wave_amplitude=0.05)
        # Создаем гирлянду снизу
        self.create_garland_segment(-1.4, -1.0, 16, colors, wave_amplitude=-0.05)
        
    def create_garland_segment(self, start_x, start_z, num_lights, colors, wave_amplitude):
        # Сначала создаем основной "провод"
        spacing = 2.8 / (num_lights - 1)  # Увеличенное расстояние между лампочками
        
        # Создаем основной провод
        cm = CardMaker('main_wire')
        cm.setFrame(0, 1, -0.002, 0.002)  # Увеличенная толщина провода
        main_wire = self.base.render2d.attachNewNode(cm.generate())
        
        # Устанавливаем размер и позицию основного провода
        main_wire.setPos(start_x, 0, start_z)
        main_wire.setScale(2.8, 1, 1)  # Увеличенная длина
        main_wire.setColor(0.2, 0.2, 0.2, 0.5)
        main_wire.setTransparency(TransparencyAttrib.MAlpha)
        self.wires.append(main_wire)
        
        for i in range(num_lights):
            # Позиция лампочки
            x = start_x + i * spacing
            # Добавляем волнообразное смещение
            z = start_z + math.sin(i * 0.5) * wave_amplitude
            
            # Создаем лампочку
            cm = CardMaker(f'light_{len(self.lights)}')
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # Увеличенный размер фрейма лампочки
            light = self.base.render2d.attachNewNode(cm.generate())
            
            light.setScale(0.035)  # Значительно увеличенный размер лампочек
            light.setPos(x, 0, z)
            light.setColor(random.choice(colors))
            light.setTransparency(TransparencyAttrib.MAlpha)
            
            # Создаем "ножку" лампочки (маленький вертикальный провод)
            stem = self.base.render2d.attachNewNode(CardMaker('stem').generate())
            stem.setScale(0.002, 1, abs(z - start_z))  # Увеличенная толщина провода
            stem.setPos(x, 0, min(z, start_z))
            stem.setColor(0.2, 0.2, 0.2, 0.5)
            stem.setTransparency(TransparencyAttrib.MAlpha)
            self.wires.append(stem)
            
            # Создаем эффект свечения
            glow = self.base.render2d.attachNewNode(cm.generate())
            glow.setScale(0.07)  # Увеличенное свечение
            glow.setPos(x, 0, z)
            glow.setColor(light.getColor() * 0.5)
            glow.setTransparency(TransparencyAttrib.MAlpha)
            glow.setAlphaScale(0.3)
            
            self.lights.extend([light, glow])
            
            # Добавляем мерцание
            def flicker(task, light=light, glow=glow):
                time = task.time
                # Более плавное мерцание
                flicker = 0.7 + 0.3 * math.sin(time * 2.0 + hash(str(light)) % 10)
                light.setAlphaScale(flicker)
                glow.setAlphaScale(flicker * 0.3)
                return task.cont
            
            self.base.taskMgr.add(flicker, f'flicker_light_{len(self.lights)}')
    
    def cleanup(self):
        # Удаляем все лампочки и их задачи
        for i, light in enumerate(self.lights):
            if i % 2 == 0:  # Только для основных лампочек (не для свечения)
                self.base.taskMgr.remove(f'flicker_light_{i}')
            light.removeNode()
        self.lights.clear()
        
        # Удаляем все провода
        for wire in self.wires:
            wire.removeNode()
        self.wires.clear()
