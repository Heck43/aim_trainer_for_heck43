"""
Базовый класс для вкладок настроек
"""
from direct.gui.DirectGui import DirectFrame, DGG

class BaseTab:
    """Базовый класс для всех вкладок настроек"""
    
    def __init__(self, game, parent, pos=(0.25, 0, 0.05)):
        self.game = game
        self.parent = parent
        self.elements = []
        
        # Создаем фрейм для вкладки
        self.frame = DirectFrame(
            frameColor=(0.12, 0.14, 0.17, 0),
            relief=DGG.FLAT,
            pos=pos,
            parent=parent
        )
        self.frame.hide()
    
    def show(self):
        """Показать вкладку"""
        self.frame.show()
    
    def hide(self):
        """Скрыть вкладку"""
        self.frame.hide()
    
    def cleanup(self):
        """Очистить ресурсы вкладки"""
        for element in self.elements:
            if element:
                element.destroy()
        self.elements.clear()
        if self.frame:
            self.frame.destroy()
