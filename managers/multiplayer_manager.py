from panda3d.core import Vec3
from multiplayer.client import NetworkClient
from multiplayer.player_model import RemotePlayerModel
from multiplayer.lobby_menu import LobbyMenu

class MultiplayerManager:
    def __init__(self, game):
        self.game = game

    def can_local_multiplayer_act(self):
        if not (self.game.is_multiplayer and self.game.network and self.game.network.is_connected()):
            return True
        return self.game.mp_local_alive

    def reset_multiplayer_motion_state(self):
        self.game.mouse_pressed = False
        self.game.horizontal_velocity = Vec3(0, 0, 0)
        self.game.vertical_velocity = 0.0
        self.game.is_jumping = False
        self.game.jump_speed_boost = 1.0
        self.game.jump_combo_multiplier = 1.0
        self.game.current_combo_jumps = 0
        self.game.recoil_pitch = 0
        self.game.recoil_yaw = 0
        self.game.current_spread = 0.0
        self.game.is_aiming = False
        self.game.can_shoot = True
        self.game.last_shot_time = 0
        self.game.shoot_state_frames = 0
        self.game.prev_camera_heading = self.game.camera_heading
        self.game.prev_camera_pitch = self.game.camera_pitch
        if self.game.combo_task:
            self.game.taskMgr.remove(self.game.combo_task)
            self.game.combo_task = None
        try:
            self.game.taskMgr.remove("reset_shoot")
        except Exception:
            pass

    def sync_local_multiplayer_spawn(self, state):
        pos = state.get("pos")
        if isinstance(pos, (list, tuple)) and len(pos) == 3:
            self.game.camera.setPos(float(pos[0]), float(pos[1]), float(pos[2]))
        self.reset_multiplayer_motion_state()
        self.game.mp_spawn_synced = True

    def update_multiplayer_feedback(self, dt: float):
        if self.game.hud_manager.hurt_flash_alpha > 0.0:
            self.game.hud_manager.hurt_flash_alpha = max(0.0, self.game.hud_manager.hurt_flash_alpha - (2.2 * dt))
            self.game.hud_manager.hurt_flash.setColor(0.85, 0.05, 0.05, self.game.hud_manager.hurt_flash_alpha)
            if self.game.hud_manager.hurt_flash_alpha > 0.0:
                self.game.hud_manager.hurt_flash.show()
            else:
                self.game.hud_manager.hurt_flash.hide()
        else:
            self.game.hud_manager.hurt_flash.hide()

        self.game.hud_manager.update_multiplayer_hud()

    def refresh_hitbox_debug_visibility(self):
        enabled = bool(self.game.settings.get("show_hitbox_debug", False))
        for player_model in self.game.remote_players.values():
            try:
                player_model.set_hitbox_debug_visible(enabled)
            except Exception:
                pass

    def set_hitbox_debug_enabled(self, enabled, save: bool = True):
        enabled = bool(enabled)
        self.game.settings["show_hitbox_debug"] = enabled
        self.refresh_hitbox_debug_visibility()
        if save:
            self.game.settings_manager.save_settings()
        state = "ON" if enabled else "OFF"
        print(f"[Debug] Multiplayer player hitboxes: {state}")

    def toggle_hitbox_debug(self):
        current = bool(self.game.settings.get("show_hitbox_debug", False))
        self.set_hitbox_debug_enabled(not current, save=True)

    def apply_local_multiplayer_state(self, state):
        if not state:
            return

        was_alive = self.game.mp_local_alive
        self.game.mp_local_max_hp = max(1, int(state.get("max_hp", self.game.mp_local_max_hp or 100)))
        self.game.mp_local_hp = max(0, int(state.get("hp", self.game.mp_local_hp)))
        self.game.mp_local_kills = max(0, int(state.get("kills", self.game.mp_local_kills)))
        self.game.mp_local_deaths = max(0, int(state.get("deaths", self.game.mp_local_deaths)))
        self.game.mp_local_alive = bool(state.get("alive", self.game.mp_local_alive))
        self.game.mp_local_respawn_at = float(state.get("respawn_at", self.game.mp_local_respawn_at or 0.0))

        new_score = int(state.get("score", self.game.score))
        if new_score != self.game.score:
            self.game.score = new_score
            self.game.hud_manager.update_score_display()

        if self.game.mp_local_alive and (not self.game.mp_spawn_synced or not was_alive):
            self.sync_local_multiplayer_spawn(state)
        elif not self.game.mp_local_alive and was_alive:
            self.reset_multiplayer_motion_state()

        self.game.hud_manager.update_multiplayer_hud()

    def show_multiplayer_menu(self):
        """Показывает меню мультиплеера"""
        if self.game.menu:
            self.game.menu.hide()

        if self.game.lobby_menu is None:
            self.game.lobby_menu = LobbyMenu(self.game)
            self.game.lobby_menu.set_connect_callback(self.connect_to_server)
            self.game.lobby_menu.set_back_callback(self.back_from_multiplayer)

        self.game.lobby_menu.show()

    def connect_to_server(self, server_ip: str, port: int, player_name: str):
        """Подключается к серверу мультиплеера"""
        if self.game.network is None:
            self.game.network = NetworkClient(self.game)

        success = self.game.network.connect(server_ip, port, player_name)

        if success:
            self.game.lobby_menu.set_connection_status(True, "Connected!")
        else:
            self.game.lobby_menu.set_connection_status(False, "Connection failed")

    def back_from_multiplayer(self):
        """Возвращается из мультиплеера в главное меню"""
        self.cleanup_multiplayer()

        if self.game.menu:
            self.game.menu.show()

    def start_multiplayer_game(self):
        """Запускает мультиплеерную игру"""
        if not self.game.network or not self.game.network.is_connected():
            print("Warning: Не подключен к серверу!")
            return

        self.game.is_multiplayer = True

        # Карта будет переключена автоматически когда сервер отправит game_start

        if self.game.lobby_menu:
            self.game.lobby_menu.hide()

        self.game.start_game()

    def update_remote_players(self, dt: float):
        """Обновляет модели других игроков"""
        if not self.game.network:
            return

        remote_players_data = self.game.network.get_remote_players()

        for player_id in list(self.game.remote_players.keys()):
            if player_id not in remote_players_data:
                self.game.remote_players[player_id].destroy()
                del self.game.remote_players[player_id]

        for player_id, player_data in remote_players_data.items():
            if player_id not in self.game.remote_players:
                player_name = player_data.get("name", "Unknown")
                model = RemotePlayerModel(self.game, player_id, player_name)
                model.set_hitbox_debug_visible(self.game.settings.get("show_hitbox_debug", False))
                self.game.remote_players[player_id] = model

            self.game.remote_players[player_id].update(player_data, dt)

    def cleanup_multiplayer(self):
        """Очищает ресурсы мультиплеера"""
        if self.game.network:
            try:
                self.game.network.disconnect()
            except Exception:
                pass
            self.game.network = None

        # Удаляем модели других игроков
        for player_model in list(self.game.remote_players.values()):
            try:
                player_model.destroy()
            except Exception:
                pass
        self.game.remote_players.clear()

        for target_id in list(self.game.mp_targets_by_id.keys()):
            target_obj = self.game.mp_targets_by_id.pop(target_id)
            try:
                if target_obj in self.game.targets:
                    self.game.targets.remove(target_obj)
                target_obj.network_id = None
                target_obj.destroy()
            except Exception:
                pass
        self.game.mp_targets_revision = -1
        self.game.chat_manager.is_chat_active = False
        self.game.show_scoreboard = False
        self.game.chat_manager.chat_messages.clear()
        if hasattr(self.game, 'chat_entry'):
            self.game.chat_manager.chat_entry["focus"] = 0
            self.game.chat_manager.chat_entry.hide()
        if hasattr(self.game, 'chat_text'):
            self.game.chat_manager.chat_text.setText("")
            self.game.chat_manager.chat_text.hide()
        if hasattr(self.game, 'scoreboard_text'):
            self.game.hud_manager.scoreboard_text.hide()
        if hasattr(self.game, 'hp_text'):
            self.game.hud_manager.hp_text.hide()
        if hasattr(self.game, 'kd_text'):
            self.game.hud_manager.kd_text.hide()
        if hasattr(self.game, 'death_overlay'):
            self.game.hud_manager.death_overlay.hide()
        if hasattr(self.game, 'death_text'):
            self.game.hud_manager.death_text.hide()
        if hasattr(self.game, 'hurt_flash'):
            self.game.hud_manager.hurt_flash.hide()
        self.game.mp_local_hp = 100
        self.game.mp_local_max_hp = 100
        self.game.mp_local_kills = 0
        self.game.mp_local_deaths = 0
        self.game.mp_local_alive = True
        self.game.mp_local_respawn_at = 0.0
        self.game.mp_spawn_synced = False
        self.game.hud_manager.hurt_flash_alpha = 0.0

        self.game.is_multiplayer = False

        # Возвращаем дефолтную карту
        if hasattr(self.game, 'current_map') and self.game.current_map == "pvp":
            self.game.switch_map("default")
