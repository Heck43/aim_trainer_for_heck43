"""
Протокол сообщений для мультиплеера
Сериализация/десериализация JSON через UDP
"""
import json
import time

# Типы сообщений
MSG_CONNECT = "connect"
MSG_DISCONNECT = "disconnect"
MSG_PLAYER_STATE = "player_state"
MSG_GAME_STATE = "game_state"
MSG_GAME_START = "game_start"
MSG_GAME_END = "game_end"
MSG_PING = "ping"
MSG_PONG = "pong"
MSG_HEARTBEAT = "heartbeat"
MSG_SHOT = "shot"
MSG_SHOT_RESULT = "shot_result"
MSG_TARGETS_STATE = "targets_state"
MSG_CHAT = "chat"

class Protocol:
    """Протокол сообщений"""
    
    BUFFER_SIZE = 4096
    
    @staticmethod
    def encode(data: dict) -> bytes:
        """Кодирует словарь в байты для отправки"""
        return json.dumps(data, separators=(',', ':')).encode('utf-8')
    
    @staticmethod
    def decode(data: bytes) -> dict:
        """Декодирует байты в словарь"""
        try:
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    @staticmethod
    def create_connect_message(player_name: str, player_id: str, hitboxes: dict = None) -> dict:
        """Создает сообщение о подключении"""
        msg = {
            "type": MSG_CONNECT,
            "player_id": player_id,
            "name": player_name,
            "timestamp": time.time()
        }
        if hitboxes:
            msg["hitboxes"] = hitboxes
        return msg
    
    @staticmethod
    def create_disconnect_message(player_id: str) -> dict:
        """Создает сообщение об отключении"""
        return {
            "type": MSG_DISCONNECT,
            "player_id": player_id,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_player_state(player_id: str, name: str, pos: tuple, 
                           heading: float, pitch: float, weapon: str,
                           shooting: bool, score: int) -> dict:
        """Создает сообщение с состоянием игрока"""
        return {
            "type": MSG_PLAYER_STATE,
            "player_id": player_id,
            "name": name,
            "pos": list(pos),
            "heading": heading,
            "pitch": pitch,
            "weapon": weapon,
            "shooting": shooting,
            "score": score,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_game_state(players: list, time_remaining: float, 
                         phase: str) -> dict:
        """Создает сообщение с состоянием игры (сервер -> клиенты)"""
        return {
            "type": MSG_GAME_STATE,
            "players": players,
            "time_remaining": time_remaining,
            "phase": phase,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_game_start(duration: int) -> dict:
        """Создает сообщение о начале игры"""
        return {
            "type": MSG_GAME_START,
            "duration": duration,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_game_end(winner_id: str, winner_name: str, 
                       final_scores: list) -> dict:
        """Создает сообщение о конце игры"""
        return {
            "type": MSG_GAME_END,
            "winner_id": winner_id,
            "winner_name": winner_name,
            "final_scores": final_scores,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_ping() -> dict:
        """Создает ping сообщение"""
        return {
            "type": MSG_PING,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_pong(ping_timestamp: float) -> dict:
        """Создает pong сообщение"""
        return {
            "type": MSG_PONG,
            "ping_timestamp": ping_timestamp,
            "timestamp": time.time()
        }
    @staticmethod
    def create_heartbeat(player_id: str, name: str) -> dict:
        """Creates a heartbeat message without gameplay state."""
        return {
            "type": MSG_HEARTBEAT,
            "player_id": player_id,
            "name": name,
            "timestamp": time.time()
        }

    @staticmethod
    def create_shot(player_id: str, shot_id: int, origin: tuple, direction: tuple,
                    weapon: str, camera_heading: float, camera_pitch: float) -> dict:
        """Creates a server-authoritative shot message."""
        return {
            "type": MSG_SHOT,
            "player_id": player_id,
            "shot_id": shot_id,
            "timestamp": time.time(),
            "origin": list(origin),
            "dir": list(direction),
            "weapon": weapon,
            "camera_heading": camera_heading,
            "camera_pitch": camera_pitch
        }

    @staticmethod
    def create_shot_result(shot_id: int, shooter_id: str, hit: bool, target_id: str,
                           part: str, damage: int, score_delta: int, new_score: int,
                           hit_pos: tuple, server_time: float = None,
                           origin: tuple = None, direction: tuple = None,
                           hit_type: str = "none", victim_id: str = None,
                           victim_name: str = None, victim_hp: int = None,
                           victim_alive: bool = None, kill: bool = False) -> dict:
        """Creates authoritative shot resolution."""
        return {
            "type": MSG_SHOT_RESULT,
            "shot_id": shot_id,
            "shooter_id": shooter_id,
            "hit": hit,
            "hit_type": hit_type,
            "target_id": target_id,
            "part": part,
            "damage": damage,
            "score_delta": score_delta,
            "new_score": new_score,
            "victim_id": victim_id,
            "victim_name": victim_name,
            "victim_hp": victim_hp,
            "victim_alive": victim_alive,
            "kill": bool(kill),
            "hit_pos": list(hit_pos) if hit_pos is not None else None,
            "origin": list(origin) if origin is not None else None,
            "dir": list(direction) if direction is not None else None,
            "server_time": server_time if server_time is not None else time.time()
        }

    @staticmethod
    def create_targets_state(targets: list, revision: int, server_time: float = None) -> dict:
        """Creates full snapshot of authoritative target state."""
        return {
            "type": MSG_TARGETS_STATE,
            "targets": targets,
            "revision": revision,
            "server_time": server_time if server_time is not None else time.time()
        }

    @staticmethod
    def create_chat_message(player_id: str, name: str, text: str, server_time: float = None) -> dict:
        """Creates a multiplayer chat message."""
        return {
            "type": MSG_CHAT,
            "player_id": player_id,
            "name": name,
            "text": text,
            "server_time": server_time if server_time is not None else time.time()
        }
