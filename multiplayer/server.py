"""
Dedicated UDP server for Aim Trainer multiplayer.
Server-authoritative combat: shots, scores, and targets are resolved on server.
"""
import socket
import threading
import time
import random
import sys
from dataclasses import dataclass

# Protocol import (works for source and PyInstaller)
try:
    from multiplayer.protocol import (
        Protocol,
        MSG_CONNECT,
        MSG_DISCONNECT,
        MSG_PLAYER_STATE,
        MSG_PING,
        MSG_HEARTBEAT,
        MSG_SHOT,
        MSG_CHAT,
    )
except ImportError:
    try:
        from .protocol import (
            Protocol,
            MSG_CONNECT,
            MSG_DISCONNECT,
            MSG_PLAYER_STATE,
            MSG_PING,
            MSG_HEARTBEAT,
            MSG_SHOT,
            MSG_CHAT,
        )
    except ImportError:
        import os

        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from multiplayer.protocol import (
            Protocol,
            MSG_CONNECT,
            MSG_DISCONNECT,
            MSG_PLAYER_STATE,
            MSG_PING,
            MSG_HEARTBEAT,
            MSG_SHOT,
            MSG_CHAT,
        )


TARGET_PART_OFFSETS = {
    "target_head": (0.0, 0.0, 2.6, 0.6),
    "target_body": (0.0, 0.0, 1.5, 0.85),
    "target_left_arm": (-1.0, 0.0, 1.5, 0.55),
    "target_right_arm": (1.0, 0.0, 1.5, 0.55),
    "target_legs": (0.0, 0.0, 0.6, 1.0),
}

PART_MULTIPLIERS = {
    "target_head": 2.0,
    "target_body": 1.0,
    "target_left_arm": 0.75,
    "target_right_arm": 0.75,
    "target_legs": 0.75,
}

WEAPON_CONFIG = {
    "pistol": {"cooldown": 0.2, "damage": 25},
    "rifle": {"cooldown": 0.1, "damage": 20},
    "sniper": {"cooldown": 1.0, "damage": 100},
    "dual_revolvers": {"cooldown": 0.1, "damage": 20},
}

PLAYER_PART_OFFSETS = {
    "target_head": (0.0, 0.0, 0.00, 0.32),
    "target_body": (0.0, 0.0, -0.70, 0.50),
    "target_left_arm": (-0.55, 0.0, -0.70, 0.26),
    "target_right_arm": (0.55, 0.0, -0.70, 0.26),
    "target_legs": (0.0, 0.0, -1.45, 0.42),
}

PLAYER_SPAWN_POINTS = [
    (-10.0, -10.0, 1.8),
    (10.0, -10.0, 1.8),
    (-10.0, 0.0, 1.8),
    (10.0, 0.0, 1.8),
    (-10.0, 10.0, 1.8),
    (10.0, 10.0, 1.8),
]

PLAYER_MAX_HP = 100
PLAYER_RESPAWN_DELAY = 3.0


def _vec3(v, fallback=(0.0, 1.0, 0.0)):
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        return [float(fallback[0]), float(fallback[1]), float(fallback[2])]
    try:
        return [float(v[0]), float(v[1]), float(v[2])]
    except (ValueError, TypeError):
        return [float(fallback[0]), float(fallback[1]), float(fallback[2])]


def _normalize(v):
    x, y, z = v
    mag = (x * x + y * y + z * z) ** 0.5
    if mag <= 1e-6:
        return [0.0, 1.0, 0.0]
    return [x / mag, y / mag, z / mag]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@dataclass
class TargetState:
    target_id: str
    pos: list
    alive: bool = True
    respawn_at: float = 0.0
    last_hit_by: str = None
    variant: str = "default"

    def to_dict(self):
        return {
            "id": self.target_id,
            "pos": self.pos,
            "alive": self.alive,
            "respawn_at": self.respawn_at,
            "variant": self.variant,
        }


