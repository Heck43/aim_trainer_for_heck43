from panda3d.core import AudioSound


class AudioManager:
    """Управляет фоновой музыкой и аудио настройками"""

    def __init__(self, game):
        self.game = game
        self.music = None
        self.current_music_path = None
        self.weapon_sounds = {}

    def setup_audio(self):
        """Настраивает и запускает фоновую музыку"""
        audio_settings = self.game.settings.get('audio', self.game.DEFAULT_SETTINGS['audio'])

        if audio_settings['music_enabled']:
            self.play_music(audio_settings['current_track'], audio_settings['music_volume'])

    def preload_weapon_sounds(self):
        """Предзагружает звуки оружия для оптимизации"""
        self.weapon_sounds = {}
        for weapon_name, weapon_data in self.game.weapons.items():
            sound_path = weapon_data.get("sound")
            if sound_path:
                try:
                    self.weapon_sounds[weapon_name] = self.game.loader.loadSfx(sound_path)
                except Exception as e:
                    print(f"Ошибка загрузки звука {weapon_name}: {e}")

    def play_music(self, track_name, volume=0.5):
        """Воспроизводит фоновую музыку с указанным объемом"""
        if self.game.is_splash_screen_active:
            return

        if self.music:
            self.music.stop()

        music_path = f"music/{track_name}"

        try:
            self.music = self.game.loader.loadSfx(music_path)
            if self.music:
                self.music.setLoop(True)
                self.music.setVolume(volume)
                self.music.play()
                self.current_music_path = music_path
        except Exception as e:
            print(f"Ошибка загрузки музыки: {e}")

    def update_music_volume(self, volume):
        """Обновляет объем текущей воспроизводимой музыки"""
        if self.music:
            self.music.setVolume(volume)

        if 'audio' not in self.game.settings:
            self.game.settings['audio'] = self.game.DEFAULT_SETTINGS['audio'].copy()
        self.game.settings['audio']['music_volume'] = volume
        self.game.settings_manager.save_settings()

    def change_music_track(self, track_name):
        """Изменяет текущий трек музыки"""
        if 'audio' not in self.game.settings:
            self.game.settings['audio'] = self.game.DEFAULT_SETTINGS['audio'].copy()

        self.game.settings['audio']['current_track'] = track_name
        self.game.settings_manager.save_settings()

        if self.game.settings['audio']['music_enabled']:
            self.play_music(track_name, self.game.settings['audio']['music_volume'])

    def toggle_music(self, enabled):
        """Включает/выключает фоновую музыку"""
        if 'audio' not in self.game.settings:
            self.game.settings['audio'] = self.game.DEFAULT_SETTINGS['audio'].copy()

        self.game.settings['audio']['music_enabled'] = enabled
        self.game.settings_manager.save_settings()

        if enabled:
            self.play_music(self.game.settings['audio']['current_track'], self.game.settings['audio']['music_volume'])
        elif self.music:
            self.music.stop()
