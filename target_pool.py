"""
Пул объектов Target для переиспользования
Вместо создания/уничтожения целей каждый раз, берем их из пула
"""

class TargetPool:
    """Пул переиспользуемых целей"""
    
    def __init__(self, game, initial_size=30):
        self.game = game
        self.available = []  # Свободные цели
        self.in_use = []     # Активные цели
        self.initial_size = initial_size
        
        print(f"🎯 Создаем пул из {initial_size} целей...")
        
        # Создаем пул заранее (без импорта здесь, импорт будет в main.py)
        # Цели создаются в методе initialize после того как Target станет доступен
    
    def initialize(self, target_class):
        """Инициализирует пул целями"""
        from target import Target
        
        for i in range(self.initial_size):
            target = Target(self.game, pooled=True)
            target.deactivate()
            self.available.append(target)
        
        print(f"✅ Пул инициализирован: {len(self.available)} целей готовы")
    
    def acquire(self):
        """Берет цель из пула"""
        if self.available:
            target = self.available.pop()
        else:
            # Пул пустой — создаем новую (редкий случай)
            print("⚠️ Пул целей пуст, создаем дополнительную цель")
            from target import Target
            target = Target(self.game, pooled=True)
        
        self.in_use.append(target)
        target.activate()
        return target
    
    def release(self, target):
        """Возвращает цель в пул"""
        if target in self.in_use:
            self.in_use.remove(target)
        
        target.deactivate()
        
        # Проверяем, не слишком ли много целей в пуле
        if len(self.available) < self.initial_size * 2:
            self.available.append(target)
        else:
            # Если пул разросся, реально уничтожаем лишние цели
            target.real_destroy()
    
    def release_all(self):
        """Возвращает все цели в пул"""
        for target in self.in_use[:]:
            self.release(target)
    
    def refresh_all_active(self):
        """Обновляет видимость всех активных целей (при смене настроек NSFW/SFW)"""
        for target in self.in_use:
            if hasattr(target, 'reset_texture'):
                target.reset_texture()
            if hasattr(target, 'update_visibility'):
                target.update_visibility()
        
        print(f"🔄 Обновлено {len(self.in_use)} активных целей")
    
    def get_stats(self):
        """Возвращает статистику пула"""
        return {
            'available': len(self.available),
            'in_use': len(self.in_use),
            'total': len(self.available) + len(self.in_use)
        }
    
    def cleanup(self):
        """Очищает весь пул"""
        # Возвращаем все активные цели
        self.release_all()
        
        # Уничтожаем все цели в пуле
        for target in self.available:
            target.real_destroy()
        
        self.available.clear()
        self.in_use.clear()
        
        print("🗑️ Пул целей очищен")

