#version 150

uniform float u_time;
uniform float u_weapon_flash;
uniform float u_fresnel_strength;
uniform float u_recoil_amount;
uniform float u_ads_amount;
uniform float u_master_enabled;
uniform float u_weapon_enabled;

in vec4 v_color;
in float v_height;
in vec3 v_local_pos;

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
    float barrel_mask = smoothstep(0.25, 1.15, v_local_pos.y);
    float muzzle_mask = smoothstep(0.80, 1.45, v_local_pos.y);
    float heat_response = clamp((u_weapon_flash * 0.65) + (u_recoil_amount * 0.55) + (u_ads_amount * 0.15), 0.0, 1.0);
    float heat_wave = 0.5 + 0.5 * sin(u_time * 9.0 + v_local_pos.y * 7.5 + v_local_pos.x * 11.0);
    vec3 heat_color = mix(vec3(0.90, 0.22, 0.08), vec3(1.00, 0.70, 0.18), heat_wave);

    vec3 color = base + vec3(highlight);
    color = mix(color, color + heat_color * (0.18 + 0.10 * pulse), barrel_mask * heat_response);
    color += vec3(1.0, 0.75, 0.35) * u_weapon_flash * (0.9 + 0.1 * pulse);
    color += vec3(1.0, 0.82, 0.40) * muzzle_mask * u_weapon_flash * (1.15 + 0.25 * pulse);
    color += vec3(0.08, 0.04, 0.02) * u_recoil_amount;
    color += vec3(0.02, 0.03, 0.06) * muzzle_mask * u_ads_amount;
    fragColor = vec4(color, 1.0);
}
