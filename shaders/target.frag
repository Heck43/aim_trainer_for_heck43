#version 150

uniform sampler2D p3d_Texture0;
uniform float u_time;
uniform float u_hit_flash;
uniform float u_emissive_strength;
uniform float u_dissolve_amount;
uniform float u_pulse_speed;
uniform float u_master_enabled;
uniform float u_target_enabled;

in vec2 v_uv;

out vec4 fragColor;

void main() {
    vec4 base = texture(p3d_Texture0, v_uv);
    if (u_master_enabled < 0.5 || u_target_enabled < 0.5) {
        fragColor = base;
        return;
    }

    float pulse = 0.5 + 0.5 * sin(u_time * max(u_pulse_speed, 0.001));
    float emissive = u_emissive_strength * pulse;
    vec3 color = base.rgb + vec3(emissive * 0.15, emissive * 0.08, emissive * 0.18);
    color = mix(color, vec3(1.0, 0.35, 0.25), clamp(u_hit_flash, 0.0, 1.0));

    float alpha = base.a;
    if (u_dissolve_amount > 0.001) {
        float noise = fract(sin(dot(v_uv * 37.0, vec2(12.9898, 78.233))) * 43758.5453);
        alpha *= step(u_dissolve_amount, noise);
    }

    fragColor = vec4(color, alpha);
}
