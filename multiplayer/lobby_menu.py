"""
UI для лобби мультиплеера
"""
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectEntry, 
    DGG, DirectScrolledList
)
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, WindowProperties
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpColorScaleInterval, Func

class LobbyMenu:
    """Меню лобби для мультиплеера"""
    
    def __init__(self, game):
        self.game = game
        self.visible = False
        self.on_connect_callback = None
        self.on_back_callback = None
        
        self.create_menu()
    
    def create_menu(self):
        """Создает UI лобби"""
        # Затемненный фон
        self.dark_bg = DirectFrame(
            frameColor=(0.05, 0.05, 0.05, 0.9),
            frameSize=(-2, 2, -2, 2),
            relief=DGG.FLAT,
            parent=self.game.render2d
        )
        self.dark_bg.hide()
        
        # Основной фрейм
        self.frame = DirectFrame(
            frameColor=(0.08, 0.08, 0.12, 0.98),
            frameSize=(-0.7, 0.7, -0.55, 0.55),
            relief=DGG.FLAT,
            pos=(0, 0, 0)
        )
        self.frame.hide()
        
        # Декоративные линии
        DirectFrame(
            frameColor=(0.3, 0.5, 1, 0.8),
            frameSize=(-0.65, 0.65, -0.002, 0.002),
            relief=DGG.FLAT,
            pos=(0, 0, 0.53),
            parent=self.frame
        )
        DirectFrame(
            frameColor=(0.3, 0.5, 1, 0.8),
            frameSize=(-0.65, 0.65, -0.002, 0.002),
            relief=DGG.FLAT,
            pos=(0, 0, -0.53),
            parent=self.frame
        )
        
        # Заголовок
        self.title = DirectLabel(
            text="MULTIPLAYER",
            scale=0.1,
            pos=(0, 0, 0.42),
            parent=self.frame,
            text_fg=(0.9, 0.95, 1, 1),
            text_align=TextNode.ACenter,
            text_shadow=(0.2, 0.4, 0.8, 0.8),
            text_shadowOffset=(0.003, -0.003),
            frameColor=(0, 0, 0, 0)
        )
        
        # Стиль для labels
        label_style = {
            'frameColor': (0, 0, 0, 0),
            'text_fg': (0.9, 0.9, 0.9, 1),
            'text_scale': 0.045,
            'text_align': TextNode.ALeft
        }
        
        # Стиль для кнопок
        button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.25, 0.25, -0.04, 0.04),
            'text_scale': 0.045,
            'text_fg': (0.95, 0.95, 0.95, 1),
            'pressEffect': 0
        }
        
        # Поле имени игрока
        DirectLabel(
            text="Your Name:",
            pos=(-0.55, 0, 0.25),
            parent=self.frame,
            **label_style
        )
        
        self.name_entry = DirectEntry(
            text="",
            scale=0.05,
            pos=(-0.1, 0, 0.25),
            width=12,
            numLines=1,
            focus=0,
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            text_fg=(1, 1, 1, 1),
            initialText="Player"
        )
        
        # Поле IP сервера
        DirectLabel(
            text="Server IP:",
            pos=(-0.55, 0, 0.12),
            parent=self.frame,
            **label_style
        )
        
        self.ip_entry = DirectEntry(
            text="",
            scale=0.05,
            pos=(-0.1, 0, 0.12),
            width=12,
            numLines=1,
            focus=0,
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            text_fg=(1, 1, 1, 1),
            initialText="127.0.0.1"
        )
        
        # Порт
        DirectLabel(
            text="Port:",
            pos=(-0.55, 0, -0.01),
            parent=self.frame,
            **label_style
        )
        
        self.port_entry = DirectEntry(
            text="",
            scale=0.05,
            pos=(-0.1, 0, -0.01),
            width=6,
            numLines=1,
            focus=0,
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            text_fg=(1, 1, 1, 1),
            initialText="7777"
        )

        # Статус подключения
        self.status_label = DirectLabel(
            text="Not connected",
            pos=(0, 0, -0.15),
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
            text_fg=(0.7, 0.7, 0.7, 1),
            text_scale=0.04,
            text_align=TextNode.ACenter
        )
        
        # Список игроков
        DirectLabel(
            text="Players in lobby:",
            pos=(-0.55, 0, -0.25),
            parent=self.frame,
            **label_style
        )

        # Фрейм для списка игроков
        self.players_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.15, 0.9),
            frameSize=(-0.5, 0.5, -0.15, 0.08),
            relief=DGG.FLAT,
            pos=(0, 0, -0.38),
            parent=self.frame
        )
        
        self.player_labels = []
        for i in range(8):
            label = DirectLabel(
                text="",
                pos=(-0.45 + (i % 4) * 0.23, 0, 0.02 - (i // 4) * 0.08),
                parent=self.players_frame,
                frameColor=(0, 0, 0, 0),
                text_fg=(0.8, 0.8, 0.8, 1),
                text_scale=0.035,
                text_align=TextNode.ALeft
            )
            self.player_labels.append(label)
        
        # Кнопка Connect
        self.connect_button = DirectButton(
            text="CONNECT",
            command=self.on_connect,
            pos=(-0.45, 0, -0.48),
            parent=self.frame,
            frameColor=(0.2, 0.5, 0.3, 0.9),
            **button_style
        )
        self.connect_button.bind(DGG.ENTER, self.button_hover_start, [self.connect_button])
        self.connect_button.bind(DGG.EXIT, self.button_hover_end, [self.connect_button])
        
        # Кнопка Start Game (скрыта по умолчанию, показывается когда подключен)
        self.start_game_button = DirectButton(
            text="START GAME",
            command=self.on_start_game,
            pos=(0, 0, -0.48),
            parent=self.frame,
            frameColor=(0.2, 0.4, 0.9, 0.9),
            **button_style
        )
        self.start_game_button.bind(DGG.ENTER, self.button_hover_start, [self.start_game_button])
        self.start_game_button.bind(DGG.EXIT, self.button_hover_end, [self.start_game_button])
        self.start_game_button.hide()
        
        # Кнопка Disconnect (скрыта по умолчанию)
        self.disconnect_button = DirectButton(
            text="DISCONNECT",
            command=self.on_disconnect,
            pos=(-0.45, 0, -0.48),
            parent=self.frame,
            frameColor=(0.5, 0.2, 0.2, 0.9),
            **button_style
        )
        self.disconnect_button.bind(DGG.ENTER, self.button_hover_start, [self.disconnect_button])
        self.disconnect_button.bind(DGG.EXIT, self.button_hover_end, [self.disconnect_button])
        self.disconnect_button.hide()
        
        # Кнопка Back
        self.back_button = DirectButton(
            text="BACK",
            command=self.on_back,
            pos=(0.45, 0, -0.48),
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            **button_style
        )
        self.back_button.bind(DGG.ENTER, self.button_hover_start, [self.back_button])
        self.back_button.bind(DGG.EXIT, self.button_hover_end, [self.back_button])
        
        # Ping display
        self.ping_label = DirectLabel(
            text="Ping: --",
            pos=(0.5, 0, 0.42),
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
            text_fg=(0.6, 0.6, 0.6, 1),
            text_scale=0.035,
            text_align=TextNode.ARight
        )
    
    def button_hover_start(self, button, event):
        """Эффект при наведении"""
        LerpColorScaleInterval(button, 0.15, (1.15, 1.15, 1.15, 1)).start()

    def button_hover_end(self, button, event):
        """Эффект при отведении"""
        LerpColorScaleInterval(button, 0.15, (1, 1, 1, 1)).start()

    def select_mode(self, mode: str):
        """Выбор режима игры"""
        self.selected_mode = mode
        if mode == "hybrid":
            self.hybrid_button['frameColor'] = (0.2, 0.4, 0.9, 0.9)
            self.hybrid_button['text_fg'] = (0.95, 0.95, 0.95, 1)
            self.pvp_button['frameColor'] = (0.15, 0.15, 0.2, 0.7)
            self.pvp_button['text_fg'] = (0.7, 0.7, 0.7, 1)
        else:
            self.pvp_button['frameColor'] = (0.9, 0.3, 0.3, 0.9)
            self.pvp_button['text_fg'] = (0.95, 0.95, 0.95, 1)
            self.hybrid_button['frameColor'] = (0.15, 0.15, 0.2, 0.7)
            self.hybrid_button['text_fg'] = (0.7, 0.7, 0.7, 1)
    
    def show(self):
        """Показывает меню"""
        self.visible = True
        self.dark_bg.show()
        self.frame.show()
        
        # Показываем курсор
        props = WindowProperties()
        props.setCursorHidden(False)
        self.game.win.requestProperties(props)
        
        # Анимация появления
        self.frame.setColorScale(1, 1, 1, 0)
        self.dark_bg.setColorScale(1, 1, 1, 0)
        Parallel(
            LerpColorScaleInterval(self.frame, 0.3, (1, 1, 1, 1)),
            LerpColorScaleInterval(self.dark_bg, 0.3, (1, 1, 1, 1))
        ).start()
        
        # Запускаем обновление UI
        self.game.taskMgr.add(self.update_task, "lobby_update")
    
    def hide(self):
        """Скрывает меню"""
        self.visible = False
        
        # Останавливаем обновление
        self.game.taskMgr.remove("lobby_update")
        
        # Анимация исчезновения
        Sequence(
            Parallel(
                LerpColorScaleInterval(self.frame, 0.2, (1, 1, 1, 0)),
                LerpColorScaleInterval(self.dark_bg, 0.2, (1, 1, 1, 0))
            ),
            Func(self.frame.hide),
            Func(self.dark_bg.hide)
        ).start()
    
    def update_task(self, task):
        """Обновляет UI лобби"""
        if not self.visible:
            return task.done
        
        # Обновляем статус подключения
        if hasattr(self.game, 'network') and self.game.network and self.game.network.is_connected():
            self.status_label.setText("Connected to server")
            self.status_label['text_fg'] = (0.3, 0.8, 0.3, 1)
            self.connect_button.hide()
            self.disconnect_button.show()
            self.start_game_button.show()
            
            # Обновляем ping
            ping = self.game.network.get_ping()
            self.ping_label.setText(f"Ping: {ping}ms")
            
            # Обновляем список игроков
            remote_players = self.game.network.get_remote_players()
            
            # Очищаем старые labels
            for label in self.player_labels:
                label.setText("")
            
            # Показываем себя
            self.player_labels[0].setText(f"• {self.game.network.player_name} (you)")
            self.player_labels[0]['text_fg'] = (0.3, 0.8, 1.0, 1)
            
            # Показываем других игроков
            for i, (player_id, player_data) in enumerate(remote_players.items()):
                if i + 1 < len(self.player_labels):
                    name = player_data.get("name", "Unknown")
                    score = player_data.get("score", 0)
                    self.player_labels[i + 1].setText(f"• {name}: {score}")
                    self.player_labels[i + 1]['text_fg'] = (0.8, 0.8, 0.8, 1)
        else:
            self.status_label.setText("Not connected")
            self.status_label['text_fg'] = (0.7, 0.7, 0.7, 1)
            self.connect_button.show()
            self.disconnect_button.hide()
            self.start_game_button.hide()
            self.ping_label.setText("Ping: --")
            
            # Очищаем список игроков
            for label in self.player_labels:
                label.setText("")
        
        return task.cont
    
    def on_connect(self):
        """Обработчик кнопки Connect"""
        player_name = self.name_entry.get().strip() or "Player"
        server_ip = self.ip_entry.get().strip() or "127.0.0.1"
        
        try:
            port = int(self.port_entry.get().strip() or "7777")
        except ValueError:
            port = 7777
        
        self.status_label.setText("Connecting...")
        self.status_label['text_fg'] = (1, 1, 0.3, 1)
        
        if self.on_connect_callback:
            self.on_connect_callback(server_ip, port, player_name)
    
    def on_disconnect(self):
        """Обработчик кнопки Disconnect"""
        if hasattr(self.game, 'network') and self.game.network:
            self.game.network.disconnect()
    
    def on_start_game(self):
        """Обработчик кнопки Start Game"""
        if hasattr(self.game, 'start_multiplayer_game'):
            self.game.start_multiplayer_game()
    
    def on_back(self):
        """Обработчик кнопки Back"""
        self.hide()
        if self.on_back_callback:
            self.on_back_callback()
    
    def set_connect_callback(self, callback):
        """Устанавливает callback для подключения"""
        self.on_connect_callback = callback
    
    def set_back_callback(self, callback):
        """Устанавливает callback для кнопки Back"""
        self.on_back_callback = callback
    
    def set_connection_status(self, connected: bool, message: str = ""):
        """Устанавливает статус подключения"""
        if connected:
            self.status_label.setText(message or "Connected")
            self.status_label['text_fg'] = (0.3, 0.8, 0.3, 1)
        else:
            self.status_label.setText(message or "Connection failed")
            self.status_label['text_fg'] = (0.8, 0.3, 0.3, 1)
    
    def destroy(self):
        """Удаляет меню"""
        self.game.taskMgr.remove("lobby_update")
        if self.frame:
            self.frame.destroy()
        if self.dark_bg:
            self.dark_bg.destroy()

