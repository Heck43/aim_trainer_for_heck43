"""
Вспомогательные функции для создания UI элементов
Упрощает создание повторяющихся элементов интерфейса
"""
from direct.gui.DirectGui import DirectLabel, DirectSlider, DirectCheckButton, DirectOptionMenu, DGG
from panda3d.core import TextNode

def get_resolution_ui_scale(game, base_width=1280, base_height=720, min_scale=0.55, max_scale=1.0):
    """Returns a resolution-aware scale so UI shrinks on larger displays."""
    width = 0
    height = 0

    win = getattr(game, "win", None)
    if win:
        try:
            props = win.getProperties()
            width = int(props.getXSize() or win.getXSize())
            height = int(props.getYSize() or win.getYSize())
        except Exception:
            width = 0
            height = 0

    if width <= 0 or height <= 0:
        resolution = str(getattr(game, "settings", {}).get("resolution", f"{base_width}x{base_height}"))
        try:
            width, height = map(int, resolution.lower().split("x"))
        except Exception:
            width, height = base_width, base_height

    scale = min(base_width / float(max(width, 1)), base_height / float(max(height, 1)))
    return max(min_scale, min(max_scale, scale))

def create_label(text, pos, parent, scale=0.045, align=TextNode.ALeft):
    """создаёт текстовую метку~~"""
    return DirectLabel(
        text=text,
        pos=pos,
        parent=parent,
        frameColor=(0, 0, 0, 0),
        text_fg=(0.9, 0.9, 0.91, 1),
        text_scale=scale,
        text_align=align
    )

def create_slider(range, value, pos, command, parent, scale=0.5):
    """создаёт слайдер в минималистичном стиле~~"""
    return DirectSlider(
        range=range,
        value=value,
        pageSize=1,
        pos=pos,
        parent=parent,
        command=command,
        frameColor=(0.2, 0.2, 0.21, 0.9),  # серый фон
        relief=DGG.FLAT,
        borderWidth=(0, 0),
        thumb_frameColor=(1.0, 0.58, 0.0, 1),  # оранжевый ползунок
        thumb_relief=DGG.FLAT,
        thumb_frameSize=(-0.025, 0.025, -0.025, 0.025),  # больше ползунок
        scale=scale,
        text_fg=(0.9, 0.9, 0.91, 1)
    )

def create_checkbox(text, pos, command, parent, scale=0.05):
    """создаёт чекбокс~~"""
    checkbox_style = {
        'frameColor': (0, 0, 0, 0),  # прозрачный фон
        'relief': DGG.FLAT,
        'borderWidth': (0, 0),
        'text_fg': (0.9, 0.9, 0.91, 1),
        'boxPlacement': 'right',
        'boxRelief': DGG.FLAT,
        'boxImage': None,
        'boxImageColor': (1.0, 0.58, 0.0, 1),  # оранжевая галочка
        'indicatorValue': 0,
        'scale': scale,
        'frameSize': (-1.5, 3.0, -0.4, 0.6),
        'text_scale': 0.8
    }

    checkbox = DirectCheckButton(
        text=text,
        pos=pos,
        command=command,
        parent=parent,
        **checkbox_style
    )
    checkbox['indicatorValue'] = 0
    checkbox['text_pos'] = (0.2, 0)

    # устанавливаем цвета для бокса
    checkbox['frameColor'] = (0, 0, 0, 0)
    checkbox.indicator['frameColor'] = (0.2, 0.2, 0.21, 0.9)  # серый бокс
    checkbox.indicator['relief'] = DGG.FLAT

    return checkbox

def create_option_menu(parent, items, initial_item, pos_x, pos_y, command):
    """создаёт выпадающее меню с опциями~~"""
    menu = DirectOptionMenu(
        parent=parent,
        text="",
        items=items,
        initialitem=items.index(initial_item) if initial_item in items else 0,
        pos=(pos_x, 0, pos_y),
        scale=0.045,
        command=command,
        highlightColor=(1.0, 0.65, 0.1, 1),  # оранжевый highlight
        frameColor=(0.2, 0.2, 0.21, 0.9),
        popupMarker_frameColor=(1.0, 0.58, 0.0, 1),  # оранжевая стрелка
        relief=DGG.FLAT,
        text_fg=(0.9, 0.9, 0.91, 1),
        item_relief=DGG.FLAT,
        item_frameColor=(0.2, 0.2, 0.21, 0.9),
        item_text_fg=(0.9, 0.9, 0.91, 1)
    )
    return menu
