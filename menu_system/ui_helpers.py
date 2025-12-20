"""
Вспомогательные функции для создания UI элементов
Упрощает создание повторяющихся элементов интерфейса
"""
from direct.gui.DirectGui import DirectLabel, DirectSlider, DirectCheckButton, DirectOptionMenu, DGG
from panda3d.core import TextNode

def create_label(text, pos, parent, scale=0.045, align=TextNode.ALeft):
    """Создает текстовую метку"""
    return DirectLabel(
        text=text,
        pos=pos,
        parent=parent,
        frameColor=(0, 0, 0, 0),
        text_fg=(0.9, 0.9, 0.9, 1),
        text_scale=scale,
        text_align=align
    )

def create_slider(range, value, pos, command, parent, scale=0.5):
    """Создает слайдер"""
    return DirectSlider(
        range=range,
        value=value,
        pageSize=1,
        pos=pos,
        parent=parent,
        command=command,
        frameColor=(0.18, 0.2, 0.25, 0.9),
        relief=DGG.FLAT,
        borderWidth=(0, 0),
        thumb_frameColor=(0.4, 0.6, 1, 1),
        thumb_relief=DGG.FLAT,
        thumb_frameSize=(-0.015, 0.015, -0.015, 0.015),
        scale=scale,
        text_fg=(0.9, 0.9, 0.9, 1)
    )

def create_checkbox(text, pos, command, parent, scale=0.05):
    """Создает чекбокс"""
    checkbox_style = {
        'frameColor': (0.18, 0.2, 0.25, 0.9),
        'relief': DGG.FLAT,
        'borderWidth': (0, 0),
        'text_fg': (0.9, 0.9, 0.9, 1),
        'boxPlacement': 'right',
        'boxRelief': DGG.FLAT,
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
    return checkbox

def create_option_menu(parent, items, initial_item, pos_x, pos_y, command):
    """Создает выпадающее меню с опциями"""
    menu = DirectOptionMenu(
        parent=parent,
        text="",
        items=items,
        initialitem=items.index(initial_item) if initial_item in items else 0,
        pos=(pos_x, 0, pos_y),
        scale=0.045,
        command=command,
        highlightColor=(0.5, 0.7, 1, 1),
        frameColor=(0.18, 0.2, 0.25, 0.9),
        popupMarker_frameColor=(0.4, 0.6, 1, 1),
        relief=DGG.FLAT,
        text_fg=(0.9, 0.9, 0.9, 1),
        item_relief=DGG.FLAT,
        item_frameColor=(0.18, 0.2, 0.25, 0.9),
        item_text_fg=(0.9, 0.9, 0.9, 1)
    )
    return menu
