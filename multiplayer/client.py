"""
Aim Trainer multiplayer network client.
"""
import socket
import threading
import time
import uuid
from .protocol import (
    Protocol,
    MSG_GAME_STATE,
    MSG_GAME_START,
    MSG_GAME_END,
    MSG_PONG,
    MSG_SHOT_RESULT,
    MSG_TARGETS_STATE,
    MSG_CHAT,
)


class NetworkClient:
    """Network client for multiplayer."""

    def __init__(self, game):
        self.game = game
        self.socket = None
        self.server_address = None
        self.connected = False
        self.running = False

        self.player_id = str(uuid.uuid4())[:8]
        self.player_name = "Player"

        self.game_state = None
        self.game_phase = "waiting"
        self.game_mode = "pve"
        self.time_remaining = 0
        self.remote_players = {}

        self.state_lock = threading.Lock()

        self.ping = 0
        self.last_ping_time = 0
        self.next_shot_id = 1
        self.local_server_score = 0
        self.server_time_offset = 0.0
        self.local_player_state = self._make_default_local_state()

        self.targets_state = {"targets": [], "revision": -1, "server_time": 0}
        self.latest_targets_snapshot = None
        self.shot_results_queue = []
        self.chat_queue = []

    def _make_default_local_state(self) -> dict:
        return {
            "id": self.player_id,
            "name": self.player_name,
            "pos": [0.0, 0.0, 1.8],
            "heading": 0.0,
            "pitch": 0.0,
            "weapon": "pistol",
            "shooting": False,
            "score": 0,
            "hp": 100,
            "max_hp": 100,
            "alive": True,
            "respawn_at": 0.0,
            "kills": 0,
            "deaths": 0,
        }

    def _update_server_time_offset(self, server_time: float):
        try:
            server_time = float(server_time)
        except (TypeError, ValueError):
            return
        if server_time <= 0:
            return
        observed_offset = server_time - time.time()
        if abs(self.server_time_offset) <= 1e-6:
            self.server_time_offset = observed_offset
        else:
            self.server_time_offset = (self.server_time_offset * 0.8) + (observed_offset * 0.2)

    def connect(self, server_ip: str, port: int = 7777, player_name: str = "Player"):
        self.player_name = player_name
        self.server_address = (server_ip, port)

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)

            # Получаем хитбоксы для отправки на сервер
            hitboxes = None
            try:
                from multiplayer.player_model import RemotePlayerModel
                hitboxes = RemotePlayerModel.preload_hitboxes(self.game)
                print(f"[NetworkClient] Отправляем хитбоксы на сервер")
            except Exception as e:
                print(f"[NetworkClient] Не удалось получить хитбоксы: {e}")

            connect_msg = Protocol.create_connect_message(self.player_name, self.player_id, hitboxes)
            self.socket.sendto(Protocol.encode(connect_msg), self.server_address)

            self.connected = True
            self.running = True
            with self.state_lock:
                self.local_server_score = 0
                self.server_time_offset = 0.0
                self.next_shot_id = 1
                self.local_player_state = self._make_default_local_state()

            self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.receive_thread.start()

            self.ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
            self.ping_thread.start()

            print(f"[Network] Connected to {server_ip}:{port}")
            return True
        except Exception as exc:
            print(f"[Network] Connection failed: {exc}")
            return False

    def disconnect(self):
        if self.connected:
            try:
                disconnect_msg = Protocol.create_disconnect_message(self.player_id)
                self.socket.sendto(Protocol.encode(disconnect_msg), self.server_address)
            except Exception:
                pass

            self.running = False
            self.connected = False

            if self.socket:
                self.socket.close()
                self.socket = None

            with self.state_lock:
                self.remote_players.clear()
                self.local_server_score = 0
                self.server_time_offset = 0.0
                self.local_player_state = self._make_default_local_state()
                self.targets_state = {"targets": [], "revision": -1, "server_time": 0}
                self.latest_targets_snapshot = None
                self.shot_results_queue.clear()
                self.chat_queue.clear()

            print("[Network] Disconnected from server")

    def send_state(self, pos, heading: float, pitch: float, weapon: str, shooting: bool, score: int):
        if not self.connected:
            return
        try:
            msg = Protocol.create_player_state(
                player_id=self.player_id,
                name=self.player_name,
                pos=(pos.getX(), pos.getY(), pos.getZ()),
                heading=heading,
                pitch=pitch,
                weapon=weapon,
                shooting=shooting,
                score=score,
            )
            self.socket.sendto(Protocol.encode(msg), self.server_address)
        except Exception as exc:
            print(f"[Network] Send error: {exc}")

    def send_shot(self, origin, direction, weapon: str, camera_heading: float, camera_pitch: float):
        if not self.connected:
            return None
        try:
            with self.state_lock:
                shot_id = self.next_shot_id
                self.next_shot_id += 1

            msg = Protocol.create_shot(
                player_id=self.player_id,
                shot_id=shot_id,
                origin=(origin.getX(), origin.getY(), origin.getZ()),
                direction=(direction.getX(), direction.getY(), direction.getZ()),
                weapon=weapon,
                camera_heading=camera_heading,
                camera_pitch=camera_pitch,
            )
            self.socket.sendto(Protocol.encode(msg), self.server_address)
            return shot_id
        except Exception as exc:
            print(f"[Network] Send shot error: {exc}")
            return None

    def send_chat(self, text: str):
        if not self.connected:
            return
        text = (text or "").strip()
        if not text:
            return
        try:
            msg = Protocol.create_chat_message(
                player_id=self.player_id,
                name=self.player_name,
                text=text[:180],
            )
            self.socket.sendto(Protocol.encode(msg), self.server_address)
        except Exception as exc:
            print(f"[Network] Send chat error: {exc}")

    def receive_loop(self):
        while self.running:
            try:
                data, _address = self.socket.recvfrom(Protocol.BUFFER_SIZE)
                message = Protocol.decode(data)
                if message:
                    self.handle_message(message)
            except BlockingIOError:
                time.sleep(0.001)
            except Exception as exc:
                if self.running:
                    print(f"[Network] Receive error: {exc}")

    def ping_loop(self):
        while self.running:
            try:
                if self.connected:
                    ping_msg = Protocol.create_ping()
                    self.last_ping_time = time.time()
                    self.socket.sendto(Protocol.encode(ping_msg), self.server_address)

                    heartbeat = Protocol.create_heartbeat(
                        player_id=self.player_id,
                        name=self.player_name,
                    )
                    self.socket.sendto(Protocol.encode(heartbeat), self.server_address)

                time.sleep(1.0)
            except Exception:
                pass

    def handle_message(self, message: dict):
        msg_type = message.get("type")
        if msg_type == MSG_GAME_STATE:
            self.handle_game_state(message)
        elif msg_type == MSG_GAME_START:
            self.handle_game_start(message)
        elif msg_type == MSG_GAME_END:
            self.handle_game_end(message)
        elif msg_type == MSG_PONG:
            self.handle_pong(message)
        elif msg_type == MSG_SHOT_RESULT:
            self.handle_shot_result(message)
        elif msg_type == MSG_TARGETS_STATE:
            self.handle_targets_state(message)
        elif msg_type == MSG_CHAT:
            self.handle_chat(message)

    def handle_game_state(self, message: dict):
        with self.state_lock:
            self._update_server_time_offset(message.get("timestamp", 0))
            self.game_state = message
            self.game_phase = message.get("phase", "waiting")
            self.time_remaining = message.get("time_remaining", 0)
            players = message.get("players", [])
            self.remote_players = {p["id"]: p for p in players if p.get("id") != self.player_id}
            local_state = None
            for player in players:
                if player.get("id") == self.player_id:
                    self.local_server_score = int(player.get("score", self.local_server_score))
                    local_state = dict(player)
                    break
            if local_state is not None:
                self.local_player_state = local_state

    def handle_game_start(self, message: dict):
        duration = message.get("duration", 60)
        game_mode = message.get("game_mode", "pve")
        self.game_mode = game_mode
        print(f"[Network] Game started! Duration: {duration}s, Mode: {game_mode}")
        self.game_phase = "playing"

        # Переключаем карту на клиенте
        if hasattr(self.game, "switch_map"):
            if game_mode == "pvp":
                self.game.switch_map("pvp")
            else:
                # pve режим использует дефолтную карту
                self.game.switch_map("default")

        # Обновляем режим в игре
        if hasattr(self.game, "multiplayer_game_mode"):
            self.game.multiplayer_game_mode = game_mode

        if hasattr(self.game, "on_multiplayer_game_start"):
            self.game.on_multiplayer_game_start()

    def handle_game_end(self, message: dict):
        winner_name = message.get("winner_name", "Unknown")
        final_scores = message.get("final_scores", [])
        print(f"[Network] Game ended! Winner: {winner_name}")
        self.game_phase = "finished"
        if hasattr(self.game, "on_multiplayer_game_end"):
            self.game.on_multiplayer_game_end(winner_name, final_scores)

    def handle_pong(self, message: dict):
        ping_timestamp = message.get("ping_timestamp", 0)
        self.ping = int((time.time() - ping_timestamp) * 1000)

    def handle_shot_result(self, message: dict):
        with self.state_lock:
            self._update_server_time_offset(message.get("server_time", 0))
            self.shot_results_queue.append(message)
            if message.get("shooter_id") == self.player_id:
                self.local_server_score = int(message.get("new_score", self.local_server_score))
                self.local_player_state["score"] = self.local_server_score
                if message.get("kill"):
                    self.local_player_state["kills"] = int(self.local_player_state.get("kills", 0)) + 1
            if message.get("victim_id") == self.player_id:
                victim_hp = message.get("victim_hp")
                if victim_hp is not None:
                    self.local_player_state["hp"] = int(victim_hp)
                if "victim_alive" in message:
                    self.local_player_state["alive"] = bool(message.get("victim_alive"))
                    if not self.local_player_state["alive"] and message.get("kill"):
                        self.local_player_state["deaths"] = int(self.local_player_state.get("deaths", 0)) + 1

    def handle_targets_state(self, message: dict):
        with self.state_lock:
            self._update_server_time_offset(message.get("server_time", 0))
            revision = int(message.get("revision", -1))
            current_revision = int(self.targets_state.get("revision", -1))
            if revision <= current_revision:
                return
            self.targets_state = {
                "targets": message.get("targets", []),
                "revision": revision,
                "server_time": message.get("server_time", 0),
            }
            self.latest_targets_snapshot = self.targets_state.copy()

    def handle_chat(self, message: dict):
        with self.state_lock:
            self._update_server_time_offset(message.get("server_time", 0))
            self.chat_queue.append(message)

    def consume_latest_targets_snapshot(self):
        with self.state_lock:
            snapshot = self.latest_targets_snapshot
            self.latest_targets_snapshot = None
            return snapshot

    def consume_shot_results(self):
        with self.state_lock:
            results = list(self.shot_results_queue)
            self.shot_results_queue.clear()
            return results

    def consume_chat_messages(self):
        with self.state_lock:
            messages = list(self.chat_queue)
            self.chat_queue.clear()
            return messages

    def get_remote_players(self) -> dict:
        with self.state_lock:
            return self.remote_players.copy()

    def get_game_phase(self) -> str:
        return self.game_phase

    def get_game_mode(self) -> str:
        return self.game_mode

    def get_time_remaining(self) -> float:
        return self.time_remaining

    def get_ping(self) -> int:
        return self.ping

    def is_connected(self) -> bool:
        return self.connected

    def get_local_server_score(self) -> int:
        with self.state_lock:
            return self.local_server_score

    def get_local_player_state(self) -> dict:
        with self.state_lock:
            return self.local_player_state.copy()

    def get_estimated_server_time(self) -> float:
        with self.state_lock:
            return time.time() + self.server_time_offset

    def get_scoreboard(self) -> list:
        with self.state_lock:
            if not self.game_state:
                return []
            players = self.game_state.get("players", [])
            return sorted(players, key=lambda p: int(p.get("score", 0)), reverse=True)
