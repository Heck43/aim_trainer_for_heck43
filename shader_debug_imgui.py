"""External ImGui shader control panel."""
from __future__ import annotations

import json
import socket
import sys
import time

from imgui_bundle import hello_imgui, imgui

from shader_shared import SHADER_CONTROL_PORT, make_default_shader_state, sanitize_shader_state


class ShaderPanelApp:
    def __init__(self):
        self.state = make_default_shader_state()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.last_send = 0.0

    def send_state(self, force: bool = False):
        now = time.time()
        if not force and now - self.last_send < 0.05:
            return
        payload = json.dumps(self.state).encode("utf-8")
        self.sock.sendto(payload, ("127.0.0.1", SHADER_CONTROL_PORT))
        self.last_send = now

    def gui(self):
        changed = False

        imgui.text("Aim Trainer Shader Control")
        imgui.separator()

        c, self.state["master_enabled"] = imgui.checkbox("Master enabled", self.state["master_enabled"])
        changed = changed or c
        c, self.state["target_enabled"] = imgui.checkbox("Target shader", self.state["target_enabled"])
        changed = changed or c
        c, self.state["weapon_enabled"] = imgui.checkbox("Weapon shader", self.state["weapon_enabled"])
        changed = changed or c
        c, self.state["post_enabled"] = imgui.checkbox("Postprocess shader", self.state["post_enabled"])
        changed = changed or c

        imgui.separator()
        imgui.text("Target")
        c, self.state["target_hit_flash"] = imgui.slider_float("Hit Flash", self.state["target_hit_flash"], 0.0, 4.0)
        changed = changed or c
        c, self.state["target_emissive"] = imgui.slider_float("Emissive", self.state["target_emissive"], 0.0, 3.0)
        changed = changed or c
        c, self.state["target_pulse_speed"] = imgui.slider_float("Pulse Speed", self.state["target_pulse_speed"], 0.0, 8.0)
        changed = changed or c
        c, self.state["target_dissolve_test"] = imgui.slider_float("Dissolve Test", self.state["target_dissolve_test"], 0.0, 1.0)
        changed = changed or c

        imgui.separator()
        imgui.text("Weapon")
        c, self.state["weapon_fresnel"] = imgui.slider_float("Fresnel", self.state["weapon_fresnel"], 0.0, 4.0)
        changed = changed or c
        c, self.state["weapon_flash_strength"] = imgui.slider_float("Shot Flash", self.state["weapon_flash_strength"], 0.0, 4.0)
        changed = changed or c

        imgui.separator()
        imgui.text("Postprocess")
        c, self.state["post_vignette"] = imgui.slider_float("Vignette", self.state["post_vignette"], 0.0, 1.0)
        changed = changed or c
        c, self.state["post_contrast"] = imgui.slider_float("Contrast", self.state["post_contrast"], 0.5, 2.0)
        changed = changed or c
        c, self.state["post_saturation"] = imgui.slider_float("Saturation", self.state["post_saturation"], 0.0, 2.0)
        changed = changed or c
        c, self.state["post_sharpen"] = imgui.slider_float("Sharpen", self.state["post_sharpen"], 0.0, 2.0)
        changed = changed or c
        c, self.state["post_hit_tint"] = imgui.slider_float("Hit Tint", self.state["post_hit_tint"], 0.0, 1.0)
        changed = changed or c
        c, self.state["post_speed_strength"] = imgui.slider_float("Speed FX", self.state["post_speed_strength"], 0.0, 1.0)
        changed = changed or c

        imgui.separator()
        if imgui.button("Reset Defaults"):
            self.state = make_default_shader_state()
            changed = True
        imgui.same_line()
        if imgui.button("Close Panel"):
            hello_imgui.get_runner_params().app_shall_exit = True

        self.state = sanitize_shader_state(self.state)
        self.send_state(force=changed)


def main():
    app = ShaderPanelApp()
    params = hello_imgui.SimpleRunnerParams()
    params.window_title = "Aim Trainer Shader Debug"
    params.window_size = (480, 760)
    params.gui_function = app.gui
    params.fps_idle = 20
    params.enable_idling = False
    app.send_state(force=True)
    hello_imgui.run(params)


if __name__ == "__main__":
    sys.exit(main() or 0)