class Player:
    """Player state stored on server."""

    def __init__(self, player_id: str, name: str, address: tuple, hitboxes: dict = None):
        self.player_id = player_id
        self.name = name
        self.address = address
        self.pos = [0, 0, 1.8]
        self.heading = 0.0
        self.pitch = 0.0
        self.weapon = "pistol"
        self.shooting = False
        self.score = 0
        self.last_update = time.time()
        self.ping = 0
        self.last_shot_time = 0.0
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.alive = True
        self.respawn_at = 0.0
        self.kills = 0
        self.deaths = 0
        self.last_spawn_index = None

        # Хитбоксы игрока (если не переданы, используем дефолтные)
        self.hitboxes = hitboxes if hitboxes else PLAYER_PART_OFFSETS.copy()

    def to_dict(self):
        return {
            "id": self.player_id,
            "name": self.name,
            "pos": self.pos,
            "heading": self.heading,
            "pitch": self.pitch,
            "weapon": self.weapon,
            "shooting": self.shooting,
            "score": self.score,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "alive": self.alive,
            "respawn_at": self.respawn_at,
            "kills": self.kills,
            "deaths": self.deaths,
        }


class GameServer:
    """UDP server for multiplayer."""

    def __init__(self, port: int = 7777, max_players: int = 8):
        self.port = port
        self.max_players = max_players
        self.players = {}
        self.targets = {}
        self.next_target_id = 1
        self.state_revision = 0
        self.processed_shots = {}
        self.running = False
        self.socket = None
        self.state_lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.log_callback = None

        self.game_phase = "waiting"  # waiting, playing, finished
        self.game_duration = 60
        self.game_start_time = 0.0
        self.time_remaining = 0.0
        self.target_count = 10
        self.target_respawn_delay = 3.0
        self.target_mode = "default"
        # Keep target snapshots available even before manual "start" command.
        self._create_targets()

    def get_local_ip(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def log(self, message: str):
        with self.log_lock:
            timestamp = time.strftime("%H:%M:%S")
            line = f"[{timestamp}] {message}"
            print(line)
        callback = self.log_callback
        if callback:
            try:
                callback(line)
            except Exception:
                pass

    def print_header(self):
        ip = self.get_local_ip()
        print("\n" + "=" * 50)
        print("     AIM TRAINER - MULTIPLAYER SERVER")
        print("=" * 50)
        print(f"  Server IP: {ip}")
        print(f"  Port: {self.port}")
        print(f"  Max Players: {self.max_players}")
        print("  Status: Waiting for players...")
        print("-" * 50)
        print("  Commands:")
        print("    start - Start the game")
        print("    stop  - Stop the game")
        print("    kick <name> - Kick a player")
        print("    set <key> <value> - Change game settings at runtime")
        print("    help - Show all commands")
        print("    status - Show server status")
        print("    quit  - Shutdown server")
        print("-" * 50)
        print()

    def print_help(self):
        print("\nServer Commands:")
        print("  start")
        print("    Start match and reset scores")
        print("  stop")
        print("    Stop current match")
        print("  status")
        print("    Print players, phase, timer and current server settings")
        print("  kick <name>")
        print("    Disconnect player by visible name")
        print("  set targets <1..100>")
        print("    Change number of targets and rebuild target state")
        print("  set respawn <0.1..30>")
        print("    Change target respawn delay in seconds")
        print("  set duration <10..3600>")
        print("    Change match duration in seconds")
        print("  set mode <nsfw|sfw>")
        print("    Control target visual mode on all clients")
        print("    Aliases: nsfw/on/1/true, sfw/off/0/false")
        print("  help")
        print("    Show this help")
        print("  quit | exit")
        print("    Shutdown server")
        print()

    def print_players(self):
        with self.state_lock:
            players = list(self.players.values())
        print(f"\nPlayers connected: {len(players)}/{self.max_players}")
        if players:
            print("-" * 30)
            for player in players:
                print(f"  {player.name}: {player.score} points (ping: {player.ping}ms)")
            print("-" * 30)
        print()

    def start(self, interactive: bool = True, print_banner: bool = True):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", self.port))
        self.socket.setblocking(False)

        self.running = True
        if print_banner:
            self.print_header()

        threading.Thread(target=self.receive_loop, daemon=True).start()
        threading.Thread(target=self.broadcast_loop, daemon=True).start()
        threading.Thread(target=self.cleanup_loop, daemon=True).start()

        if interactive:
            self.command_loop()

    def receive_loop(self):
        while self.running:
            try:
                data, address = self.socket.recvfrom(Protocol.BUFFER_SIZE)
                message = Protocol.decode(data)
                if message:
                    self.handle_message(message, address)
            except BlockingIOError:
                time.sleep(0.001)
            except Exception as exc:
                if self.running:
                    self.log(f"Receive error: {exc}")

    def _snapshot_game_state(self):
        with self.state_lock:
            players = [p.to_dict() for p in self.players.values()]
            phase = self.game_phase
            remaining = self.time_remaining
            targets = [t.to_dict() for t in self.targets.values()]
            revision = self.state_revision
        return players, phase, remaining, targets, revision

    def broadcast_loop(self):
        tick_rate = 20.0
        while self.running:
            try:
                with self.state_lock:
                    if self.game_phase == "playing":
                        elapsed = time.time() - self.game_start_time
                        self.time_remaining = max(0.0, self.game_duration - elapsed)
                        if self.time_remaining <= 0.0:
                            # end_game uses same lock, call outside
                            should_end = True
                        else:
                            should_end = False
                    else:
                        should_end = False

                if should_end:
                    self.end_game()

                players, phase, remaining, targets, revision = self._snapshot_game_state()
                if players:
                    game_state = Protocol.create_game_state(players, remaining, phase)
                    targets_state = Protocol.create_targets_state(targets, revision, time.time())
                    game_data = Protocol.encode(game_state)
                    targets_data = Protocol.encode(targets_state)
                    self._broadcast_raw(game_data)
                    self._broadcast_raw(targets_data)

                time.sleep(1.0 / tick_rate)
            except Exception as exc:
                if self.running:
                    self.log(f"Broadcast error: {exc}")

    def cleanup_loop(self):
        while self.running:
            try:
                now = time.time()
                disconnected = []
                with self.state_lock:
                    for player_id, player in self.players.items():
                        if now - player.last_update > 5.0:
                            disconnected.append(player_id)

                    for player_id in disconnected:
                        player = self.players.pop(player_id, None)
                        if player:
                            self.processed_shots.pop(player_id, None)
                            self.log(f"Player \"{player.name}\" timed out")

                    # target respawn
                    for target in self.targets.values():
                        if not target.alive and target.respawn_at > 0 and now >= target.respawn_at:
                            target.alive = True
                            target.respawn_at = 0.0
                            target.last_hit_by = None
                            target.pos = self._spawn_target_pos()
                            target.variant = self.target_mode
                            self.state_revision += 1

                    for player in self.players.values():
                        if not player.alive and player.respawn_at > 0 and now >= player.respawn_at:
                            self._spawn_player(player, avoid_last=True)

                time.sleep(0.05)
            except Exception as exc:
                if self.running:
                    self.log(f"Cleanup error: {exc}")

    def _broadcast_raw(self, data: bytes):
        with self.state_lock:
            addresses = [p.address for p in self.players.values()]
        for address in addresses:
            try:
                self.socket.sendto(data, address)
            except Exception:
                pass

    def broadcast_message(self, message: dict):
        self._broadcast_raw(Protocol.encode(message))

    def handle_message(self, message: dict, address: tuple):
        msg_type = message.get("type")
        if msg_type == MSG_CONNECT:
            self.handle_connect(message, address)
        elif msg_type == MSG_DISCONNECT:
            self.handle_disconnect(message)
        elif msg_type == MSG_PLAYER_STATE:
            self.handle_player_state(message, address)
        elif msg_type == MSG_PING:
            self.handle_ping(message, address)
        elif msg_type == MSG_HEARTBEAT:
            self.handle_heartbeat(message, address)
        elif msg_type == MSG_SHOT:
            self.handle_shot(message, address)
        elif msg_type == MSG_CHAT:
            self.handle_chat(message, address)

    def handle_connect(self, message: dict, address: tuple):
        player_id = message.get("player_id")
        name = message.get("name", "Unknown")
        if not player_id:
            return

        with self.state_lock:
            if len(self.players) >= self.max_players:
                self.log(f"Connection rejected (server full): {name} from {address[0]}")
                return

            if player_id not in self.players:
                # Получаем хитбоксы от клиента
                hitboxes = message.get("hitboxes")

                # Валидируем хитбоксы если они есть
                if hitboxes:
                    if self._validate_hitboxes(hitboxes):
                        self.log(f"Player \"{name}\" connected with custom hitboxes")
                    else:
                        self.log(f"Player \"{name}\" sent invalid hitboxes, using defaults")
                        hitboxes = None

                self.players[player_id] = Player(player_id, name, address, hitboxes)
                self._spawn_player(self.players[player_id], avoid_last=False)
                self.processed_shots[player_id] = set()
                self.log(f"Player \"{name}\" connected from {address[0]}:{address[1]}")

        self.print_players()

    def _validate_hitboxes(self, hitboxes: dict, max_radius: float = 2.0) -> bool:
        """Валидирует хитбоксы чтобы предотвратить читы"""
        if not isinstance(hitboxes, dict):
            return False

        required_parts = ["target_head", "target_body", "target_left_arm",
                         "target_right_arm", "target_legs"]

        for part in required_parts:
            if part not in hitboxes:
                return False

            hitbox = hitboxes[part]
            if not isinstance(hitbox, (list, tuple)) or len(hitbox) != 4:
                return False

            try:
                x, y, z, radius = float(hitbox[0]), float(hitbox[1]), float(hitbox[2]), float(hitbox[3])
            except (ValueError, TypeError):
                return False

            # Проверяем что радиус разумный
            if radius <= 0 or radius > max_radius:
                return False

            # Проверяем что позиция не слишком далеко от центра
            if abs(x) > 5.0 or abs(y) > 5.0 or abs(z) > 5.0:
                return False

        return True

    def handle_disconnect(self, message: dict):
        player_id = message.get("player_id")
        with self.state_lock:
            player = self.players.pop(player_id, None)
            self.processed_shots.pop(player_id, None)
        if player:
            self.log(f"Player \"{player.name}\" disconnected")
            self.print_players()

    def handle_player_state(self, message: dict, address: tuple):
        player_id = message.get("player_id")
        with self.state_lock:
            player = self.players.get(player_id)
            if not player:
                return
            now = time.time()
            player.last_update = now
            player.address = address
            if not player.alive:
                player.shooting = False
                return
            player.pos = _vec3(message.get("pos"), player.pos)
            player.heading = float(message.get("heading", player.heading))
            player.pitch = float(message.get("pitch", player.pitch))
            player.weapon = str(message.get("weapon", player.weapon))
            player.shooting = bool(message.get("shooting", player.shooting))
            # score is authoritative on server; ignore client score
            player.last_update = now
            player.address = address

    def handle_heartbeat(self, message: dict, address: tuple):
        player_id = message.get("player_id")
        with self.state_lock:
            player = self.players.get(player_id)
            if player:
                player.last_update = time.time()
                player.address = address

    def handle_ping(self, message: dict, address: tuple):
        pong = Protocol.create_pong(message.get("timestamp", 0))
        try:
            self.socket.sendto(Protocol.encode(pong), address)
        except Exception:
            pass

    def _spawn_target_pos(self):
        min_distance = 15.0
        max_distance = 35.0
        arena_width = 30.0
        return [
            random.uniform(-arena_width / 2.0, arena_width / 2.0),
            random.uniform(min_distance, max_distance),
            1.0,
        ]

    def _choose_player_spawn(self, avoid_index=None):
        available = list(range(len(PLAYER_SPAWN_POINTS)))
        if avoid_index in available and len(available) > 1:
            available.remove(avoid_index)
        spawn_index = random.choice(available)
        spawn = PLAYER_SPAWN_POINTS[spawn_index]
        return spawn_index, [float(spawn[0]), float(spawn[1]), float(spawn[2])]

    def _spawn_player(self, player: Player, avoid_last: bool = True):
        avoid_index = player.last_spawn_index if avoid_last else None
        spawn_index, spawn_pos = self._choose_player_spawn(avoid_index)
        player.last_spawn_index = spawn_index
        player.pos = spawn_pos
        player.hp = player.max_hp
        player.alive = True
        player.respawn_at = 0.0
        player.shooting = False
        player.last_shot_time = 0.0

    def _create_targets(self):
        self.targets.clear()
        self.next_target_id = 1
        for _ in range(self.target_count):
            target_id = f"t{self.next_target_id}"
            self.next_target_id += 1
            self.targets[target_id] = TargetState(
                target_id=target_id,
                pos=self._spawn_target_pos(),
                variant=self.target_mode,
            )
        self.state_revision += 1

    def start_game(self):
        with self.state_lock:
            if len(self.players) < 1:
                self.log("Cannot start: no players connected")
                return

            self.game_phase = "playing"
            self.game_start_time = time.time()
            self.time_remaining = float(self.game_duration)

            for player in self.players.values():
                player.score = 0
                player.kills = 0
                player.deaths = 0
                self._spawn_player(player, avoid_last=True)
            self._create_targets()

            addresses = [p.address for p in self.players.values()]

        self.log(f"Game started! Duration: {self.game_duration}s")
        start_msg = Protocol.create_game_start(self.game_duration)
        data = Protocol.encode(start_msg)
        for addr in addresses:
            try:
                self.socket.sendto(data, addr)
            except Exception:
                pass

    def end_game(self):
        with self.state_lock:
            self.game_phase = "finished"
            players = list(self.players.values())
            if not players:
                self.game_phase = "waiting"
                return
            winner = max(players, key=lambda p: p.score)
            final_scores = [
                (p.name, p.score) for p in sorted(players, key=lambda p: p.score, reverse=True)
            ]
            addresses = [p.address for p in players]
            self.game_phase = "waiting"

        self.log(f"Game ended! Winner: {winner.name} ({winner.score} points)")
        print("\n  Final Scores:")
        for i, (name, score) in enumerate(final_scores, 1):
            print(f"    {i}. {name}: {score} points")
        print()

        end_msg = Protocol.create_game_end(winner.player_id, winner.name, final_scores)
        data = Protocol.encode(end_msg)
        for addr in addresses:
            try:
                self.socket.sendto(data, addr)
            except Exception:
                pass

    def kick_player(self, name: str):
        kicked_player = None
        with self.state_lock:
            for player_id, player in list(self.players.items()):
                if player.name.lower() == name.lower():
                    kicked_player = self.players.pop(player_id, None)
                    self.processed_shots.pop(player_id, None)
                    break
        if kicked_player:
            self.log(f"Player \"{kicked_player.name}\" was kicked")
            self.print_players()
        else:
            self.log(f"Player \"{name}\" not found")

    def _ray_sphere_hit(self, origin, direction, center, radius):
        oc = [origin[0] - center[0], origin[1] - center[1], origin[2] - center[2]]
        b = _dot(oc, direction)
        c = _dot(oc, oc) - (radius * radius)
        discriminant = (b * b) - c
        if discriminant < 0:
            return None
        sqrt_discriminant = discriminant ** 0.5
        t = -b - sqrt_discriminant
        if t < 0:
            t = -b + sqrt_discriminant
        if t < 0:
            return None
        return [
            origin[0] + direction[0] * t,
            origin[1] + direction[1] * t,
            origin[2] + direction[2] * t,
        ]

    def _resolve_target_hit(self, origin, direction):
        best = None
        for target in self.targets.values():
            if not target.alive:
                continue
            tx, ty, tz = target.pos
            for part, offset in TARGET_PART_OFFSETS.items():
                ox, oy, oz, radius = offset
                center = [tx + ox, ty + oy, tz + oz]
                hit_pos = self._ray_sphere_hit(origin, direction, center, radius)
                if hit_pos is None:
                    continue
                dx = hit_pos[0] - origin[0]
                dy = hit_pos[1] - origin[1]
                dz = hit_pos[2] - origin[2]
                distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                if best is None or distance < best["distance"]:
                    best = {
                        "hit_type": "target",
                        "target": target,
                        "part": part,
                        "hit_pos": hit_pos,
                        "distance": distance,
                    }
        return best

    def _resolve_player_hit(self, shooter_id, origin, direction):
        best = None
        for player_id, player in self.players.items():
            if player_id == shooter_id or not player.alive:
                continue
            px, py, pz = player.pos
            # Используем хитбоксы конкретного игрока вместо глобальных
            for part, offset in player.hitboxes.items():
                ox, oy, oz, radius = offset
                center = [px + ox, py + oy, pz + oz]
                hit_pos = self._ray_sphere_hit(origin, direction, center, radius)
                if hit_pos is None:
                    continue
                dx = hit_pos[0] - origin[0]
                dy = hit_pos[1] - origin[1]
                dz = hit_pos[2] - origin[2]
                distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                if best is None or distance < best["distance"]:
                    best = {
                        "hit_type": "player",
                        "player": player,
                        "part": part,
                        "hit_pos": hit_pos,
                        "distance": distance,
                    }
        return best

    def _resolve_hit(self, shooter_id, origin, direction):
        target_hit = self._resolve_target_hit(origin, direction)
        player_hit = self._resolve_player_hit(shooter_id, origin, direction)
        if target_hit and player_hit:
            if player_hit["distance"] < target_hit["distance"]:
                return player_hit
            return target_hit
        return player_hit or target_hit

    def handle_shot(self, message: dict, address: tuple):
        now = time.time()
        player_id = message.get("player_id")
        shot_id = message.get("shot_id")
        if player_id is None or shot_id is None:
            return

        try:
            shot_id = int(shot_id)
        except (TypeError, ValueError):
            return

        with self.state_lock:
            player = self.players.get(player_id)
            if not player:
                return
            player.last_update = now
            player.address = address

            processed = self.processed_shots.setdefault(player_id, set())
            if shot_id in processed:
                return
            processed.add(shot_id)
            if len(processed) > 256:
                # keep dedup memory bounded
                processed.clear()
                processed.add(shot_id)

            weapon = str(message.get("weapon", player.weapon))
            player.weapon = weapon
            weapon_cfg = WEAPON_CONFIG.get(weapon, WEAPON_CONFIG["pistol"])
            min_interval = float(weapon_cfg["cooldown"])

            if not player.alive:
                return

            if now - player.last_shot_time < min_interval * 0.95:
                return
            player.last_shot_time = now

            origin = _vec3(message.get("origin"), player.pos)
            direction = _normalize(_vec3(message.get("dir"), (0.0, 1.0, 0.0)))
            resolved = self._resolve_hit(player_id, origin, direction)

            if not resolved:
                shot_result = Protocol.create_shot_result(
                    shot_id=shot_id,
                    shooter_id=player_id,
                    hit=False,
                    hit_type="none",
                    target_id=None,
                    part=None,
                    damage=0,
                    score_delta=0,
                    new_score=player.score,
                    hit_pos=None,
                    origin=origin,
                    direction=direction,
                    server_time=now,
                )
            else:
                part = resolved["part"]
                hit_pos = resolved["hit_pos"]
                base_damage = weapon_cfg["damage"]
                damage = int(base_damage * PART_MULTIPLIERS.get(part, 0.0))
                hit_type = resolved.get("hit_type", "none")
                if hit_type == "player":
                    victim = resolved["player"]
                    victim.hp = max(0, int(victim.hp - damage))
                    kill = victim.hp <= 0
                    score_delta = damage + (100 if kill else 0)
                    player.score += score_delta
                    if kill:
                        victim.alive = False
                        victim.respawn_at = now + PLAYER_RESPAWN_DELAY
                        victim.shooting = False
                        victim.deaths += 1
                        player.kills += 1
                    shot_result = Protocol.create_shot_result(
                        shot_id=shot_id,
                        shooter_id=player_id,
                        hit=True,
                        hit_type="player",
                        target_id=None,
                        part=part,
                        damage=damage,
                        score_delta=score_delta,
                        new_score=player.score,
                        victim_id=victim.player_id,
                        victim_name=victim.name,
                        victim_hp=victim.hp,
                        victim_alive=victim.alive,
                        kill=kill,
                        hit_pos=hit_pos,
                        origin=origin,
                        direction=direction,
                        server_time=now,
                    )
                else:
                    target = resolved["target"]
                    score_delta = damage
                    player.score += score_delta
                    target.alive = False
                    target.respawn_at = now + self.target_respawn_delay
                    target.last_hit_by = player_id
                    self.state_revision += 1
                    shot_result = Protocol.create_shot_result(
                        shot_id=shot_id,
                        shooter_id=player_id,
                        hit=True,
                        hit_type="target",
                        target_id=target.target_id,
                        part=part,
                        damage=damage,
                        score_delta=score_delta,
                        new_score=player.score,
                        hit_pos=hit_pos,
                        origin=origin,
                        direction=direction,
                        server_time=now,
                    )

        self.broadcast_message(shot_result)

    def handle_chat(self, message: dict, address: tuple):
        now = time.time()
        player_id = message.get("player_id")
        text = str(message.get("text", "")).strip()
        if not player_id or not text:
            return
        text = text[:180]

        with self.state_lock:
            player = self.players.get(player_id)
            if not player:
                return
            player.last_update = now
            player.address = address
            chat_msg = Protocol.create_chat_message(
                player_id=player.player_id,
                name=player.name,
                text=text,
                server_time=now,
            )
        self.broadcast_message(chat_msg)

    def snapshot_status(self) -> dict:
        with self.state_lock:
            players = [
                {
                    "id": p.player_id,
                    "name": p.name,
                    "score": p.score,
                    "ping": p.ping,
                    "hp": p.hp,
                    "alive": p.alive,
                    "kills": p.kills,
                    "deaths": p.deaths,
                }
                for p in self.players.values()
            ]
            players.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
            return {
                "running": self.running,
                "phase": self.game_phase,
                "time_remaining": float(self.time_remaining),
                "port": self.port,
                "max_players": self.max_players,
                "players": players,
                "target_count": self.target_count,
                "target_respawn_delay": self.target_respawn_delay,
                "target_mode": self.target_mode,
            }

    def execute_command(self, cmd_raw: str) -> bool:
        cmd_raw = (cmd_raw or "").strip()
        if not cmd_raw:
            return True
        cmd = cmd_raw.lower()

        if cmd == "start":
            self.start_game()
            return True

        if cmd == "stop":
            with self.state_lock:
                in_progress = self.game_phase == "playing"
            if in_progress:
                self.end_game()
            else:
                self.log("No game in progress")
            return True

        if cmd.startswith("kick "):
            name = cmd_raw[5:].strip()
            if name:
                self.kick_player(name)
            else:
                self.log("Usage: kick <name>")
            return True

        if cmd.startswith("set "):
            self.handle_set_command(cmd_raw[4:].strip())
            return True

        if cmd == "status":
            snapshot = self.snapshot_status()
            print(f"\nGame Phase: {snapshot['phase']}")
            if snapshot["phase"] == "playing":
                print(f"Time Remaining: {snapshot['time_remaining']:.1f}s")
            print(
                f"Target Count: {snapshot['target_count']} | "
                f"Respawn: {snapshot['target_respawn_delay']:.2f}s | "
                f"Mode: {snapshot['target_mode']}"
            )
            self.print_players()
            return True

        if cmd in ("quit", "exit"):
            self.log("Shutting down server...")
            self.running = False
            return False

        if cmd == "help":
            self.print_help()
            return True

        self.log("Unknown command. Use: start, stop, kick <name>, set <key> <value>, status, quit")
        return True

    def command_loop(self):
        while self.running:
            try:
                cmd_raw = input().strip()
                should_continue = self.execute_command(cmd_raw)
                if not should_continue:
                    break
            except EOFError:
                break
            except KeyboardInterrupt:
                self.log("Shutting down server...")
                self.running = False
                break

    def handle_set_command(self, args: str):
        parts = args.split()
        if len(parts) < 2:
            self.log("Usage: set <targets|respawn|duration|mode> <value>")
            return

        key = parts[0].lower()
        value = " ".join(parts[1:]).strip()
        now = time.time()

        with self.state_lock:
            if key == "targets":
                try:
                    new_count = max(1, min(100, int(value)))
                except ValueError:
                    self.log("Invalid targets value")
                    return
                self.target_count = new_count
                self._create_targets()
                msg = f"[SERVER] target_count set to {new_count}"
            elif key == "respawn":
                try:
                    new_respawn = max(0.1, min(30.0, float(value)))
                except ValueError:
                    self.log("Invalid respawn value")
                    return
                self.target_respawn_delay = new_respawn
                msg = f"[SERVER] target_respawn_delay set to {new_respawn:.2f}s"
            elif key == "duration":
                try:
                    new_duration = max(10, min(3600, int(value)))
                except ValueError:
                    self.log("Invalid duration value")
                    return
                self.game_duration = new_duration
                msg = f"[SERVER] game_duration set to {new_duration}s"
            elif key == "mode":
                raw_mode = value.lower()
                if raw_mode in ("nsfw", "on", "1", "true"):
                    self.target_mode = "nsfw"
                elif raw_mode in ("sfw", "safe", "off", "0", "false"):
                    self.target_mode = "sfw"
                else:
                    self.target_mode = raw_mode[:32] or "default"
                for target in self.targets.values():
                    target.variant = self.target_mode
                self.state_revision += 1
                msg = f"[SERVER] target_mode set to {self.target_mode}"
            else:
                self.log("Unknown set key. Use: targets, respawn, duration, mode")
                return

            chat_msg = Protocol.create_chat_message(
                player_id="server",
                name="SERVER",
                text=msg,
                server_time=now,
            )

        self.log(msg)
        self.broadcast_message(chat_msg)

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None


def main():
    port = 7777
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
