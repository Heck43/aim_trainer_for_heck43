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
    def create_connect_message(player_name: str, player_id: str) -> dict:
        """Создает сообщение о подключении"""
        return {
            "type": MSG_CONNECT,
            "player_id": player_id,
            "name": player_name,
            "timestamp": time.time()
        }
    
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
