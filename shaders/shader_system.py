"""Runtime GLSL shader system controlled by an external ImGui panel."""
from __future__ import annotations

import atexit
import json
import os
import socket
import subprocess
import sys
import threading
import time

from panda3d.core import Camera, CardMaker, Filename, FrameBufferProperties, GraphicsOutput, GraphicsPipe, NodePath, Shader, Texture, Vec2, Vec4, WindowProperties

from shaders.shader_shared import (
    SHADER_CONTROL_PORT,
    TAB_LAYOUT,
    build_panel_registry,
    build_technique_registry,
    count_enabled_techniques,
    make_default_shader_state,
    make_preset_payload,
    sanitize_preset_payload,
    sanitize_shader_state,
)


class ShaderSystem:
    """Centralized shader management for targets, weapon and fullscreen pass."""

    def __init__(self, game):
        self.game = game
        self.enabled = True
        self.state = make_default_shader_state()
        self.state_lock = threading.Lock()
        self.pending_state = None

        self.target_shader = None
        self.weapon_shader = None
        self.post_shader = None
        self.postprocess_supported = False
        self.post_quad = None
        self.scene_tex = None
        self.scene_buffer = None
        self.scene_region = None
        self.post_camera_np = None
        self.main_region = None
        self.main_region_original_camera = None
        self.post_stage_applied = 0
        self.postprocess_failed_stage = None

        self.target_states = {}
        self.target_visibility = {}
        self.target_materialize_started = {}
        self.weapon_flash_until = 0.0
        self.hit_tint_until = 0.0
        self.current_weapon_np = None

        self.listener_socket = None
        self.listener_thread = None
        self.listener_running = False

        self.debug_panel_process = None
        self.current_preset_name = "default"
        self.loaded_preset_state = sanitize_shader_state({}, None)
        self.last_reload_status = "Ready"
        self.last_reload_timestamp = 0.0
        atexit.register(self.shutdown)

    def _safe_set_shader_input(self, node, name: str, value) -> bool:
        """Panda3D may assert if a uniform is absent; disable the pass instead of crashing."""
        if not node or node.isEmpty():
            return False
        try:
            node.setShaderInput(name, value)
            return True
        except AssertionError as exc:
            print(f"[ShaderSystem] Shader input '{name}' is unavailable: {exc}")
            return False
        except Exception as exc:
            print(f"[ShaderSystem] Failed to set shader input '{name}': {exc}")
            return False

    def initialize(self):
        self._load_shaders()
        self.postprocess_supported = self.post_shader is not None
        self._ensure_default_preset()
        self.load_preset("default")
        self._start_listener()

    def shutdown(self):
        self.listener_running = False
        if self.listener_socket:
            try:
                self.listener_socket.close()
            except Exception:
                pass
            self.listener_socket = None
        if self.debug_panel_process and self.debug_panel_process.poll() is None:
            try:
                self.debug_panel_process.terminate()
            except Exception:
                pass
        self.debug_panel_process = None

    def _shader_path(self, name: str) -> str:
        root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(root, "shaders", name)

    def _load_shader_pair(self, vert_name: str, frag_name: str):
        vert_path = Filename.fromOsSpecific(self._shader_path(vert_name))
        frag_path = Filename.fromOsSpecific(self._shader_path(frag_name))
        try:
            return Shader.load(
                Shader.SL_GLSL,
                vertex=vert_path,
                fragment=frag_path,
            )
        except Exception as exc:
            print(f"[ShaderSystem] Failed to load shader pair {vert_name}/{frag_name}: {exc}")
            return None

    def _load_shaders(self):
        self.target_shader = self._load_shader_pair("target.vert", "target.frag")
        self.weapon_shader = self._load_shader_pair("weapon.vert", "weapon.frag")
        self.post_shader = self._load_shader_pair("postprocess.vert", "postprocess.frag")

    def _preset_dir(self) -> str:
        root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(root, "shader_presets")

    def _preset_path(self, preset_name: str) -> str:
        safe_name = "".join(ch for ch in (preset_name or "default") if ch.isalnum() or ch in ("_", "-", " ")).strip()
        if not safe_name:
            safe_name = "default"
        return os.path.join(self._preset_dir(), f"{safe_name}.json")

    def _ensure_preset_dir(self):
        os.makedirs(self._preset_dir(), exist_ok=True)

    def _ensure_default_preset(self):
        self._ensure_preset_dir()
        default_path = self._preset_path("default")
        if os.path.exists(default_path):
            return
        with open(default_path, "w", encoding="utf-8") as preset_file:
            json.dump(make_preset_payload("default", make_default_shader_state()), preset_file, indent=2)

    def list_presets(self) -> list[str]:
        self._ensure_preset_dir()
        presets = []
        for entry in os.listdir(self._preset_dir()):
            if not entry.lower().endswith(".json"):
                continue
            presets.append(os.path.splitext(entry)[0])
        return sorted(presets, key=str.lower)

    def load_preset(self, preset_name: str) -> bool:
        preset_path = self._preset_path(preset_name)
        if not os.path.exists(preset_path):
            return False
        try:
            with open(preset_path, "r", encoding="utf-8") as preset_file:
                payload = json.load(preset_file)
            safe_payload = sanitize_preset_payload(payload)
            self.state = safe_payload["state"]
            self.loaded_preset_state = sanitize_shader_state({}, self.state)
            self.current_preset_name = safe_payload["name"]
            return True
        except Exception as exc:
            self.last_reload_status = f"Preset load failed: {exc}"
            return False

    def save_preset(self, preset_name: str) -> bool:
        try:
            self._ensure_preset_dir()
            preset_path = self._preset_path(preset_name)
            payload = make_preset_payload(preset_name, self.state)
            with open(preset_path, "w", encoding="utf-8") as preset_file:
                json.dump(payload, preset_file, indent=2)
            self.current_preset_name = payload["name"]
            self.loaded_preset_state = sanitize_shader_state({}, self.state)
            return True
        except Exception as exc:
            self.last_reload_status = f"Preset save failed: {exc}"
            return False

    def delete_preset(self, preset_name: str) -> bool:
        if preset_name == "default":
            self.last_reload_status = "Default preset is protected"
            return False
        preset_path = self._preset_path(preset_name)
        if not os.path.exists(preset_path):
            return False
        try:
            os.remove(preset_path)
            if self.current_preset_name == preset_name:
                self.current_preset_name = "default"
                self.load_preset("default")
            return True
        except Exception as exc:
            self.last_reload_status = f"Preset delete failed: {exc}"
            return False

    def is_preset_dirty(self) -> bool:
        return self.state != self.loaded_preset_state

    def set_state_bool(self, key: str, value: bool):
        self.state = sanitize_shader_state({key: bool(value)}, self.state)

    def set_state_value(self, key: str, value: float):
        self.state = sanitize_shader_state({key: float(value)}, self.state)

    def reset_state(self):
        self.state = sanitize_shader_state({}, None)

    def reload_shaders(self):
        try:
            self._disable_postprocess()
            self.current_weapon_np = None
            self._load_shaders()
            self.postprocess_supported = self.post_shader is not None
            self.rebind_scene_objects()
            self.last_reload_status = "Shaders reloaded"
            self.last_reload_timestamp = time.time()
            return True
        except Exception as exc:
            self.last_reload_status = f"Shader reload failed: {exc}"
            self.last_reload_timestamp = time.time()
            return False

    def get_ui_snapshot(self) -> dict:
        registry = build_technique_registry(self.state)
        panels = build_panel_registry(self.state)
        render_size = (0, 0)
        framebuffer_size = (0, 0)
        if self.game.win:
            render_size = (int(self.game.win.getXSize()), int(self.game.win.getYSize()))
            framebuffer_size = (int(self.game.win.getFbXSize()), int(self.game.win.getFbYSize()))
        buffer_size = None
        if self.scene_buffer:
            buffer_size = (int(self.scene_buffer.getXSize()), int(self.scene_buffer.getYSize()))

        return {
            "tabs": TAB_LAYOUT,
            "registry": registry,
            "panels": panels,
            "current_preset": self.current_preset_name,
            "preset_dirty": self.is_preset_dirty(),
            "preset_names": self.list_presets(),
            "compile_status": self.last_reload_status,
            "compile_timestamp": self.last_reload_timestamp,
            "active_count": count_enabled_techniques(registry),
            "technique_count": len(registry),
            "render_size": render_size,
            "framebuffer_size": framebuffer_size,
            "buffer_size": buffer_size,
            "post_stage_applied": self.post_stage_applied,
            "post_supported": self.postprocess_supported,
            "pipeline_order": [
                "scene capture",
                "clarity/color base",
                "bloom/glare",
                "lens/distortion",
                "gameplay-reactive overlays",
                "utility/debug overlays",
            ],
        }

    def _ensure_postprocess(self):
        desired_stage = int(round(float(self.state.get("post_debug_stage", 0.0))))
        desired_stage = max(0, min(3, desired_stage))
        enabled = bool(self.state.get("post_enabled", False)) and desired_stage > 0

        if (not enabled) or (not self.postprocess_supported) or (not self.game.win) or (not self.game.cam):
            self._disable_postprocess()
            return

        if self.scene_buffer and self.post_quad and self.post_stage_applied == desired_stage:
            return

        self._disable_postprocess()

        try:
            self.main_region = self._find_main_region()
            if self.main_region is None:
                raise RuntimeError("main camera display region not found")
            self.main_region_original_camera = self.main_region.getCamera()

            self.scene_tex = Texture()
            self.scene_tex.setWrapU(Texture.WMClamp)
            self.scene_tex.setWrapV(Texture.WMClamp)

            fbprops = FrameBufferProperties(self.game.win.getFbProperties())
            fbprops.setBackBuffers(0)
            if fbprops.getDepthBits() == 0:
                fbprops.setDepthBits(1)

            x_size = max(1, int(self.game.win.getFbXSize()))
            y_size = max(1, int(self.game.win.getFbYSize()))

            winprops = WindowProperties()
            winprops.setSize(x_size, y_size)
            self.scene_buffer = self.game.graphicsEngine.makeOutput(
                self.game.win.getPipe(),
                "postprocess-scene",
                -100,
                fbprops,
                winprops,
                GraphicsPipe.BFRefuseWindow | GraphicsPipe.BFResizeable,
                self.game.win.getGsg(),
                self.game.win,
            )
            if self.scene_buffer is None:
                raise RuntimeError("makeOutput returned None")

            self.scene_buffer.addRenderTexture(
                self.scene_tex,
                GraphicsOutput.RTMBindOrCopy,
                GraphicsOutput.RTPColor,
            )

            self.scene_buffer.setSort(-100)
            self.scene_buffer.setClearColor(self.game.win.getClearColor())
            self.scene_buffer.setClearColorActive(True)

            self.post_camera_np = self.render_attach_post_camera()
            self.scene_region = self.scene_buffer.makeDisplayRegion()
            self.scene_region.setCamera(self.post_camera_np)
            self.scene_region.setActive(True)

            self.post_quad = self._create_present_quad()
            self.post_quad.setColor(1, 1, 1, 1)

            if desired_stage == 1:
                self.post_quad.clearShader()
            else:
                self.post_quad.setShader(self.post_shader)
                if not self._safe_set_shader_input(self.post_quad, "scene_tex", self.scene_tex):
                    raise RuntimeError("scene_tex shader input unavailable")

            self.main_region.setActive(False)
            self.post_stage_applied = desired_stage
            self.postprocess_failed_stage = None
            print(f"[ShaderSystem] Fullscreen postprocess stage {desired_stage} enabled")
        except Exception as exc:
            if self.postprocess_failed_stage != desired_stage:
                print(f"[ShaderSystem] Failed to enable fullscreen postprocess stage {desired_stage}: {exc}")
                self.postprocess_failed_stage = desired_stage
            self._disable_postprocess()

    def _disable_postprocess(self):
        if self.main_region is not None:
            try:
                self.main_region.setActive(True)
                if self.main_region_original_camera is not None:
                    self.main_region.setCamera(self.main_region_original_camera)
            except Exception:
                pass
        self.main_region_original_camera = None
        self.main_region = None

        if self.post_quad and not self.post_quad.isEmpty():
            try:
                self.post_quad.clearShader()
                self.post_quad.removeNode()
            except Exception:
                pass
        self.post_quad = None

        if self.post_camera_np and not self.post_camera_np.isEmpty():
            self.post_camera_np.removeNode()
        self.post_camera_np = None

        self.scene_region = None
        if self.scene_buffer is not None:
            try:
                self.game.graphicsEngine.removeWindow(self.scene_buffer)
            except Exception:
                pass
        self.scene_buffer = None
        self.scene_tex = None
        self.post_stage_applied = 0

    def _find_main_region(self):
        region = None
        best_area = -1.0
        for dr in self.game.win.getDisplayRegions():
            if dr.getCamera() != self.game.cam or not dr.isActive():
                continue
            width = max(0.0, dr.getRight() - dr.getLeft())
            height = max(0.0, dr.getTop() - dr.getBottom())
            area = width * height
            if area > best_area:
                best_area = area
                region = dr
        return region

    def _create_present_quad(self):
        quad = NodePath(self.scene_buffer.getTextureCard())
        quad.reparentTo(self.game.render2d)
        quad.setDepthTest(False)
        quad.setDepthWrite(False)
        quad.setBin("background", 0)
        quad.setTransparency(False)
        return quad

    def render_attach_post_camera(self):
        lens = self.game.camLens.makeCopy()
        camera = Camera("postprocess-scene-camera")
        camera.setLens(lens)
        post_camera_np = self.game.render.attachNewNode(camera)
        post_camera_np.setMat(self.game.camera.getMat(self.game.render))
        return post_camera_np

    def _sync_post_camera(self):
        if not self.post_camera_np or self.post_camera_np.isEmpty():
            return
        self.post_camera_np.setMat(self.game.camera.getMat(self.game.render))
        post_lens = self.post_camera_np.node().getLens()
        post_lens.setFov(self.game.camLens.getFov())
        post_lens.setAspectRatio(self.game.camLens.getAspectRatio())
        post_lens.setNearFar(self.game.camLens.getNear(), self.game.camLens.getFar())

    def _start_listener(self):
        if self.listener_thread:
            return

        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.bind(("127.0.0.1", SHADER_CONTROL_PORT))
        self.listener_socket.setblocking(False)
        self.listener_running = True
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()

    def _listener_loop(self):
        while self.listener_running:
            try:
                data, _addr = self.listener_socket.recvfrom(65535)
                payload = json.loads(data.decode("utf-8"))
                if isinstance(payload, dict):
                    with self.state_lock:
                        self.pending_state = payload
            except BlockingIOError:
                time.sleep(0.02)
            except Exception:
                time.sleep(0.05)

    def _apply_pending_state(self):
        with self.state_lock:
            payload = self.pending_state
            self.pending_state = None
        if payload is not None:
            self.state = sanitize_shader_state(payload, self.state)

    def toggle_debug_panel(self):
        """Opens/closes the external ImGui shader control panel."""
        if self.debug_panel_process and self.debug_panel_process.poll() is None:
            try:
                self.debug_panel_process.terminate()
            except Exception:
                pass
            self.debug_panel_process = None
            return

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shader_debug_imgui.py")
        try:
            self.debug_panel_process = subprocess.Popen([sys.executable, script_path])
        except Exception as exc:
            print(f"[ShaderSystem] Failed to launch shader panel: {exc}")

    def mark_target_hit(self, target_obj):
        self.target_states[id(target_obj)] = {
            "hit_until": time.time() + 0.15,
        }
        self.hit_tint_until = max(self.hit_tint_until, time.time() + 0.12)

    def pulse_weapon(self):
        self.weapon_flash_until = max(self.weapon_flash_until, time.time() + 0.08)

    def rebind_scene_objects(self):
        self._attach_visible_weapon()
        for target in getattr(self.game, "targets", []):
            self._attach_target(target)

    def _attach_target(self, target):
        visual = getattr(target, "visual", None)
        if not visual or visual.isEmpty() or self.target_shader is None:
            return
        if visual.getShader() != self.target_shader:
            visual.setShader(self.target_shader)
            self._safe_set_shader_input(visual, "u_time", 0.0)
            self._safe_set_shader_input(visual, "u_hit_flash", 0.0)
            self._safe_set_shader_input(visual, "u_emissive_strength", 0.0)
            self._safe_set_shader_input(visual, "u_dissolve_amount", 0.0)
            self._safe_set_shader_input(visual, "u_pulse_speed", 0.0)
            self._safe_set_shader_input(visual, "u_materialize_progress", 1.0)
            self._safe_set_shader_input(visual, "u_master_enabled", 1.0)
            self._safe_set_shader_input(visual, "u_target_enabled", 1.0)

    def _attach_visible_weapon(self):
        weapon_np = None
        if hasattr(self.game, "weapon_models") and self.game.current_weapon in self.game.weapon_models:
            weapon_np = self.game.weapon_models[self.game.current_weapon]
        if not weapon_np or weapon_np.isEmpty() or self.weapon_shader is None:
            return
        if self.current_weapon_np != weapon_np:
            self.current_weapon_np = weapon_np
            weapon_np.setShader(self.weapon_shader)
            self._safe_set_shader_input(weapon_np, "u_time", 0.0)
            self._safe_set_shader_input(weapon_np, "u_weapon_flash", 0.0)
            self._safe_set_shader_input(weapon_np, "u_fresnel_strength", 0.0)
            self._safe_set_shader_input(weapon_np, "u_recoil_amount", 0.0)
            self._safe_set_shader_input(weapon_np, "u_ads_amount", 0.0)
            self._safe_set_shader_input(weapon_np, "u_master_enabled", 1.0)
            self._safe_set_shader_input(weapon_np, "u_weapon_enabled", 1.0)

    def update(self, dt: float):
        self._apply_pending_state()
        self._ensure_postprocess()
        self._sync_post_camera()
        self.rebind_scene_objects()

        now = time.time()
        state = self.state
        materialize_duration = 0.42
        visible_target_ids = set()

        for target in getattr(self.game, "targets", []):
            visual = getattr(target, "visual", None)
            if not visual or visual.isEmpty():
                continue
            target_id = id(target)
            visible_target_ids.add(target_id)
            is_active = bool(getattr(target, "is_active", True)) and not visual.isHidden()
            was_active = self.target_visibility.get(target_id)
            if is_active and was_active is not True:
                self.target_materialize_started[target_id] = now
            self.target_visibility[target_id] = is_active
            if not is_active:
                continue

            target_state = self.target_states.get(target_id, {})
            hit_flash = 0.0
            hit_until = target_state.get("hit_until", 0.0)
            if hit_until > now:
                hit_flash = (hit_until - now) / 0.15
            elif target_id in self.target_states:
                self.target_states.pop(target_id, None)

            materialize_progress = 1.0
            started_at = self.target_materialize_started.get(target_id)
            if started_at is not None:
                materialize_progress = max(0.0, min(1.0, (now - started_at) / materialize_duration))
                if materialize_progress >= 1.0:
                    self.target_materialize_started.pop(target_id, None)

            self._safe_set_shader_input(visual, "u_time", now)
            self._safe_set_shader_input(visual, "u_hit_flash", hit_flash * state["target_hit_flash"])
            self._safe_set_shader_input(visual, "u_emissive_strength", state["target_emissive"])
            self._safe_set_shader_input(visual, "u_dissolve_amount", state["target_dissolve_test"])
            self._safe_set_shader_input(visual, "u_pulse_speed", state["target_pulse_speed"])
            self._safe_set_shader_input(visual, "u_materialize_progress", materialize_progress)
            self._safe_set_shader_input(visual, "u_master_enabled", 1.0 if state["master_enabled"] else 0.0)
            self._safe_set_shader_input(visual, "u_target_enabled", 1.0 if state["target_enabled"] else 0.0)

        stale_target_ids = set(self.target_visibility.keys()) - visible_target_ids
        for target_id in stale_target_ids:
            self.target_visibility.pop(target_id, None)
            self.target_materialize_started.pop(target_id, None)
            self.target_states.pop(target_id, None)

        if self.current_weapon_np and not self.current_weapon_np.isEmpty():
            recoil_amount = min(
                1.0,
                abs(getattr(self.game, "recoil_pitch", 0.0)) / max(getattr(self.game, "max_recoil_pitch", 1.0), 0.001),
            )
            flash_amount = 0.0
            if self.weapon_flash_until > now:
                flash_amount = (self.weapon_flash_until - now) / 0.08
            self._safe_set_shader_input(self.current_weapon_np, "u_time", now)
            self._safe_set_shader_input(self.current_weapon_np, "u_weapon_flash", flash_amount * state["weapon_flash_strength"])
            self._safe_set_shader_input(self.current_weapon_np, "u_fresnel_strength", state["weapon_fresnel"])
            self._safe_set_shader_input(self.current_weapon_np, "u_recoil_amount", recoil_amount)
            self._safe_set_shader_input(
                self.current_weapon_np,
                "u_ads_amount",
                max(0.0, min(1.0, float(getattr(self.game, "aim_transition", 0.0)))),
            )
            self._safe_set_shader_input(self.current_weapon_np, "u_master_enabled", 1.0 if state["master_enabled"] else 0.0)
            self._safe_set_shader_input(self.current_weapon_np, "u_weapon_enabled", 1.0 if state["weapon_enabled"] else 0.0)

        if self.post_quad and not self.post_quad.isEmpty() and self.post_stage_applied >= 2:
            window_props = self.game.win.getProperties()
            x_size = max(1, int(window_props.getXSize()))
            y_size = max(1, int(window_props.getYSize()))
            current_speed = getattr(self.game, "horizontal_velocity", Vec4(0, 0, 0, 0)).length()
            speed_factor = min(1.0, current_speed / 25.0)
            ads_factor = max(0.0, min(1.0, float(getattr(self.game, "aim_transition", 0.0))))
            combo_factor = max(0.0, min(1.0, float(getattr(self.game, "combo_multiplier", 1.0)) - 1.0))
            hit_factor = 0.0
            if self.hit_tint_until > now:
                hit_factor = (self.hit_tint_until - now) / 0.12

            post_enabled = 1.0 if self.post_stage_applied >= 3 and state["post_enabled"] else 0.0
            ok = True
            ok &= self._safe_set_shader_input(self.post_quad, "u_master_enabled", 1.0 if state["master_enabled"] else 0.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_post_enabled", post_enabled)
            ok &= self._safe_set_shader_input(self.post_quad, "u_vignette", state["post_vignette"] if self.post_stage_applied >= 3 else 0.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_contrast", state["post_contrast"] if self.post_stage_applied >= 3 else 1.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_saturation", state["post_saturation"] if self.post_stage_applied >= 3 else 1.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_sharpen", state["post_sharpen"] if self.post_stage_applied >= 3 else 0.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_hit_tint_strength", hit_factor * state["post_hit_tint"] if self.post_stage_applied >= 3 else 0.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_speed_strength", speed_factor * state["post_speed_strength"] if self.post_stage_applied >= 3 else 0.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_texel_size", Vec2(1.0 / x_size, 1.0 / y_size))
            ok &= self._safe_set_shader_input(self.post_quad, "u_time", now)
            ok &= self._safe_set_shader_input(self.post_quad, "u_ads_amount", ads_factor if self.post_stage_applied >= 3 else 0.0)
            ok &= self._safe_set_shader_input(self.post_quad, "u_combo_amount", combo_factor if self.post_stage_applied >= 3 else 0.0)
            if not ok:
                print("[ShaderSystem] Disabling fullscreen postprocess due to shader input mismatch")
                self.postprocess_supported = False
                self._disable_postprocess()
