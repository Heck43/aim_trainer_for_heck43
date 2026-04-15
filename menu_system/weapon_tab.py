"""
Вкладка настроек оружия
"""
from direct.gui.DirectGui import DirectButton, DGG
from .base_tab import BaseTab
from .ui_helpers import create_label, create_slider

class WeaponTab(BaseTab):
    """Вкладка с настройками оружия"""
    
    def __init__(self, game, parent):
        super().__init__(game, parent)
        self.create_ui()
    
    def create_ui(self):
        """Создает UI элементы вкладки"""
        # Weapon Position Title
        weapon_pos_label = create_label(
            "Weapon Position",
            pos=(-0.7, 0, 0.3),
            parent=self.frame
        )
        self.elements.append(weapon_pos_label)
        
        # X Position
        x_label = create_label("X Position", pos=(-0.7, 0, 0.2), parent=self.frame)
        self.elements.append(x_label)
        
        self.x_slider = create_slider(
            range=(-1.0, 1.0),
            value=self.game.settings.get('weapon_position', {}).get('x', self.game.DEFAULT_SETTINGS['weapon_position']['x']),
            pos=(0.2, 0, 0.2),
            command=self.update_x_position,
            parent=self.frame
        )
        self.elements.append(self.x_slider)
        
        # Y Position
        y_label = create_label("Y Position", pos=(-0.7, 0, 0.1), parent=self.frame)
        self.elements.append(y_label)
        
        self.y_slider = create_slider(
            range=(-1.0, 2.0),
            value=self.game.settings.get('weapon_position', {}).get('y', self.game.DEFAULT_SETTINGS['weapon_position']['y']),
            pos=(0.2, 0, 0.1),
            command=self.update_y_position,
            parent=self.frame
        )
        self.elements.append(self.y_slider)
        
        # Z Position
        z_label = create_label("Z Position", pos=(-0.7, 0, 0.0), parent=self.frame)
        self.elements.append(z_label)
        
        self.z_slider = create_slider(
            range=(-1.0, 1.0),
            value=self.game.settings.get('weapon_position', {}).get('z', self.game.DEFAULT_SETTINGS['weapon_position']['z']),
            pos=(0.2, 0, 0.0),
            command=self.update_z_position,
            parent=self.frame
        )
        self.elements.append(self.z_slider)
        
        # Reset Button
        self.reset_pos_button = DirectButton(
            text="Reset Position",
            command=self.reset_position,
            pos=(0, 0, -0.2),
            parent=self.frame,
            frameColor=(0.2, 0.22, 0.27, 0.9),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            frameSize=(-0.25, 0.25, -0.04, 0.04),
            text_scale=0.045,
            text_fg=(0.9, 0.9, 0.9, 1),
            pressEffect=0
        )
        self.elements.append(self.reset_pos_button)
    
    def update_x_position(self):
        """Обновляет X позицию оружия"""
        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.game.settings['weapon_position']['x'] = self.x_slider['value']
        messenger.send('update_weapon_position')
        self.game.settings_manager.save_settings()
    
    def update_y_position(self):
        """Обновляет Y позицию оружия"""
        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.game.settings['weapon_position']['y'] = self.y_slider['value']
        messenger.send('update_weapon_position')
        self.game.settings_manager.save_settings()
    
    def update_z_position(self):
        """Обновляет Z позицию оружия"""
        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.game.settings['weapon_position']['z'] = self.z_slider['value']
        messenger.send('update_weapon_position')
        self.game.settings_manager.save_settings()
    
    def reset_position(self):
        """Сбрасывает позицию оружия"""
        self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.x_slider['value'] = self.game.settings['weapon_position']['x']
        self.y_slider['value'] = self.game.settings['weapon_position']['y']
        self.z_slider['value'] = self.game.settings['weapon_position']['z']
        
        messenger.send('update_weapon_position')
        self.game.settings_manager.save_settings()
