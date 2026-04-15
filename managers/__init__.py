# managers/__init__.py
"""
Manager modules for the aim trainer game.
Separates concerns into modular components.
"""

from managers.settings_manager import SettingsManager
from managers.weapons_manager import WeaponsManager
from managers.effects_manager import EffectsManager
from managers.movement_manager import MovementManager
from managers.killfeed_manager import KillfeedManager
from managers.shell_manager import ShellManager
from managers.shader_debug_ui import ShaderDebugUI

__all__ = [
    'SettingsManager',
    'WeaponsManager',
    'EffectsManager',
    'MovementManager',
    'KillfeedManager',
    'ShellManager',
    'ShaderDebugUI',
]
