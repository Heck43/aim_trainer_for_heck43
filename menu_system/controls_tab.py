"""
Вкладка настроек управления
"""
from .base_tab import BaseTab
from .ui_helpers import create_label, create_slider

class ControlsTab(BaseTab):
    """Вкладка с настройками управления"""
    
    def __init__(self, game, parent):
        super().__init__(game, parent)
        self.current_sensitivity = game.settings.get('sensitivity', game.DEFAULT_SETTINGS['sensitivity'])
        self.create_ui()
    
    def create_ui(self):
        """Создает UI элементы вкладки"""
        # Mouse Sensitivity
        sensitivity_label = create_label(
            "Mouse Sensitivity",
            pos=(-0.75, 0, 0.3),
            parent=self.frame
        )
        self.elements.append(sensitivity_label)
        
        self.sensitivity_slider = create_slider(
            range=(0.1, 300.0),  # увеличил максимум до 300
            value=self.current_sensitivity,
            pos=(0.25, 0, 0.3),
            command=self.update_sensitivity,
            parent=self.frame
        )
        self.elements.append(self.sensitivity_slider)
    
    def update_sensitivity(self):
        """Обновляет чувствительность мыши"""
        value = self.sensitivity_slider['value']
        self.game.mouse_sensitivity = value
        self.game.settings_manager.save_settings()
