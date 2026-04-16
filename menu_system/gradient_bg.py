"""
градиентный фон с медленной анимацией~~
"""
from direct.gui.DirectGui import DirectFrame, DGG
from panda3d.core import CardMaker, NodePath, Texture, PNMImage
from direct.interval.IntervalGlobal import LerpColorInterval, Sequence
import random

# цвета
DARKER_BG = (0.17, 0.17, 0.18, 0.98)
BLACK_BG = (0.0, 0.0, 0.0, 1.0)


class GradientBackground:
    def __init__(self, game):
        self.game = game
        self.root = self.game.render2d.attachNewNode("gradient_bg")

        # создаём градиентный фон
        self.create_gradient()

        # добавляем тонкие линии
        self.create_grid_lines()

        # запускаем анимацию
        self.start_animation()

    def create_gradient(self):
        """создаёт вертикальный градиент от тёмно-серого к чёрному~~"""
        cm = CardMaker('gradient_card')
        cm.setFrame(-2, 2, -2, 2)

        self.gradient_card = self.root.attachNewNode(cm.generate())
        self.gradient_card.setTransparency(1)

        # создаём текстуру градиента
        img = PNMImage(2, 256)
        for y in range(256):
            # интерполяция от DARKER_BG к BLACK_BG
            t = y / 255.0
            r = DARKER_BG[0] * (1 - t) + BLACK_BG[0] * t
            g = DARKER_BG[1] * (1 - t) + BLACK_BG[1] * t
            b = DARKER_BG[2] * (1 - t) + BLACK_BG[2] * t

            img.setXel(0, y, r, g, b)
            img.setXel(1, y, r, g, b)

        tex = Texture()
        tex.load(img)
        self.gradient_card.setTexture(tex)
        self.gradient_card.setColor(1, 1, 1, 1)

    def create_grid_lines(self):
        """создаёт тонкие диагональные линии на фоне~~"""
        self.lines_root = self.root.attachNewNode("grid_lines")

        # создаём несколько диагональных линий
        for i in range(8):
            line = DirectFrame(
                frameColor=(0.2, 0.2, 0.2, 0.15),
                frameSize=(-0.002, 0.002, -3, 3),
                relief=DGG.FLAT,
                parent=self.lines_root
            )

            x_pos = -1.5 + i * 0.4
            line.setPos(x_pos, 0, 0)
            line.setR(25)  # наклон

            # добавляем лёгкую вариацию
            alpha = random.uniform(0.1, 0.2)
            line['frameColor'] = (0.2, 0.2, 0.2, alpha)

    def start_animation(self):
        """медленная пульсация градиента~~"""
        color1 = (0.95, 0.95, 0.95, 1.0)
        color2 = (1.05, 1.05, 1.05, 1.0)

        anim = Sequence(
            LerpColorInterval(self.gradient_card, 4.0, color2, color1, blendType='easeInOut'),
            LerpColorInterval(self.gradient_card, 4.0, color1, color2, blendType='easeInOut')
        )
        anim.loop()

    def show(self):
        """показать фон~~"""
        self.root.show()

    def hide(self):
        """скрыть фон~~"""
        self.root.hide()

    def cleanup(self):
        """очистка ресурсов~~"""
        if self.root:
            self.root.removeNode()
