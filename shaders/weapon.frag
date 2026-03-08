#version 150

uniform float u_time;
uniform float u_weapon_flash;
uniform float u_fresnel_strength;
uniform float u_recoil_amount;
uniform float u_master_enabled;
uniform float u_weapon_enabled;

in vec4 v_color;
in float v_height;

out vec4 fragColor;

void main() {
    vec3 base = max(v_color.rgb, vec3(0.15, 0.15, 0.15));
    if (u_master_enabled < 0.5 || u_weapon_enabled < 0.5) {
        fragColor = vec4(base, 1.0);
        return;
    }

    float pulse = 0.5 + 0.5 * sin(u_time * 5.0);
    float edge_like = smoothstep(-0.4, 0.6, v_height + 0.2);
    float highlight = edge_like * u_fresnel_strength * (0.20 + 0.20 * pulse);
    vec3 color = base + vec3(highlight);
    color += vec3(1.0, 0.75, 0.35) * u_weapon_flash * (0.9 + 0.1 * pulse);
    color += vec3(0.08, 0.04, 0.02) * u_recoil_amount;
    fragColor = vec4(color, 1.0);
}
