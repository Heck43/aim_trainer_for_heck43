import time
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, CardMaker, TransparencyAttrib

# минималистичные цвета для HUD
TEXT_PRIMARY = (0.90, 0.90, 0.91, 1.0)
TEXT_SECONDARY = (0.68, 0.68, 0.70, 1.0)
ACCENT_ORANGE = (1.0, 0.58, 0.0, 1.0)
ACCENT_GREEN = (0.20, 0.78, 0.35, 1.0)
ACCENT_RED = (1.0, 0.23, 0.19, 1.0)


class HudManager:
    """управляет всеми HUD элементами игры~~"""

    def __init__(self, game):
        self.game = game

        # счёт и таймер
        self.score_text = OnscreenText(
            text="Score: 0",
            pos=(-1.3, 0.9),
            fg=TEXT_PRIMARY,
            align=TextNode.ALeft,
            scale=0.07,
            mayChange=True
        )
        self.score_text.hide()

        self.timer_text = OnscreenText(
            text="Time: 0.0",
            pos=(-0.0, -0.9),
            fg=TEXT_PRIMARY,
            align=TextNode.ACenter,
            scale=0.07,
            shadow=(0, 0, 0, 0.5)
        )
        self.timer_text.hide()

        # таблица мультиплеера
        self.scoreboard_text = OnscreenText(
            text="",
            pos=(1.25, 0.86),
            fg=TEXT_PRIMARY,
            align=TextNode.ARight,
            scale=0.05,
            mayChange=True,
        )
        self.scoreboard_text.hide()

        # HP и K/D для мультиплеера
        self.hp_text = OnscreenText(
            text="HP: 100/100",
            pos=(-1.3, 0.82),
            fg=ACCENT_GREEN,
            align=TextNode.ALeft,
            scale=0.06,
            mayChange=True,
        )
        self.hp_text.hide()

        self.kd_text = OnscreenText(
            text="K/D: 0/0",
            pos=(-1.3, 0.74),
            fg=TEXT_SECONDARY,
            align=TextNode.ALeft,
            scale=0.055,
            mayChange=True,
        )
        self.kd_text.hide()

        # индикатор режима игры
        self.mode_text = OnscreenText(
            text="",
            pos=(0, 0.9),
            fg=ACCENT_ORANGE,
            align=TextNode.ACenter,
            scale=0.06,
            mayChange=True,
            shadow=(0, 0, 0, 0.5)
        )
        self.mode_text.hide()

        # оверлей смерти
        death_overlay_cm = CardMaker("death_overlay")
        death_overlay_cm.setFrame(-1, 1, -1, 1)
        self.death_overlay = self.game.render2d.attachNewNode(death_overlay_cm.generate())
        self.death_overlay.setTransparency(TransparencyAttrib.MAlpha)
        self.death_overlay.setColor(0.15, 0.0, 0.0, 0.5)
        self.death_overlay.hide()

        self.death_text = OnscreenText(
            text="",
            pos=(0, 0.12),
            fg=TEXT_PRIMARY,
            align=TextNode.ACenter,
            scale=0.09,
            mayChange=True,
        )
        self.death_text.hide()

        # вспышка урона
        hurt_flash_cm = CardMaker("hurt_flash")
        hurt_flash_cm.setFrame(-1, 1, -1, 1)
        self.hurt_flash = self.game.render2d.attachNewNode(hurt_flash_cm.generate())
        self.hurt_flash.setTransparency(TransparencyAttrib.MAlpha)
        self.hurt_flash.setColor(0.8, 0.05, 0.05, 0.0)
        self.hurt_flash.hide()

        self.hurt_flash_alpha = 0.0

    def update_score_display(self):
        """Обновляет отображение счета"""
        self.score_text.setText(f"Score: {self.game.score}")

    def update_timer_display(self):
        """Обновляет отображение таймера"""
        minutes = int(self.game.game_time) // 60
        seconds = int(self.game.game_time) % 60
        self.timer_text.setText(f"Time: {minutes}:{seconds:02d}")

    def update_timer_task(self, task):
        """Таск для обновления таймера"""
        if not self.game.show_timer:
            return task.done
        self.game.game_time = time.time() - self.game.start_time
        self.update_timer_display()
        return task.cont

    def update_multiplayer_hud(self):
        """Обновляет HUD для мультиплеера"""
        if not (self.game.is_multiplayer and self.game.network and self.game.network.is_connected()):
            self.hp_text.hide()
            self.kd_text.hide()
            self.death_overlay.hide()
            self.death_text.hide()
            self.mode_text.hide()
            return

        self.hp_text.show()
        self.kd_text.show()
        self.kd_text.setText(f"K/D: {self.game.mp_local_kills}/{self.game.mp_local_deaths}")

        # Показываем индикатор режима
        if hasattr(self.game.network, 'game_mode'):
            if self.game.network.game_mode == "pvp":
                self.mode_text.setText("PVP MODE")
                self.mode_text.show()
            elif self.game.network.game_mode == "pve":
                self.mode_text.setText("PVE MODE")
                self.mode_text.show()
            else:
                self.mode_text.hide()
        else:
            self.mode_text.hide()

        if self.game.mp_local_alive:
            hp_ratio = self.game.mp_local_hp / max(1, self.game.mp_local_max_hp)
            if hp_ratio > 0.6:
                color = (0.5, 1.0, 0.5, 1)
            elif hp_ratio > 0.3:
                color = (1.0, 1.0, 0.3, 1)
            else:
                color = (1.0, 0.3, 0.3, 1)
            self.hp_text.setFg(color)
            self.hp_text.setText(f"HP: {self.game.mp_local_hp}/{self.game.mp_local_max_hp}")
            self.death_overlay.hide()
            self.death_text.hide()
        else:
            self.hp_text.setText("HP: 0/100")
            self.hp_text.setFg((1.0, 0.3, 0.3, 1))
            now = time.time()
            remaining = max(0.0, self.game.mp_local_respawn_at - now)
            if remaining > 0:
                self.death_overlay.show()
                self.death_text.setText(f"You died!\nRespawning in {remaining:.1f}s")
                self.death_text.show()
            else:
                self.death_overlay.hide()
                self.death_text.hide()

    def trigger_hurt_flash(self, intensity=0.6):
        """Показывает красную вспышку при получении урона"""
        clamped = max(0.0, min(0.85, float(intensity)))
        self.hurt_flash_alpha = max(self.hurt_flash_alpha, clamped)
        self.hurt_flash.show()

    def hide_all(self):
        """Скрывает все HUD элементы"""
        self.score_text.hide()
        self.timer_text.hide()
        self.scoreboard_text.hide()
        self.hp_text.hide()
        self.kd_text.hide()
        self.death_overlay.hide()
        self.death_text.hide()
        self.hurt_flash.hide()
        self.mode_text.hide()

    def show_game_hud(self):
        """Показывает HUD для обычной игры"""
        if self.game.show_score:
            self.score_text.show()
        if self.game.show_timer:
            self.timer_text.show()

    def reset_hurt_flash(self):
        """Сбрасывает эффект вспышки урона"""
        self.hurt_flash_alpha = 0.0
        self.hurt_flash.hide()
