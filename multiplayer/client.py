"""
Клиент для мультиплеера Aim Trainer
Интегрируется в main.py
"""
import socket
import threading
import time
import uuid
from .protocol import Protocol, MSG_GAME_STATE, MSG_GAME_START, MSG_GAME_END, MSG_PONG

class NetworkClient:
    """Сетевой клиент для мультиплеера"""
    
    def __init__(self, game):
        self.game = game
        self.socket = None
        self.server_address = None
        self.connected = False
        self.running = False
        
        # Идентификация игрока
        self.player_id = str(uuid.uuid4())[:8]
        self.player_name = "Player"
        
        # Состояние игры от сервера
        self.game_state = None
        self.game_phase = "waiting"
        self.time_remaining = 0
        self.remote_players = {}  # {player_id: player_data}
        
        # Потокобезопасность
        self.state_lock = threading.Lock()
        
        # Для измерения ping
        self.ping = 0
        self.last_ping_time = 0
    
    def connect(self, server_ip: str, port: int = 7777, player_name: str = "Player"):
        """Подключается к серверу"""
        self.player_name = player_name
        self.server_address = (server_ip, port)
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            
            # Отправляем сообщение о подключении
            connect_msg = Protocol.create_connect_message(self.player_name, self.player_id)
            data = Protocol.encode(connect_msg)
            self.socket.sendto(data, self.server_address)
            
            self.connected = True
            self.running = True
            
            # Запускаем поток получения данных
            self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Запускаем поток ping
            self.ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
            self.ping_thread.start()
            
            print(f"[Network] Connected to {server_ip}:{port}")
            return True
            
        except Exception as e:
            print(f"[Network] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Отключается от сервера"""
        if self.connected:
            try:
                # Отправляем сообщение об отключении
                disconnect_msg = Protocol.create_disconnect_message(self.player_id)
                data = Protocol.encode(disconnect_msg)
                self.socket.sendto(data, self.server_address)
            except:
                pass
            
            self.running = False
            self.connected = False
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            print("[Network] Disconnected from server")
    
    def send_state(self, pos, heading: float, pitch: float, 
                  weapon: str, shooting: bool, score: int):
        """Отправляет состояние игрока на сервер"""
        if not self.connected:
            return
        
        try:
            state_msg = Protocol.create_player_state(
                player_id=self.player_id,
                name=self.player_name,
                pos=(pos.getX(), pos.getY(), pos.getZ()),
                heading=heading,
                pitch=pitch,
                weapon=weapon,
                shooting=shooting,
                score=score
            )
            data = Protocol.encode(state_msg)
            self.socket.sendto(data, self.server_address)
        except Exception as e:
            print(f"[Network] Send error: {e}")
    
    def receive_loop(self):
        """Цикл получения данных от сервера"""
        while self.running:
            try:
                data, address = self.socket.recvfrom(Protocol.BUFFER_SIZE)
                message = Protocol.decode(data)
                if message:
                    self.handle_message(message)
            except BlockingIOError:
                time.sleep(0.001)
            except Exception as e:
                if self.running:
                    print(f"[Network] Receive error: {e}")
    
    def ping_loop(self):
        """Цикл отправки ping и heartbeat"""
        while self.running:
            try:
                if self.connected:
                    # Отправляем ping
                    ping_msg = Protocol.create_ping()
                    self.last_ping_time = time.time()
                    data = Protocol.encode(ping_msg)
                    self.socket.sendto(data, self.server_address)
                    
                    # Отправляем heartbeat (состояние игрока) чтобы сервер знал что мы живы
                    heartbeat = Protocol.create_player_state(
                        player_id=self.player_id,
                        name=self.player_name,
                        pos=(0, 0, 1.8),  # Позиция по умолчанию в лобби
                        heading=0,
                        pitch=0,
                        weapon="pistol",
                        shooting=False,
                        score=0
                    )
                    data = Protocol.encode(heartbeat)
                    self.socket.sendto(data, self.server_address)
                    
                time.sleep(1.0)  # Раз в секунду
            except:
                pass
    
    def handle_message(self, message: dict):
        """Обрабатывает входящее сообщение"""
        msg_type = message.get("type")
        
        if msg_type == MSG_GAME_STATE:
            self.handle_game_state(message)
        elif msg_type == MSG_GAME_START:
            self.handle_game_start(message)
        elif msg_type == MSG_GAME_END:
            self.handle_game_end(message)
        elif msg_type == MSG_PONG:
            self.handle_pong(message)
    
    def handle_game_state(self, message: dict):
        """Обрабатывает состояние игры от сервера"""
        with self.state_lock:
            self.game_state = message
            self.game_phase = message.get("phase", "waiting")
            self.time_remaining = message.get("time_remaining", 0)
            
            # Обновляем список игроков
            players = message.get("players", [])
            self.remote_players = {
                p["id"]: p for p in players if p["id"] != self.player_id
            }
    
    def handle_game_start(self, message: dict):
        """Обрабатывает начало игры"""
        duration = message.get("duration", 60)
        print(f"[Network] Game started! Duration: {duration}s")
        self.game_phase = "playing"
        
        # Уведомляем игру о начале
        if hasattr(self.game, 'on_multiplayer_game_start'):
            self.game.on_multiplayer_game_start()
    
    def handle_game_end(self, message: dict):
        """Обрабатывает конец игры"""
        winner_name = message.get("winner_name", "Unknown")
        final_scores = message.get("final_scores", [])
        print(f"[Network] Game ended! Winner: {winner_name}")
        self.game_phase = "finished"
        
        # Уведомляем игру о конце
        if hasattr(self.game, 'on_multiplayer_game_end'):
            self.game.on_multiplayer_game_end(winner_name, final_scores)
    
    def handle_pong(self, message: dict):
        """Обрабатывает pong ответ"""
        ping_timestamp = message.get("ping_timestamp", 0)
        self.ping = int((time.time() - ping_timestamp) * 1000)
    
    def get_remote_players(self) -> dict:
        """Возвращает список удаленных игроков"""
        with self.state_lock:
            return self.remote_players.copy()
    
    def get_game_phase(self) -> str:
        """Возвращает текущую фазу игры"""
        return self.game_phase
    
    def get_time_remaining(self) -> float:
        """Возвращает оставшееся время"""
        return self.time_remaining
    
    def get_ping(self) -> int:
        """Возвращает ping в миллисекундах"""
        return self.ping
    
    def is_connected(self) -> bool:
        """Проверяет подключение"""
        return self.connected

