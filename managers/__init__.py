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
from managers.imgui_patches import apply_imgui_patches
from managers.visual_markers import VisualMarkersManager
from managers.collision_manager import CollisionManager
from managers.multiplayer_manager import MultiplayerManager
from managers.game import Game

__all__ = [
    'SettingsManager',
    'WeaponsManager',
    'EffectsManager',
    'MovementManager',
    'KillfeedManager',
    'ShellManager',
    'ShaderDebugUI',
    'apply_imgui_patches',
    'VisualMarkersManager',
    'CollisionManager',
    'MultiplayerManager',
    'Game',
]
