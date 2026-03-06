"""
Graphical wrapper for multiplayer server.
Keeps console server implementation intact and reuses GameServer commands.
"""
import sys

try:
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QLineEdit,
        QSpinBox,
        QDoubleSpinBox,
        QComboBox,
    )
except ImportError:
    try:
        from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
        from PySide6.QtWidgets import (
            QApplication,
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QTextEdit,
            QLineEdit,
            QSpinBox,
            QDoubleSpinBox,
            QComboBox,
        )
    except ImportError:
        print("GUI server requires PyQt5 or PySide6.")
        print("Install one of:")
        print("  pip install pyqt5")
        print("  pip install pyside6")
        sys.exit(1)

from multiplayer.server import GameServer


class ServerWindow(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.server = None
        self.setWindowTitle("Aim Trainer MP Server (GUI)")
        self.resize(980, 680)
        self._build_ui()
        self.log_signal.connect(self._append_log)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(400)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(7777)
        top.addWidget(self.port_spin)

        top.addWidget(QLabel("Max players:"))
        self.max_players_spin = QSpinBox()
        self.max_players_spin.setRange(1, 64)
        self.max_players_spin.setValue(8)
        top.addWidget(self.max_players_spin)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_server)
        top.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        top.addWidget(self.stop_btn)

        self.status_btn = QPushButton("Status")
        self.status_btn.clicked.connect(lambda: self.run_command("status"))
        top.addWidget(self.status_btn)

        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(lambda: self.run_command("help"))
        top.addWidget(self.help_btn)

        top.addStretch(1)
        root.addLayout(top)

        settings = QHBoxLayout()
        settings.addWidget(QLabel("Targets:"))
        self.targets_spin = QSpinBox()
        self.targets_spin.setRange(1, 100)
        self.targets_spin.setValue(10)
        settings.addWidget(self.targets_spin)

        settings.addWidget(QLabel("Respawn:"))
        self.respawn_spin = QDoubleSpinBox()
        self.respawn_spin.setRange(0.1, 30.0)
        self.respawn_spin.setDecimals(2)
        self.respawn_spin.setSingleStep(0.1)
        self.respawn_spin.setValue(3.0)
        settings.addWidget(self.respawn_spin)

        settings.addWidget(QLabel("Duration:"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 3600)
        self.duration_spin.setValue(60)
        settings.addWidget(self.duration_spin)

        settings.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["nsfw", "sfw"])
        settings.addWidget(self.mode_combo)

        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.clicked.connect(self.apply_settings)
        settings.addWidget(self.apply_btn)

        settings.addStretch(1)
        root.addLayout(settings)

        cmd = QHBoxLayout()
        cmd.addWidget(QLabel("Command:"))
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("Examples: start | set targets 20 | kick Player")
        self.command_edit.returnPressed.connect(self.on_send_command)
        cmd.addWidget(self.command_edit, 1)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send_command)
        cmd.addWidget(self.send_btn)
        root.addLayout(cmd)

        stats = QHBoxLayout()
        self.phase_label = QLabel("Phase: -")
        self.time_label = QLabel("Time: -")
        self.players_label = QLabel("Players: 0/0")
        self.targets_label = QLabel("Targets: -")
        for label in (self.phase_label, self.time_label, self.players_label, self.targets_label):
            stats.addWidget(label)
        stats.addStretch(1)
        root.addLayout(stats)

        main = QHBoxLayout()
        self.players_view = QTextEdit()
        self.players_view.setReadOnly(True)
        self.players_view.setPlaceholderText("Players will appear here...")
        main.addWidget(self.players_view, 1)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Server log...")
        main.addWidget(self.log_view, 2)
        root.addLayout(main, 1)

    def _append_log(self, line: str):
        self.log_view.append(line)

    def _log(self, text: str):
        self._append_log(text)

    def _on_server_log(self, line: str):
        self.log_signal.emit(line)

    def start_server(self):
        if self.server and self.server.running:
            return
        port = int(self.port_spin.value())
        max_players = int(self.max_players_spin.value())
        try:
            self.server = GameServer(port=port, max_players=max_players)
            self.server.log_callback = self._on_server_log
            self.server.start(interactive=False, print_banner=False)
            self._log(f"[GUI] Server started on port {port}")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.port_spin.setEnabled(False)
            self.max_players_spin.setEnabled(False)
            self.apply_settings()
        except Exception as exc:
            self._log(f"[GUI] Failed to start server: {exc}")
            self.server = None

    def stop_server(self):
        if not self.server:
            return
        try:
            self.server.stop()
            self._log("[GUI] Server stopped")
        except Exception as exc:
            self._log(f"[GUI] Stop error: {exc}")
        self.server = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.port_spin.setEnabled(True)
        self.max_players_spin.setEnabled(True)
        self.phase_label.setText("Phase: -")
        self.time_label.setText("Time: -")
        self.players_label.setText("Players: 0/0")
        self.targets_label.setText("Targets: -")
        self.players_view.clear()

    def run_command(self, cmd: str):
        if not self.server or not self.server.running:
            self._log("[GUI] Server is not running")
            return
        try:
            self.server.execute_command(cmd)
        except Exception as exc:
            self._log(f"[GUI] Command error: {exc}")

    def on_send_command(self):
        cmd = self.command_edit.text().strip()
        if not cmd:
            return
        self._log(f"> {cmd}")
        self.run_command(cmd)
        self.command_edit.clear()

    def apply_settings(self):
        if not self.server or not self.server.running:
            return
        self.run_command(f"set targets {self.targets_spin.value()}")
        self.run_command(f"set respawn {self.respawn_spin.value():.2f}")
        self.run_command(f"set duration {self.duration_spin.value()}")
        self.run_command(f"set mode {self.mode_combo.currentText()}")

    def refresh_status(self):
        if not self.server or not self.server.running:
            return
        try:
            snap = self.server.snapshot_status()
        except Exception:
            return

        self.phase_label.setText(f"Phase: {snap['phase']}")
        self.time_label.setText(f"Time: {snap['time_remaining']:.1f}s")
        self.players_label.setText(f"Players: {len(snap['players'])}/{snap['max_players']}")
        self.targets_label.setText(
            f"Targets: {snap['target_count']} | Respawn: {snap['target_respawn_delay']:.2f}s | Mode: {snap['target_mode']}"
        )
        lines = [f"{p['name']} | score={p['score']} | ping={p['ping']}ms" for p in snap["players"]]
        self.players_view.setPlainText("\n".join(lines))

    def closeEvent(self, event):
        self.stop_server()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = ServerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
