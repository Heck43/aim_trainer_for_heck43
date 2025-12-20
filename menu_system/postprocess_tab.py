"""
Вкладка настроек пост-обработки
"""
from .base_tab import BaseTab
from .ui_helpers import create_label, create_checkbox, create_slider

class PostProcessTab(BaseTab):
    """Вкладка с настройками пост-обработки"""
    
    def __init__(self, game, parent, bg_filters=None):
        super().__init__(game, parent)
        self.bg_filters = bg_filters
        self.create_ui()
    
    def create_ui(self):
        """Создает UI элементы вкладки"""
        # Bloom Effect
        bloom_enabled_label = create_label("Bloom Effect", pos=(-0.3, 0, 0.40), parent=self.frame)
        self.elements.append(bloom_enabled_label)
        
        self.bloom_checkbox = create_checkbox(
            "Enable",
            pos=(0.2, 0, 0.40),
            command=self.toggle_bloom,
            parent=self.frame
        )
        self.bloom_checkbox['indicatorValue'] = self.game.settings.get('bloom_enabled', False)
        self.elements.append(self.bloom_checkbox)
        
        # Bloom Intensity
        bloom_intensity_label = create_label("Bloom Intensity", pos=(-0.3, 0, 0.28), parent=self.frame)
        self.elements.append(bloom_intensity_label)
        
        self.bloom_intensity_slider = create_slider(
            range=(0.1, 2.0),
            value=self.game.settings.get('bloom_intensity', 1.0),
            pos=(0.2, 0, 0.28),
            command=self.update_bloom_intensity,
            parent=self.frame
        )
        self.elements.append(self.bloom_intensity_slider)
        
        # Blur Effect
        blur_enabled_label = create_label("Blur Effect", pos=(-0.3, 0, 0.14), parent=self.frame)
        self.elements.append(blur_enabled_label)
        
        self.blur_checkbox = create_checkbox(
            "Enable",
            pos=(0.2, 0, 0.14),
            command=self.toggle_blur,
            parent=self.frame
        )
        self.blur_checkbox['indicatorValue'] = self.game.settings.get('blur_enabled', False)
        self.elements.append(self.blur_checkbox)
        
        # Blur Amount
        blur_amount_label = create_label("Blur Amount", pos=(-0.3, 0, 0.02), parent=self.frame)
        self.elements.append(blur_amount_label)
        
        self.blur_amount_slider = create_slider(
            range=(0.0, 2.0),
            value=self.game.settings.get('blur_amount', 0.5),
            pos=(0.2, 0, 0.02),
            command=self.update_blur_amount,
            parent=self.frame
        )
        self.elements.append(self.blur_amount_slider)
        
        # Cartoon Shading
        cartoon_enabled_label = create_label("Cartoon Shading", pos=(-0.3, 0, -0.12), parent=self.frame)
        self.elements.append(cartoon_enabled_label)
        
        self.cartoon_checkbox = create_checkbox(
            "Enable",
            pos=(0.2, 0, -0.12),
            command=self.toggle_cartoon,
            parent=self.frame
        )
        self.cartoon_checkbox['indicatorValue'] = self.game.settings.get('cartoon_enabled', False)
        self.elements.append(self.cartoon_checkbox)
        
        # Inverted Colors
        inverted_enabled_label = create_label("Inverted Colors", pos=(-0.3, 0, -0.22), parent=self.frame)
        self.elements.append(inverted_enabled_label)
        
        self.inverted_checkbox = create_checkbox(
            "Enable",
            pos=(0.2, 0, -0.22),
            command=self.toggle_inverted,
            parent=self.frame
        )
        self.inverted_checkbox['indicatorValue'] = self.game.settings.get('inverted_enabled', False)
        self.elements.append(self.inverted_checkbox)
        
        # Ambient Occlusion
        ao_enabled_label = create_label("Ambient Occlusion", pos=(-0.3, 0, -0.32), parent=self.frame)
        self.elements.append(ao_enabled_label)
        
        self.ao_checkbox = create_checkbox(
            "Enable",
            pos=(0.2, 0, -0.32),
            command=self.toggle_ao,
            parent=self.frame
        )
        self.ao_checkbox['indicatorValue'] = self.game.settings.get('ao_enabled', False)
        self.elements.append(self.ao_checkbox)
        
        # Motion Blur
        motion_blur_enabled_label = create_label("Motion Blur", pos=(-0.3, 0, -0.42), parent=self.frame)
        self.elements.append(motion_blur_enabled_label)
        
        self.motion_blur_checkbox = create_checkbox(
            "Enable",
            pos=(0.2, 0, -0.42),
            command=self.toggle_motion_blur,
            parent=self.frame
        )
        self.motion_blur_checkbox['indicatorValue'] = self.game.settings.get('motion_blur_enabled', False)
        self.elements.append(self.motion_blur_checkbox)
        
        # Motion Blur Amount
        motion_blur_amount_label = create_label("Motion Blur Amount", pos=(-0.3, 0, -0.54), parent=self.frame)
        self.elements.append(motion_blur_amount_label)
        
        self.motion_blur_amount_slider = create_slider(
            range=(0.1, 1.0),
            value=self.game.settings.get('motion_blur_amount', 0.5),
            pos=(0.2, 0, -0.54),
            command=self.update_motion_blur_amount,
            parent=self.frame
        )
        self.elements.append(self.motion_blur_amount_slider)
    
    def toggle_bloom(self, enabled):
        """Переключает bloom эффект"""
        self.game.settings['bloom_enabled'] = bool(enabled)
        self.game.save_settings()
        
        if self.bg_filters:
            try:
                if enabled:
                    intensity = self.game.settings.get('bloom_intensity', 1.0)
                    self.bg_filters.setBloom(blend=(0.3, 0.4, 0.5, 0.0), desat=-0.5, intensity=intensity, size="small")
                else:
                    self.bg_filters.delBloom()
            except Exception as e:
                print(f"Error toggling bloom: {e}")
    
    def update_bloom_intensity(self):
        """Обновляет интенсивность bloom"""
        intensity = self.bloom_intensity_slider['value']
        self.game.settings['bloom_intensity'] = intensity
        self.game.save_settings()
        
        if self.game.settings.get('bloom_enabled', False) and self.bg_filters:
            try:
                self.bg_filters.delBloom()
                self.bg_filters.setBloom(blend=(0.3, 0.4, 0.5, 0.0), desat=-0.5, intensity=intensity, size="small")
            except Exception as e:
                print(f"Error updating bloom intensity: {e}")
    
    def toggle_blur(self, enabled):
        """Переключает blur эффект"""
        self.game.settings['blur_enabled'] = bool(enabled)
        self.game.save_settings()
        
        if self.bg_filters:
            try:
                if enabled:
                    amount = self.game.settings.get('blur_amount', 0.5)
                    self.bg_filters.setBlurSharpen(amount=amount)
                else:
                    self.bg_filters.delBlurSharpen()
            except Exception as e:
                print(f"Error toggling blur: {e}")
    
    def update_blur_amount(self):
        """Обновляет количество blur"""
        amount = self.blur_amount_slider['value']
        self.game.settings['blur_amount'] = amount
        self.game.save_settings()
        
        if self.game.settings.get('blur_enabled', False) and self.bg_filters:
            try:
                self.bg_filters.delBlurSharpen()
                self.bg_filters.setBlurSharpen(amount=amount)
            except Exception as e:
                print(f"Error updating blur amount: {e}")
    
    def toggle_cartoon(self, enabled):
        """Переключает cartoon shading"""
        self.game.settings['cartoon_enabled'] = bool(enabled)
        self.game.save_settings()
        
        if self.bg_filters:
            try:
                if enabled:
                    self.bg_filters.setCartoonInk(separation=1.0)
                else:
                    self.bg_filters.delCartoonInk()
            except Exception as e:
                print(f"Error toggling cartoon: {e}")
    
    def toggle_inverted(self, enabled):
        """Переключает inverted colors"""
        self.game.settings['inverted_enabled'] = bool(enabled)
        self.game.save_settings()
        
        if self.bg_filters:
            try:
                if enabled:
                    self.bg_filters.setInverted()
                else:
                    self.bg_filters.delInverted()
            except Exception as e:
                print(f"Error toggling inverted: {e}")
    
    def toggle_ao(self, enabled):
        """Переключает ambient occlusion"""
        self.game.settings['ao_enabled'] = bool(enabled)
        self.game.save_settings()
        
        if self.bg_filters:
            try:
                if enabled:
                    self.bg_filters.setAmbientOcclusion()
                else:
                    self.bg_filters.delAmbientOcclusion()
            except Exception as e:
                print(f"Error toggling AO: {e}")
    
    def toggle_motion_blur(self, enabled):
        """Переключает motion blur"""
        self.game.settings['motion_blur_enabled'] = bool(enabled)
        self.game.save_settings()
    
    def update_motion_blur_amount(self):
        """Обновляет количество motion blur"""
        amount = self.motion_blur_amount_slider['value']
        self.game.settings['motion_blur_amount'] = amount
        self.game.save_settings()

