# managers/settings_manager.py
import json
import os
import sys

class SettingsManager:
    """Manages game settings loading, saving, and validation"""

    DEFAULT_SETTINGS = {
        'sensitivity': 50.0,
        'fov': 70,
        'resolution': '1280x720',
        'fullscreen': True,
        'show_score': True,
        'show_timer': True,
        'volume': 100,
        'show_target_images': False,
        'damage_numbers': True,
        'killfeed': True,
        'show_fps': True,
        'recoil_enabled': True,
        'weapon_position': {
            'x': 0.25,
            'y': 0.6,
            'z': -0.3
        },
        'bhop_enabled': True,
        'audio': {
            'music_enabled': True,
            'music_volume': 0.5,
            'current_track': 'kiss_me_again.mp3'
        },
        'target_count': 10,
        'bullet_traces': True,
        'spread_enabled': True,
        'show_hitbox_debug': False,
    }

    def __init__(self, game):
        self.game = game
        self.settings = self.load_settings()

    def _get_settings_path(self):
        """Returns path to settings.json (works with PyInstaller)"""
        if hasattr(sys, 'frozen'):
            # In PyInstaller - save next to exe
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            return os.path.join(exe_dir, 'settings.json')
        else:
            # In normal mode - in project root
            return 'settings.json'

    def validate_settings(self, settings):
        """Validates and normalizes settings"""
        if 'fov' in settings:
            settings['fov'] = max(60, min(120, settings['fov']))

        if 'resolution' in settings:
            try:
                width, height = map(int, settings['resolution'].split('x'))
                if width < 640 or height < 480:
                    settings['resolution'] = '1280x720'
            except:
                settings['resolution'] = '1280x720'

        # Remove deprecated shader settings
        for key in [
            'bloom_enabled', 'bloom_intensity',
            'blur_enabled', 'blur_amount',
            'cartoon_enabled', 'inverted_enabled',
            'ao_enabled',
            'motion_blur_enabled', 'motion_blur_amount',
        ]:
            settings.pop(key, None)

        # Ensure boolean keys are actually booleans
        bool_keys = ['show_target_images', 'bhop_enabled', 'fullscreen', 'show_score',
                     'show_timer', 'damage_numbers', 'killfeed', 'show_fps',
                     'recoil_enabled', 'screen_shake_enabled', 'spread_enabled',
                     'show_hitbox_debug']

        for key in bool_keys:
            if key in settings:
                if isinstance(settings[key], int):
                    settings[key] = bool(settings[key])

        return settings

    def load_settings(self):
        """Loads settings from JSON file"""
        settings_path = self._get_settings_path()
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                loaded = self.validate_settings(loaded)
                return loaded
        except Exception as e:
            print(f"⚠️ Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        """Saves current settings to file"""
        # Sync mouse sensitivity if it exists in game
        if hasattr(self.game, 'mouse_sensitivity'):
            self.settings['sensitivity'] = self.game.mouse_sensitivity

        # Remove deprecated shader settings before saving
        for key in [
            'bloom_enabled', 'bloom_intensity',
            'blur_enabled', 'blur_amount',
            'cartoon_enabled', 'inverted_enabled',
            'ao_enabled',
            'motion_blur_enabled', 'motion_blur_amount',
        ]:
            self.settings.pop(key, None)

        settings_path = self._get_settings_path()
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        """Get a setting value with optional default"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Set a setting value"""
        self.settings[key] = value
