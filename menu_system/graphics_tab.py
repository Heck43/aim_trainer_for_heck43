"""
Вкладка графических настроек
"""
from direct.gui.DirectGui import DirectLabel, DirectSlider, DirectCheckButton, DirectOptionMenu, DGG
from panda3d.core import TextNode
from .base_tab import BaseTab
from .ui_helpers import create_checkbox, create_label, create_slider

class GraphicsTab(BaseTab):
    """Вкладка с настройками графики"""
    
    def __init__(self, game, parent, resolutions):
        super().__init__(game, parent)
        self.resolutions = resolutions
        self.current_resolution = game.settings.get('resolution', '1280x720')
        self.create_ui()
    
    def create_ui(self):
        """Создает UI элементы вкладки"""
        # Resolution
        resolution_label = create_label(
            "Resolution",
            pos=(-0.6, 0, 0.3),
            parent=self.frame
        )
        self.elements.append(resolution_label)
        
        self.resolution_menu = DirectOptionMenu(
            text="Resolution",
            scale=0.05,
            pos=(0.0, 0, 0.3),
            items=self.resolutions,
            initialitem=self.resolutions.index(self.current_resolution) if self.current_resolution in self.resolutions else 3,
            parent=self.frame,
            frameColor=(0.18, 0.2, 0.25, 0.9),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            text_fg=(0.9, 0.9, 0.9, 1),
            highlightColor=(0.4, 0.6, 1, 0.8),
            item_frameColor=(0.16, 0.18, 0.21, 0.95),
            popupMenu_frameColor=(0.16, 0.18, 0.21, 0.95),
            command=self.update_resolution,
            item_relief=DGG.FLAT,
            popupMenu_relief=DGG.FLAT
        )
        self.elements.append(self.resolution_menu)
        
        # FOV
        fov_label = create_label("FOV", pos=(-0.6, 0, 0.15), parent=self.frame)
        self.elements.append(fov_label)
        
        self.fov_slider = create_slider(
            range=(60, 120),
            value=self.game.settings.get('fov', 90),
            pos=(0.1, 0, 0.15),
            command=self.update_fov,
            parent=self.frame
        )
        self.elements.append(self.fov_slider)
        
        # Fullscreen
        fullscreen_label = create_label("Fullscreen", pos=(-0.6, 0, -0.15), parent=self.frame)
        self.elements.append(fullscreen_label)
        
        self.fullscreen_checkbox = create_checkbox(
            "Enable",
            pos=(-0.1, 0, -0.15),
            command=self.toggle_fullscreen,
            parent=self.frame
        )
        self.fullscreen_checkbox['indicatorValue'] = self.game.settings.get('fullscreen', False)
        self.elements.append(self.fullscreen_checkbox)
        
        # NSFW Mode
        nsfw_label = create_label("NSFW mode", pos=(-0.6, 0, 0), parent=self.frame)
        self.elements.append(nsfw_label)
        
        self.show_images_checkbox = create_checkbox(
            "Enable",
            pos=(-0.1, 0, 0),
            command=self.toggle_show_images,
            parent=self.frame
        )
        self.show_images_checkbox['indicatorValue'] = self.game.settings.get('show_target_images', True)
        self.elements.append(self.show_images_checkbox)
        
        # NSFW Category
        self.nsfw_categories = ["furry", "anime", "futa", "femboy", "hentai", "fnia", "furry_2", "furry_3"]
        
        self.nsfw_category_label = create_label("NSFW Category", pos=(-0.6, 0, -0.3), parent=self.frame)
        self.elements.append(self.nsfw_category_label)
        
        self.nsfw_category_menu = DirectOptionMenu(
            text="Category",
            scale=0.05,
            pos=(0.1, 0, -0.3),
            items=self.nsfw_categories,
            initialitem=self.nsfw_categories.index(self.game.settings.get('nsfw_category', 'furry')) if self.game.settings.get('nsfw_category', 'furry') in self.nsfw_categories else 0,
            parent=self.frame,
            frameColor=(0.18, 0.2, 0.25, 0.9),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            text_fg=(0.9, 0.9, 0.9, 1),
            highlightColor=(0.4, 0.6, 1, 0.8),
            item_frameColor=(0.16, 0.18, 0.21, 0.95),
            popupMenu_frameColor=(0.16, 0.18, 0.21, 0.95),
            command=self.update_nsfw_category,
            item_relief=DGG.FLAT,
            popupMenu_relief=DGG.FLAT
        )
        self.elements.append(self.nsfw_category_menu)
        
        # Hide category menu if NSFW mode is disabled
        if not self.game.settings.get('show_target_images', True):
            self.nsfw_category_menu.hide()
            self.nsfw_category_label.hide()
    
    def update_resolution(self, resolution):
        """Обновляет разрешение экрана"""
        from panda3d.core import WindowProperties
        
        was_fullscreen = self.game.settings.get('fullscreen', False)
        
        if was_fullscreen:
            props = WindowProperties()
            props.setFullscreen(False)
            self.game.win.requestProperties(props)
        
        self.game.settings['resolution'] = resolution
        self.game.settings['windowed_resolution'] = resolution
        width, height = map(int, resolution.split('x'))
        
        props = WindowProperties()
        props.setSize(width, height)
        self.game.win.requestProperties(props)
        
        if was_fullscreen:
            props = WindowProperties()
            props.setFullscreen(True)
            self.game.win.requestProperties(props)
        
        self.game.save_settings()
    
    def update_fov(self):
        """Обновляет FOV"""
        new_fov = int(self.fov_slider['value'])
        self.game.settings['fov'] = new_fov
        self.game.save_settings()
        base.camLens.setFov(new_fov)
    
    def toggle_fullscreen(self, status):
        """Переключает полноэкранный режим"""
        from panda3d.core import WindowProperties
        
        self.game.settings['fullscreen'] = status
        props = WindowProperties()
        
        if status:
            self.game.settings['windowed_resolution'] = self.game.settings['resolution']
            props.setFullscreen(True)
        else:
            props.setFullscreen(False)
            width, height = map(int, self.game.settings.get('windowed_resolution', '1280x720').split('x'))
            props.setSize(width, height)
        
        self.game.win.requestProperties(props)
        self.game.save_settings()
    
    def toggle_show_images(self, status):
        """Переключает NSFW режим"""
        self.game.settings['show_target_images'] = status
        self.game.save_settings()
        
        if status:
            self.nsfw_category_menu.show()
            self.nsfw_category_label.show()
        else:
            self.nsfw_category_menu.hide()
            self.nsfw_category_label.hide()
        
        # Обновляем все активные цели если пул существует
        if hasattr(self.game, 'target_pool') and self.game.target_pool:
            self.game.target_pool.refresh_all_active()
    
    def update_nsfw_category(self, category):
        """Обновляет NSFW категорию"""
        self.game.settings['nsfw_category'] = category
        self.game.save_settings()
        
        # Обновляем все активные цели если пул существует
        if hasattr(self.game, 'target_pool') and self.game.target_pool:
            self.game.target_pool.refresh_all_active()

