try:
    from imgui_bundle import imgui
    from imgui_bundle import ImVec2
    HAS_IMGUI = True
except:
    imgui = None
    ImVec2 = None
    HAS_IMGUI = False

from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectSlider, DirectButton
from panda3d.core import WindowProperties

class ShaderDebugUI:
    def __init__(self, game):
        self.game = game
        self.shader_system = game.shader_system

        self.is_open = False
        self.imgui_backend = None
        self.using_imgui = False
        self.debug_panel = None
        self.debug_widgets = []

        self.ui_search = ""
        self.ui_preset_name = self.shader_system.current_preset_name
        self.ui_selected_preset = self.shader_system.current_preset_name
        self.ui_config = {
            "width_ratio": 0.46,
            "height_ratio": 0.52,
            "min_width": 420.0,
            "min_height": 280.0,
            "max_width": 700.0,
            "max_height": 520.0,
            "margin_x": 24.0,
            "margin_y": 56.0,
            "alpha": 0.94,
            "font_scale": 0.82,
            "lock_window_size": False,
            "show_style_editor": False,
            "show_imgui_demo": False,
        }

    def initialize_imgui(self):
        if not HAS_IMGUI:
            return False

        try:
            import p3dimgui
            self.imgui_backend = p3dimgui.ImGuiBackend(style="dark")
            self.imgui_backend.io.mouse_draw_cursor = True
            self.imgui_backend.hide()
            self.game.accept("imgui-new-frame", self.render_imgui)
            self.using_imgui = True
            print("[ShaderDebug] Using in-game Dear ImGui backend")
            return True
        except Exception as exc:
            self.imgui_backend = None
            self.using_imgui = False
            print(f"[ShaderDebug] ImGui backend unavailable, falling back to DirectGUI: {exc}")
            return False

    def render_imgui(self):
        if not self.is_open or not self.using_imgui or not self.imgui_backend:
            return

        snapshot = self.shader_system.get_ui_snapshot()
        preset_names = snapshot["preset_names"]
        if self.ui_selected_preset not in preset_names and preset_names:
            self.ui_selected_preset = preset_names[0]
        if not self.ui_preset_name:
            self.ui_preset_name = snapshot["current_preset"]

        io = imgui.get_io()
        style = imgui.get_style()
        style.alpha = float(self.ui_config.get("alpha", 1.0))
        shell_scale = self.game.get_imgui_shell_scale()
        display_width = float(io.display_size.x or 1024.0)
        display_height = float(io.display_size.y or 768.0)
        margin_x = float(self.ui_config.get("margin_x", 24.0))
        margin_y = float(self.ui_config.get("margin_y", 56.0))
        min_width = float(self.ui_config.get("min_width", 480.0)) * shell_scale
        min_height = float(self.ui_config.get("min_height", 320.0)) * shell_scale
        max_width = min(
            float(self.ui_config.get("max_width", 860.0)) * shell_scale,
            max(min_width, display_width - (margin_x * 2.0)),
        )
        max_height = min(
            float(self.ui_config.get("max_height", 620.0)) * shell_scale,
            max(min_height, display_height - (margin_y + 24.0)),
        )
        default_width = min(max_width, max(min_width, display_width * float(self.ui_config.get("width_ratio", 0.58)) * shell_scale))
        default_height = min(max_height, max(min_height, display_height * float(self.ui_config.get("height_ratio", 0.62)) * shell_scale))

        imgui.set_next_window_pos(ImVec2(margin_x, margin_y), imgui.Cond_.always)
        imgui.set_next_window_size_constraints(
            ImVec2(min_width, min_height),
            ImVec2(max_width, max_height),
        )
        imgui.set_next_window_size(ImVec2(default_width, default_height), imgui.Cond_.always)
        window_flags = (
            imgui.WindowFlags_.no_saved_settings.value
            | imgui.WindowFlags_.no_collapse.value
        )
        if self.ui_config.get("lock_window_size", False):
            window_flags |= imgui.WindowFlags_.no_resize.value

        imgui.begin("Shader Shell", flags=window_flags)
        if hasattr(imgui, "set_window_font_scale"):
            imgui.set_window_font_scale(max(0.55, float(self.ui_config.get("font_scale", 1.0)) * shell_scale))
        imgui.text("F7 / Esc close")
        imgui.same_line()
        self._render_status_badge(snapshot["compile_status"], "experimental")
        imgui.same_line()
        dirty_text = "Dirty" if snapshot["preset_dirty"] else "Saved"
        self._render_status_badge(dirty_text, "active" if not snapshot["preset_dirty"] else "experimental")
        imgui.separator()

        if imgui.begin_tab_bar("shader-shell-tabs"):
            for tab in snapshot["tabs"]:
                opened, _ = imgui.begin_tab_item(tab["label"])
                if opened:
                    imgui.begin_child(f"shader-shell-body::{tab['id']}", ImVec2(0, 0))
                    if tab["id"] == "home":
                        self._render_home_tab(snapshot)
                    elif tab["id"] == "techniques":
                        self._render_techniques_tab(snapshot)
                    elif tab["id"] == "targets":
                        self._render_panel_tab("targets", snapshot)
                    elif tab["id"] == "weapon":
                        self._render_panel_tab("weapon", snapshot)
                    elif tab["id"] == "post":
                        self._render_panel_tab("post", snapshot)
                    elif tab["id"] == "volumes":
                        self._render_panel_tab("volumes", snapshot)
                    elif tab["id"] == "stats":
                        self._render_stats_tab(snapshot)
                    imgui.end_child()
                    imgui.end_tab_item()
            opened, _ = imgui.begin_tab_item("ImGui")
            if opened:
                imgui.begin_child("shader-shell-body::imgui", ImVec2(0, 0))
                self._render_imgui_settings_tab(display_width, display_height)
                imgui.end_child()
                imgui.end_tab_item()
            imgui.end_tab_bar()

        if self.ui_config.get("show_imgui_demo", False) and hasattr(imgui, "show_demo_window"):
            visible = True
            imgui.show_demo_window(visible)

        imgui.end()

    def _status_color(self, status: str):
        palette = {
            "active": imgui.ImVec4(0.33, 0.82, 0.48, 1.0),
            "planned": imgui.ImVec4(0.45, 0.67, 0.95, 1.0),
            "experimental": imgui.ImVec4(0.97, 0.72, 0.25, 1.0),
            "broken": imgui.ImVec4(0.93, 0.33, 0.33, 1.0),
        }
        return palette.get(status, imgui.ImVec4(0.8, 0.8, 0.8, 1.0))

    def _render_status_badge(self, text: str, status: str):
        imgui.text_colored(self._status_color(status), text)

    def _render_global_toggles(self):
        for label, key in [
            ("Master", "master_enabled"),
            ("Targets", "target_enabled"),
            ("Weapon", "weapon_enabled"),
            ("Post", "post_enabled"),
            ("Volumes", "volumes_enabled"),
            ("Debug Views", "debug_views_enabled"),
        ]:
            changed, value = imgui.checkbox(label, bool(self.shader_system.state.get(key, False)))
            if changed:
                self.update_bool(key, value)
            imgui.same_line()
        imgui.new_line()

    def _render_home_tab(self, snapshot: dict):
        self._render_global_toggles()
        imgui.separator_text("Presets")

        changed, self.ui_preset_name = imgui.input_text("Preset Name", self.ui_preset_name)
        if changed:
            self.ui_preset_name = self.ui_preset_name.strip()

        if imgui.button("Save"):
            if self.shader_system.save_preset(self.ui_preset_name or "default"):
                self.ui_selected_preset = self.shader_system.current_preset_name
                self.ui_preset_name = self.shader_system.current_preset_name
        imgui.same_line()
        if imgui.button("Load"):
            if self.shader_system.load_preset(self.ui_selected_preset):
                self.ui_preset_name = self.shader_system.current_preset_name
        imgui.same_line()
        if imgui.button("Delete"):
            if self.shader_system.delete_preset(self.ui_selected_preset):
                self.ui_selected_preset = self.shader_system.current_preset_name
                self.ui_preset_name = self.shader_system.current_preset_name
        imgui.same_line()
        if imgui.button("Reload Shaders"):
            self.shader_system.reload_shaders()
        imgui.same_line()
        if imgui.button("Reset All"):
            self.reset_values()
            self.ui_preset_name = self.shader_system.current_preset_name

        if imgui.begin_list_box("Available Presets", ImVec2(-1, 72)):
            for preset_name in snapshot["preset_names"]:
                selected = preset_name == self.ui_selected_preset
                clicked, selected = imgui.selectable(preset_name, selected)
                if clicked:
                    self.ui_selected_preset = preset_name
            imgui.end_list_box()

        imgui.separator_text("Overview")
        imgui.bullet_text(f"Preset: {snapshot['current_preset']}")
        imgui.bullet_text(f"Enabled techniques: {snapshot['active_count']} / {snapshot['technique_count']}")
        imgui.bullet_text(f"Render: {snapshot['render_size'][0]} x {snapshot['render_size'][1]}")
        imgui.bullet_text(f"Framebuffer: {snapshot['framebuffer_size'][0]} x {snapshot['framebuffer_size'][1]}")
        if snapshot["buffer_size"]:
            imgui.bullet_text(f"Scene Buffer: {snapshot['buffer_size'][0]} x {snapshot['buffer_size'][1]}")
        imgui.bullet_text(f"Post Stage Applied: {snapshot['post_stage_applied']}")

        imgui.separator_text("Pipeline Order")
        for idx, stage_name in enumerate(snapshot["pipeline_order"], 1):
            imgui.bullet_text(f"{idx}. {stage_name}")

        imgui.separator_text("Roadmap")
        for roadmap_item in [
            "Color grading / tonemap / LUT pack",
            "Bloom / lens dirt / glare shell",
            "Reactive overlays for damage, kill and ADS states",
            "Target outline / respawn materialize pack",
            "Local fog, heat haze and impact dust placeholders",
        ]:
            imgui.bullet_text(roadmap_item)

    def _render_techniques_tab(self, snapshot: dict):
        changed, self.ui_search = imgui.input_text("Search", self.ui_search)
        if changed:
            self.ui_search = self.ui_search.strip()
        imgui.separator()
        self._render_grouped_cards(snapshot["registry"], self.ui_search)

    def _render_panel_tab(self, panel_id: str, snapshot: dict):
        panel_registry = snapshot["panels"].get(panel_id, [])
        self._render_grouped_cards(panel_registry, "")

    def _render_grouped_cards(self, techniques: list, search_query: str):
        grouped = {}
        lowered_search = search_query.lower().strip()
        for technique in techniques:
            haystack = " ".join(
                [
                    technique.get("display_name", ""),
                    technique.get("description", ""),
                    technique.get("group", ""),
                    technique.get("status", ""),
                ]
            ).lower()
            if lowered_search and lowered_search not in haystack:
                continue
            grouped.setdefault(technique.get("group", "Misc"), []).append(technique)

        if not grouped:
            imgui.text_colored(self._status_color("planned"), "No techniques match the current filter.")
            return

        for group_name, items in grouped.items():
            imgui.separator_text(group_name)
            for technique in sorted(items, key=lambda item: item.get("order", 0)):
                self._render_technique_card(technique)

    def _render_technique_card(self, technique: dict):
        status = technique.get("status", "planned")
        header_open = imgui.collapsing_header(
            f"{technique['display_name']}##{technique['technique_id']}",
            imgui.TreeNodeFlags_.default_open.value if status in ("active", "experimental") else 0,
        )
        if not header_open:
            return

        self._render_status_badge(status.upper(), status)
        imgui.same_line()
        imgui.text(f"Stage: {technique.get('stage', 'n/a')} | Cost: {technique.get('cost', 'n/a')}")
        imgui.text_wrapped(technique.get("description", ""))
        if technique.get("debug_notes"):
            imgui.text_colored(imgui.ImVec4(0.62, 0.70, 0.82, 1.0), technique["debug_notes"])

        enabled_key = technique.get("enabled_key")
        if enabled_key:
            changed, enabled = imgui.checkbox(
                f"Enabled##{technique['technique_id']}",
                bool(self.shader_system.state.get(enabled_key, False)),
            )
            if changed:
                self.update_bool(enabled_key, enabled)
        else:
            imgui.begin_disabled()
            imgui.checkbox(f"Enabled##{technique['technique_id']}", False)
            imgui.end_disabled()

        if technique["params"]:
            for param in technique["params"]:
                slider_width = max(240.0, imgui.get_content_region_avail().x - 8.0)
                imgui.set_next_item_width(slider_width)
                changed, value = imgui.slider_float(
                    f"{param['label']}##{technique['technique_id']}::{param['key']}",
                    float(param["value"]),
                    param["min"],
                    param["max"],
                    param.get("format", "%.2f"),
                )
                if changed:
                    self.update_value(param["key"], value)
        else:
            message = "Runtime-integrated effect. No direct per-technique controls yet."
            message_status = status if status in ("active", "experimental", "broken") else "planned"
            if message_status == "planned":
                message = "Planned placeholder. GLSL implementation will be attached later."
            imgui.text_colored(self._status_color(message_status), message)
        imgui.spacing()

    def _render_stats_tab(self, snapshot: dict):
        imgui.separator_text("Runtime")
        imgui.bullet_text(f"Compile Status: {snapshot['compile_status']}")
        imgui.bullet_text(f"Current Preset: {snapshot['current_preset']}")
        imgui.bullet_text(f"Preset Dirty: {'Yes' if snapshot['preset_dirty'] else 'No'}")
        imgui.bullet_text(f"Active Techniques: {snapshot['active_count']}")
        imgui.bullet_text(f"Fullscreen Stage Applied: {snapshot['post_stage_applied']}")
        imgui.bullet_text(f"Post Supported: {'Yes' if snapshot['post_supported'] else 'No'}")
        imgui.separator_text("Buffers")
        imgui.bullet_text(f"Render Size: {snapshot['render_size'][0]} x {snapshot['render_size'][1]}")
        imgui.bullet_text(f"Framebuffer Size: {snapshot['framebuffer_size'][0]} x {snapshot['framebuffer_size'][1]}")
        if snapshot["buffer_size"]:
            imgui.bullet_text(f"Scene Buffer Size: {snapshot['buffer_size'][0]} x {snapshot['buffer_size'][1]}")
        else:
            imgui.bullet_text("Scene Buffer Size: inactive")
        imgui.separator_text("Debug")
        imgui.text_wrapped(
            "This shell is the future ReShade-Lite host for custom GLSL passes, object shaders and local volumetric placeholders."
        )

    def _render_imgui_settings_tab(self, display_width: float, display_height: float):
        cfg = self.ui_config

        imgui.separator_text("Shell Window")
        changed, value = imgui.slider_float("Width Ratio", float(cfg["width_ratio"]), 0.35, 0.90, "%.2f")
        if changed:
            cfg["width_ratio"] = value
        changed, value = imgui.slider_float("Height Ratio", float(cfg["height_ratio"]), 0.35, 0.90, "%.2f")
        if changed:
            cfg["height_ratio"] = value
        changed, value = imgui.slider_float("Margin X", float(cfg["margin_x"]), 8.0, 96.0, "%.0f")
        if changed:
            cfg["margin_x"] = value
        changed, value = imgui.slider_float("Margin Y", float(cfg["margin_y"]), 8.0, 128.0, "%.0f")
        if changed:
            cfg["margin_y"] = value
        changed, value = imgui.slider_float("Min Width", float(cfg["min_width"]), 360.0, 760.0, "%.0f")
        if changed:
            cfg["min_width"] = value
        changed, value = imgui.slider_float("Min Height", float(cfg["min_height"]), 260.0, 640.0, "%.0f")
        if changed:
            cfg["min_height"] = value
        changed, value = imgui.slider_float("Max Width", float(cfg["max_width"]), 520.0, min(display_width, 1400.0), "%.0f")
        if changed:
            cfg["max_width"] = value
        changed, value = imgui.slider_float("Max Height", float(cfg["max_height"]), 360.0, min(display_height, 1200.0), "%.0f")
        if changed:
            cfg["max_height"] = value
        changed, value = imgui.checkbox("Lock Window Resize", bool(cfg["lock_window_size"]))
        if changed:
            cfg["lock_window_size"] = value

        imgui.separator_text("Visual")
        changed, value = imgui.slider_float("Font Scale", float(cfg["font_scale"]), 0.70, 1.35, "%.2f")
        if changed:
            cfg["font_scale"] = value
        changed, value = imgui.slider_float("Alpha", float(cfg["alpha"]), 0.65, 1.00, "%.2f")
        if changed:
            cfg["alpha"] = value

        imgui.separator_text("Tools")
        changed, value = imgui.checkbox("Show Style Editor", bool(cfg["show_style_editor"]))
        if changed:
            cfg["show_style_editor"] = value
        changed, value = imgui.checkbox("Show ImGui Demo", bool(cfg["show_imgui_demo"]))
        if changed:
            cfg["show_imgui_demo"] = value
        if imgui.button("Reset ImGui Shell"):
            self.ui_config.update(
                {
                    "width_ratio": 0.46,
                    "height_ratio": 0.52,
                    "min_width": 420.0,
                    "min_height": 280.0,
                    "max_width": 700.0,
                    "max_height": 520.0,
                    "margin_x": 24.0,
                    "margin_y": 56.0,
                    "alpha": 0.94,
                    "font_scale": 0.82,
                    "lock_window_size": False,
                    "show_style_editor": False,
                    "show_imgui_demo": False,
                }
            )

        imgui.separator_text("Display")
        imgui.bullet_text(f"Display Size: {int(display_width)} x {int(display_height)}")
        imgui.bullet_text(f"Current Width Ratio: {cfg['width_ratio']:.2f}")
        imgui.bullet_text(f"Current Height Ratio: {cfg['height_ratio']:.2f}")

        if cfg.get("show_style_editor", False) and hasattr(imgui, "show_style_editor"):
            imgui.separator_text("Style Editor")
            imgui.show_style_editor()

    def create_directgui_panel(self):
        panel = DirectFrame(
            frameColor=(0.06, 0.06, 0.08, 0.92),
            frameSize=(-0.62, 0.62, -0.82, 0.82),
            pos=(0.0, 0, 0.0),
        )
        panel.hide()
        self.debug_panel = panel

        title = DirectLabel(
            text="Shader Debug",
            scale=0.07,
            pos=(0, 0, 0.74),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            parent=panel,
        )
        self.debug_widgets.append(title)

        subtitle = DirectLabel(
            text="F7 close | post stages: 0 off, 1 filter, 2 glsl copy, 3 fx",
            scale=0.04,
            pos=(0, 0, 0.66),
            text_fg=(0.75, 0.8, 0.9, 1),
            frameColor=(0, 0, 0, 0),
            parent=panel,
        )
        self.debug_widgets.append(subtitle)

    def _set_overlay_mouse_mode(self, enabled: bool):
        props = WindowProperties()
        props.setCursorHidden(not enabled)
        props.setMouseMode(WindowProperties.M_absolute if enabled else WindowProperties.M_relative)
        self.game.win.requestProperties(props)

    def toggle(self):
        if self.game.is_splash_screen_active:
            return
        if self.is_open:
            self.is_open = False
            if self.using_imgui and self.imgui_backend:
                self.imgui_backend.hide()
            if self.debug_panel:
                self.debug_panel.hide()
            self._set_overlay_mouse_mode(False)
            return

        if self.game.chat_manager.is_chat_active:
            self.game.chat_manager.close_chat_input()
        if self.is_open:
            self.toggle()

        self.is_open = True
        if self.using_imgui and self.imgui_backend:
            self.imgui_backend.show()
            props = WindowProperties()
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_absolute)
            self.game.win.requestProperties(props)
        elif self.debug_panel:
            self.debug_panel.show()
            self._set_overlay_mouse_mode(True)
        self.game.mouse_pressed = False
        for key in self.game.keyMap:
            self.game.keyMap[key] = False

    def update_bool(self, key: str, value):
        self.shader_system.set_state_bool(key, value)

    def update_value(self, key: str, value):
        self.shader_system.set_state_value(key, value)

    def reset_values(self):
        self.shader_system.reset_state()
        if self.using_imgui:
            return
        if not self.debug_panel:
            return
        self.debug_panel.destroy()
        self.debug_widgets = []
        self.create_directgui_panel()
        if self.is_open and self.debug_panel:
            self.debug_panel.show()
