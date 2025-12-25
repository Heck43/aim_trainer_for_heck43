"""
Выделенный UDP сервер для мультиплеера Aim Trainer
Запускается как отдельное консольное приложение
"""
import socket
import threading
import time
import sys
import os

# Импорт protocol (работает и в исходниках, и в PyInstaller)
try:
    # Абсолютный импорт для PyInstaller
    from multiplayer.protocol import Protocol, MSG_CONNECT, MSG_DISCONNECT, MSG_PLAYER_STATE, MSG_PING
except ImportError:
    try:
        # Относительный импорт для запуска как модуля
        from .protocol import Protocol, MSG_CONNECT, MSG_DISCONNECT, MSG_PLAYER_STATE, MSG_PING
    except ImportError:
        # Для запуска напрямую из файла (fallback)
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from multiplayer.protocol import Protocol, MSG_CONNECT, MSG_DISCONNECT, MSG_PLAYER_STATE, MSG_PING

class Player:
    """Информация об игроке"""
    def __init__(self, player_id: str, name: str, address: tuple):
        self.player_id = player_id
        self.name = name
        self.address = address  # (ip, port)
        self.pos = [0, 0, 1.8]
        self.heading = 0.0
        self.pitch = 0.0
        self.weapon = "pistol"
        self.shooting = False
        self.score = 0
        self.last_update = time.time()
        self.ping = 0
    
    def to_dict(self):
        """Преобразует в словарь для отправки"""
        return {
            "id": self.player_id,
            "name": self.name,
            "pos": self.pos,
            "heading": self.heading,
            "pitch": self.pitch,
            "weapon": self.weapon,
            "shooting": self.shooting,
            "score": self.score
        }

