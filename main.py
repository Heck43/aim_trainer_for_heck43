#!/usr/bin/env python3
"""
Aim Trainer - точка входа приложения
Запускает игру из модуля managers.game
"""

from managers.game import Game


if __name__ == "__main__":
    game = Game()
    game.run()
