"""
Вкладка игровых настроек
"""
from direct.gui.DirectGui import DirectOptionMenu, DGG
from .base_tab import BaseTab
from .ui_helpers import create_label, create_checkbox

class GameTab(BaseTab):
    """Вкладка с игровыми настройками"""
    
    def __init__(self, game, parent):
        super().__init__(game, parent)
        self.create_ui()
    
    def create_ui(self):
        """Создает UI элементы вкладки"""
        # Bunny Hop
        bhop_label = create_label("Bunny Hop", pos=(-0.6, 0, 0.3), parent=self.frame)
        self.elements.append(bhop_label)
        
        self.bhop_checkbox = create_checkbox(
            "Enable",
            pos=(-0.1, 0, 0.3),
            command=self.toggle_bhop,
            parent=self.frame
        )
        self.bhop_checkbox['indicatorValue'] = self.game.settings.get('bhop_enabled', True)
        self.elements.append(self.bhop_checkbox)
        
        # Recoil
        recoil_label = create_label("Recoil", pos=(-0.6, 0, 0.2), parent=self.frame)
        self.elements.append(recoil_label)
        
        self.recoil_checkbox = create_checkbox(
            "Enable",
            pos=(-0.1, 0, 0.2),
            command=self.toggle_recoil,
            parent=self.frame
        )
        self.recoil_checkbox['indicatorValue'] = self.game.settings.get('recoil_enabled', True)
        self.elements.append(self.recoil_checkbox)
        
        # Spread
        spread_label = create_label("Spread", pos=(-0.6, 0, 0.1), parent=self.frame)
        self.elements.append(spread_label)
        
        self.spread_checkbox = create_checkbox(
            "Enable",
            pos=(-0.1, 0, 0.1),
            command=self.toggle_spread,
            parent=self.frame
        )
        self.spread_checkbox['indicatorValue'] = self.game.settings.get('spread_enabled', True)
        self.elements.append(self.spread_checkbox)
        
        # Target Count
        target_count_label = create_label("Target Count", pos=(-0.6, 0, 0), parent=self.frame)
        self.elements.append(target_count_label)
        
        self.target_count_options = ["5", "10", "15", "20", "25", "30"]
        current_target_count = str(self.game.settings.get('target_count', 10))
        
        self.target_count_menu = DirectOptionMenu(
            text="",
            text_scale=0.05,
            scale=0.1,
            items=self.target_count_options,
            initialitem=self.target_count_options.index(current_target_count) if current_target_count in self.target_count_options else 1,
            highlightColor=(0.65, 0.65, 0.65, 1),
            parent=self.frame,
            pos=(0.0, 0, 0),
            command=self.set_target_count,
            frameColor=(0.18, 0.2, 0.25, 0.9),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            text_fg=(0.9, 0.9, 0.9, 1),
            item_frameColor=(0.16, 0.18, 0.21, 0.95),
            popupMenu_frameColor=(0.16, 0.18, 0.21, 0.95),
            item_relief=DGG.FLAT,
            popupMenu_relief=DGG.FLAT
        )
        self.elements.append(self.target_count_menu)
    
    def toggle_bhop(self, status):
        """Переключает bunny hop"""
        self.game.settings['bhop_enabled'] = status
        self.game.save_settings()
    
    def toggle_recoil(self, status):
        """Переключает отдачу"""
        self.game.settings['recoil_enabled'] = status
        self.game.save_settings()
    
    def toggle_spread(self, status):
        """Переключает разброс"""
        self.game.settings['spread_enabled'] = status
        self.game.save_settings()
    
    def set_target_count(self, count):
        """Устанавливает количество манекенов"""
        self.game.settings['target_count'] = int(count)
        self.game.save_settings()