class GameServer:
    """UDP сервер для мультиплеера"""
    
    def __init__(self, port: int = 7777, max_players: int = 8):
        self.port = port
        self.max_players = max_players
        self.players = {}  # {player_id: Player}
        self.running = False
        self.socket = None
        
        # Состояние игры
        self.game_phase = "waiting"  # waiting, playing, finished
        self.game_duration = 60  # секунды
        self.game_start_time = 0
        self.time_remaining = 0
        
        # Для логирования
        self.log_lock = threading.Lock()
    
    def get_local_ip(self):
        """Получает локальный IP адрес"""
        try:
            # Создаем временный сокет для определения IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def log(self, message: str):
        """Потокобезопасный вывод в консоль"""
        with self.log_lock:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def print_header(self):
        """Выводит заголовок сервера"""
        ip = self.get_local_ip()
        print("\n" + "=" * 50)
        print("     AIM TRAINER - MULTIPLAYER SERVER")
        print("=" * 50)
        print(f"  Server IP: {ip}")
        print(f"  Port: {self.port}")
        print(f"  Max Players: {self.max_players}")
        print(f"  Status: Waiting for players...")
        print("-" * 50)
        print("  Commands:")
        print("    start - Start the game")
        print("    stop  - Stop the game")
        print("    kick <name> - Kick a player")
        print("    status - Show server status")
        print("    quit  - Shutdown server")
        print("-" * 50)
        print()
    
    def print_players(self):
        """Выводит список игроков"""
        print(f"\nPlayers connected: {len(self.players)}/{self.max_players}")
        if self.players:
            print("-" * 30)
            for player in self.players.values():
                print(f"  {player.name}: {player.score} points (ping: {player.ping}ms)")
            print("-" * 30)
        print()
    
    def start(self):
        """Запускает сервер"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.socket.setblocking(False)
        
        self.running = True
        self.print_header()
        
        # Запускаем потоки
        receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        broadcast_thread = threading.Thread(target=self.broadcast_loop, daemon=True)
        cleanup_thread = threading.Thread(target=self.cleanup_loop, daemon=True)
        
        receive_thread.start()
        broadcast_thread.start()
        cleanup_thread.start()
        
        # Главный цикл - обработка команд
        self.command_loop()
    
    def receive_loop(self):
        """Цикл получения сообщений"""
        while self.running:
            try:
                data, address = self.socket.recvfrom(Protocol.BUFFER_SIZE)
                message = Protocol.decode(data)
                if message:
                    self.handle_message(message, address)
            except BlockingIOError:
                time.sleep(0.001)  # Небольшая пауза если нет данных
            except Exception as e:
                if self.running:
                    self.log(f"Receive error: {e}")
    
    def broadcast_loop(self):
        """Цикл рассылки состояния игры"""
        while self.running:
            try:
                # Обновляем время игры
                if self.game_phase == "playing":
                    elapsed = time.time() - self.game_start_time
                    self.time_remaining = max(0, self.game_duration - elapsed)
                    
                    if self.time_remaining <= 0:
                        self.end_game()
                
                # Рассылаем состояние всем игрокам
                if self.players:
                    players_list = [p.to_dict() for p in self.players.values()]
                    game_state = Protocol.create_game_state(
                        players=players_list,
                        time_remaining=self.time_remaining,
                        phase=self.game_phase
                    )
                    data = Protocol.encode(game_state)
                    
                    for player in self.players.values():
                        try:
                            self.socket.sendto(data, player.address)
                        except:
                            pass
                
                time.sleep(1/30)  # 30 раз в секунду
            except Exception as e:
                if self.running:
                    self.log(f"Broadcast error: {e}")
    
    def cleanup_loop(self):
        """Цикл очистки неактивных игроков"""
        while self.running:
            try:
                current_time = time.time()
                disconnected = []
                
                for player_id, player in self.players.items():
                    if current_time - player.last_update > 5.0:  # 5 секунд без ответа
                        disconnected.append(player_id)
                
                for player_id in disconnected:
                    player = self.players.pop(player_id, None)
                    if player:
                        self.log(f"Player \"{player.name}\" timed out")
                
                time.sleep(1.0)
            except Exception as e:
                if self.running:
                    self.log(f"Cleanup error: {e}")
    
    def handle_message(self, message: dict, address: tuple):
        """Обрабатывает входящее сообщение"""
        msg_type = message.get("type")
        
        if msg_type == MSG_CONNECT:
            self.handle_connect(message, address)
        elif msg_type == MSG_DISCONNECT:
            self.handle_disconnect(message)
        elif msg_type == MSG_PLAYER_STATE:
            self.handle_player_state(message, address)
        elif msg_type == MSG_PING:
            self.handle_ping(message, address)
    
    def handle_connect(self, message: dict, address: tuple):
        """Обрабатывает подключение игрока"""
        player_id = message.get("player_id")
        name = message.get("name", "Unknown")
        
        if len(self.players) >= self.max_players:
            self.log(f"Connection rejected (server full): {name} from {address[0]}")
            return
        
        if player_id not in self.players:
            player = Player(player_id, name, address)
            self.players[player_id] = player
            self.log(f"Player \"{name}\" connected from {address[0]}:{address[1]}")
            self.print_players()
    
    def handle_disconnect(self, message: dict):
        """Обрабатывает отключение игрока"""
        player_id = message.get("player_id")
        player = self.players.pop(player_id, None)
        if player:
            self.log(f"Player \"{player.name}\" disconnected")
            self.print_players()
    
    def handle_player_state(self, message: dict, address: tuple):
        """Обрабатывает обновление состояния игрока"""
        player_id = message.get("player_id")
        
        if player_id in self.players:
            player = self.players[player_id]
            player.pos = message.get("pos", player.pos)
            player.heading = message.get("heading", player.heading)
            player.pitch = message.get("pitch", player.pitch)
            player.weapon = message.get("weapon", player.weapon)
            player.shooting = message.get("shooting", player.shooting)
            player.score = message.get("score", player.score)
            player.last_update = time.time()
            player.address = address  # Обновляем адрес на случай NAT
    
    def handle_ping(self, message: dict, address: tuple):
        """Отвечает на ping"""
        pong = Protocol.create_pong(message.get("timestamp", 0))
        data = Protocol.encode(pong)
        try:
            self.socket.sendto(data, address)
        except:
            pass
    
    def start_game(self):
        """Запускает игру"""
        if len(self.players) < 1:
            self.log("Cannot start: no players connected")
            return
        
        self.game_phase = "playing"
        self.game_start_time = time.time()
        self.time_remaining = self.game_duration
        
        # Сбрасываем очки
        for player in self.players.values():
            player.score = 0
        
        self.log(f"Game started! Duration: {self.game_duration}s")
        
        # Отправляем сообщение о начале
        start_msg = Protocol.create_game_start(self.game_duration)
        data = Protocol.encode(start_msg)
        for player in self.players.values():
            try:
                self.socket.sendto(data, player.address)
            except:
                pass
    
    def end_game(self):
        """Завершает игру"""
        self.game_phase = "finished"
        
        # Находим победителя
        if self.players:
            winner = max(self.players.values(), key=lambda p: p.score)
            final_scores = [(p.name, p.score) for p in 
                           sorted(self.players.values(), key=lambda p: p.score, reverse=True)]
            
            self.log(f"Game ended! Winner: {winner.name} ({winner.score} points)")
            print("\n  Final Scores:")
            for i, (name, score) in enumerate(final_scores, 1):
                print(f"    {i}. {name}: {score} points")
            print()
            
            # Отправляем сообщение о конце
            end_msg = Protocol.create_game_end(winner.player_id, winner.name, final_scores)
            data = Protocol.encode(end_msg)
            for player in self.players.values():
                try:
                    self.socket.sendto(data, player.address)
                except:
                    pass
        
        # Возвращаемся в режим ожидания
        self.game_phase = "waiting"
    
    def kick_player(self, name: str):
        """Кикает игрока по имени"""
        for player_id, player in list(self.players.items()):
            if player.name.lower() == name.lower():
                self.players.pop(player_id)
                self.log(f"Player \"{player.name}\" was kicked")
                self.print_players()
                return
        self.log(f"Player \"{name}\" not found")
    
    def command_loop(self):
        """Цикл обработки команд"""
        while self.running:
            try:
                cmd = input().strip().lower()
                
                if cmd == "start":
                    self.start_game()
                elif cmd == "stop":
                    if self.game_phase == "playing":
                        self.end_game()
                    else:
                        self.log("No game in progress")
                elif cmd.startswith("kick "):
                    name = cmd[5:].strip()
                    if name:
                        self.kick_player(name)
                elif cmd == "status":
                    print(f"\nGame Phase: {self.game_phase}")
                    if self.game_phase == "playing":
                        print(f"Time Remaining: {self.time_remaining:.1f}s")
                    self.print_players()
                elif cmd == "quit" or cmd == "exit":
                    self.log("Shutting down server...")
                    self.running = False
                    break
                elif cmd:
                    print("Unknown command. Use: start, stop, kick <name>, status, quit")
            except EOFError:
                break
            except KeyboardInterrupt:
                self.log("Shutting down server...")
                self.running = False
                break
    
    def stop(self):
        """Останавливает сервер"""
        self.running = False
        if self.socket:
            self.socket.close()

def main():
    """Точка входа"""
    port = 7777
    
    # Можно передать порт как аргумент
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    server = GameServer(port=port)
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

if __name__ == "__main__":
    main()
