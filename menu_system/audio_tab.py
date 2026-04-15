"""
Вкладка аудио настроек
"""
from direct.gui.DirectGui import DirectOptionMenu, DGG
import os
import sys
from .base_tab import BaseTab
from .ui_helpers import create_label, create_checkbox, create_slider

class AudioTab(BaseTab):
    """Вкладка с аудио настройками"""
    
    def __init__(self, game, parent):
        super().__init__(game, parent)
        self.available_tracks = self.get_available_tracks()
        self.create_ui()
    
    def get_available_tracks(self):
        """Получает список доступных треков"""
        try:
            music_dir = "music"
            if hasattr(sys, '_MEIPASS'):
                music_dir = os.path.join(os.path.dirname(sys.executable), 'music')
            
            if os.path.exists(music_dir):
                tracks = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
                if tracks:
                    return tracks

            return ['gunslinger.mp3', 'kill_you_family.mp3', 'kiss_me_again.mp3', 'genshin_enpack.mp3', 'macks_bolev.mp3']
        except Exception as e:
            print(f"Ошибка получения списка треков: {e}")
            return ['gunslinger.mp3']
    
    def create_ui(self):
        """Создает UI элементы вкладки"""
        # Music Enable/Disable
        music_enabled_label = create_label("Background Music", pos=(-0.6, 0, 0.3), parent=self.frame)
        self.elements.append(music_enabled_label)
        
        self.music_enabled_checkbox = create_checkbox(
            "Enable",
            pos=(-0.1, 0, 0.3),
            command=self.toggle_music,
            parent=self.frame
        )
        self.music_enabled_checkbox['indicatorValue'] = self.game.settings.get('audio', {}).get('music_enabled', True)
        self.elements.append(self.music_enabled_checkbox)
        
        # Volume Control
        volume_label = create_label("Music Volume", pos=(-0.6, 0, 0.15), parent=self.frame)
        self.elements.append(volume_label)
        
        self.volume_slider = create_slider(
            range=(0, 1.0),
            value=self.game.settings.get('audio', {}).get('music_volume', 0.5),
            pos=(0.2, 0, 0.15),
            command=self.update_music_volume,
            parent=self.frame
        )
        self.elements.append(self.volume_slider)
        
        # Track Selection
        track_label = create_label("Music Track", pos=(-0.6, 0, 0.0), parent=self.frame)
        self.elements.append(track_label)
        
        current_track = self.game.settings.get('audio', {}).get('current_track', 'default_track.mp3')
        
        self.track_menu = DirectOptionMenu(
            text="Track",
            scale=0.05,
            pos=(0.2, 0, 0.0),
            items=self.available_tracks,
            initialitem=self.available_tracks.index(current_track) if current_track in self.available_tracks else 0,
            command=self.change_music_track,
            parent=self.frame,
            frameColor=(0.18, 0.2, 0.25, 0.9),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            text_fg=(0.9, 0.9, 0.9, 1),
            item_frameColor=(0.16, 0.18, 0.21, 0.95),
            popupMenu_frameColor=(0.16, 0.18, 0.21, 0.95),
            item_relief=DGG.FLAT,
            popupMenu_relief=DGG.FLAT
        )
        self.elements.append(self.track_menu)
    
    def toggle_music(self, enabled):
        """Переключает музыку"""
        self.game.audio_manager.toggle_music(enabled)

    def update_music_volume(self):
        """Обновляет громкость музыки"""
        volume = self.volume_slider['value']
        self.game.audio_manager.update_music_volume(volume)

    def change_music_track(self, track_name):
        """Меняет трек"""
        self.game.audio_manager.change_music_track(track_name)
