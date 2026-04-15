import time
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectEntry
from panda3d.core import TextNode


class ChatManager:
    """Управляет чатом в мультиплеере"""

    def __init__(self, game):
        self.game = game
        self.is_chat_active = False
        self.chat_messages = []
        self.chat_message_lifetime = 10.0
        self.chat_last_toggle_time = 0.0

        # Create chat UI elements
        self.chat_text = OnscreenText(
            text="",
            pos=(-1.28, -0.80),
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            scale=0.04,
            mayChange=True,
        )
        self.chat_text.hide()

        self.chat_entry = DirectEntry(
            text="",
            scale=0.05,
            pos=(-1.28, 0, -0.93),
            frameColor=(0, 0, 0, 0.7),
            text_fg=(1, 1, 1, 1),
            initialText="",
            numLines=1,
            width=28,
            focus=0,
            command=self.submit_chat_message,
            suppressKeys=False,
        )
        self.chat_entry.hide()

    def add_chat_line(self, name: str, text: str):
        """Добавляет сообщение в чат"""
        clean_name = (name or "Player").strip()[:24]
        clean_text = (text or "").strip()[:180]
        if not clean_text:
            return
        self.chat_messages.append({
            "t": time.time(),
            "line": f"{clean_name}: {clean_text}",
        })
        if len(self.chat_messages) > 30:
            self.chat_messages = self.chat_messages[-30:]
        self.refresh_chat_display()

    def refresh_chat_display(self):
        """Обновляет отображение чата"""
        now = time.time()
        if self.is_chat_active:
            visible = self.chat_messages[-8:]
        else:
            self.chat_messages = [
                m for m in self.chat_messages
                if now - float(m.get("t", now)) <= self.chat_message_lifetime
            ]
            visible = self.chat_messages[-6:]

        if not visible:
            self.chat_text.setText("")
            self.chat_text.hide()
            return

        lines = [m.get("line", "") for m in reversed(visible)]
        self.chat_text.setText("\n".join(lines))
        self.chat_text.show()

    def toggle_chat_input(self):
        """Переключает ввод чата"""
        now = time.time()
        if now - self.chat_last_toggle_time < 0.2:
            return
        self.chat_last_toggle_time = now

        if self.game.is_splash_screen_active:
            return
        if not (self.game.is_multiplayer and self.game.network and self.game.network.is_connected()):
            return

        if not self.is_chat_active:
            self.is_chat_active = True
            self.chat_entry.enterText("")
            self.chat_entry.show()
            self.chat_entry["focus"] = 1
            self.game.mouse_pressed = False
            for key in self.game.keyMap:
                self.game.keyMap[key] = False
            self.refresh_chat_display()
        else:
            self.close_chat_input()

    def submit_chat_message(self, text):
        """Отправляет сообщение в чат"""
        if self.game.network and self.game.network.is_connected():
            msg = (text or "").strip()
            if msg:
                self.game.network.send_chat(msg)
        self.chat_entry.enterText("")
        self.close_chat_input()

    def close_chat_input(self):
        """Закрывает ввод чата"""
        self.chat_entry["focus"] = 0
        self.chat_entry.hide()
        self.is_chat_active = False
        self.chat_last_toggle_time = time.time()
        self.refresh_chat_display()

    def cleanup(self):
        """Очищает ресурсы чата"""
        self.chat_entry["focus"] = 0
        self.chat_entry.hide()
        self.chat_text.hide()
