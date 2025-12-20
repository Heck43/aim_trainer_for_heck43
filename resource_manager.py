"""
Единый менеджер ресурсов с кешированием
Загружает и хранит текстуры, звуки, модели для быстрого доступа
"""
import os
import sys

class ResourceManager:
    """Менеджер ресурсов с кешированием и прогрессом загрузки"""
    
    def __init__(self, game):
        self.game = game
        self.textures = {}      # Кеш текстур
        self.sounds = {}        # Кеш звуков
        self.models = {}        # Кеш моделей
        
        self.total_resources = 0
        self.loaded_resources = 0
        self.on_progress = None  # Callback для прогресс-бара
    
    def preload_all(self, on_progress=None):
        """Загружает все критические ресурсы с прогрессом"""
        self.on_progress = on_progress
        
        # Список всех ресурсов для предзагрузки
        resources = []
        
        # Модели
        resources.append(('model', 'models/map.glb'))
        resources.append(('model', 'models/weapon.glb'))
        
        # Звуки
        sound_files = [
            'sounds/pistol_shot.wav',
            'sounds/rifle_shot.wav',
            'sounds/sniper_shot.wav',
            'sounds/ui_click.wav',
            'sounds/ui_hover.wav'
        ]
        for sound in sound_files:
            resources.append(('sound', sound))
        
        # NSFW текстуры (текущая категория)
        current_category = self.game.settings.get('nsfw_category', 'furry')
        nsfw_images = self.get_nsfw_images(current_category)
        for img_path in nsfw_images:
            resources.append(('texture', img_path))
        
        self.total_resources = len(resources)
        
        # Загружаем каждый ресурс
        for i, (res_type, path) in enumerate(resources):
            try:
                if res_type == 'model':
                    self.load_model(path)
                elif res_type == 'sound':
                    self.load_sound(path)
                elif res_type == 'texture':
                    self.load_texture(path)
                
                self.loaded_resources = i + 1
                
                # Обновляем прогресс
                if self.on_progress:
                    progress = self.loaded_resources / max(self.total_resources, 1)
                    filename = os.path.basename(path)
                    self.on_progress(progress, filename)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки {path}: {e}")
                self.loaded_resources = i + 1
    
    def get_nsfw_images(self, category):
        """Получает список NSFW изображений для категории"""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        category_rel_path = os.path.join('images', 'nsfw', category)
        category_full_path = os.path.join(base_path, category_rel_path)
        
        if not os.path.exists(category_full_path):
            return []
        
        valid_extensions = ('.png', '.jpg', '.jpeg')
        images = []
        
        try:
            for file in os.listdir(category_full_path):
                if file.lower().endswith(valid_extensions):
                    rel_path = os.path.join(category_rel_path, file).replace('\\', '/')
                    images.append(rel_path)
        except Exception as e:
            print(f"❌ Ошибка чтения директории {category_full_path}: {e}")
        
        return images
    
    def load_texture(self, path):
        """Загружает текстуру и сохраняет в кеш"""
        if path in self.textures:
            return self.textures[path]
        
        try:
            tex = self.game.loader.loadTexture(path)
            if tex:
                self.textures[path] = tex
                return tex
        except Exception as e:
            print(f"❌ Ошибка загрузки текстуры {path}: {e}")
        
        return None
    
    def load_sound(self, path):
        """Загружает звук и сохраняет в кеш"""
        if path in self.sounds:
            return self.sounds[path]
        
        try:
            sound = self.game.loader.loadSfx(path)
            if sound:
                self.sounds[path] = sound
                return sound
        except Exception as e:
            print(f"❌ Ошибка загрузки звука {path}: {e}")
        
        return None
    
    def load_model(self, path):
        """Загружает модель и сохраняет в кеш"""
        if path in self.models:
            # Возвращаем копию модели
            return self.models[path].copyTo(self.game.render)
        
        try:
            model = self.game.loader.loadModel(path)
            if model:
                self.models[path] = model
                # Возвращаем копию для использования
                return model.copyTo(self.game.render)
        except Exception as e:
            print(f"❌ Ошибка загрузки модели {path}: {e}")
        
        return None
    
    def get_texture(self, path):
        """Получает текстуру из кеша или загружает"""
        return self.textures.get(path) or self.load_texture(path)
    
    def get_sound(self, path):
        """Получает звук из кеша или загружает"""
        return self.sounds.get(path) or self.load_sound(path)
    
    def get_model(self, path):
        """Получает копию модели из кеша или загружает"""
        return self.load_model(path)
    
    def clear_cache(self):
        """Очищает весь кеш"""
        self.textures.clear()
        self.sounds.clear()
        self.models.clear()
    
    def get_cache_stats(self):
        """Возвращает статистику кеша"""
        return {
            'textures': len(self.textures),
            'sounds': len(self.sounds),
            'models': len(self.models),
            'total': len(self.textures) + len(self.sounds) + len(self.models)
        }

