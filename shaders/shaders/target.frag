#version 150

uniform sampler2D p3d_Texture0;
uniform float u_time;
uniform float u_hit_flash;
uniform float u_emissive_strength;
uniform float u_dissolve_amount;
uniform float u_pulse_speed;
uniform float u_materialize_progress;
uniform float u_master_enabled;
uniform float u_target_enabled;

in vec2 v_uv;

out vec4 fragColor;

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float sample_alpha(vec2 uv) {
    return texture(p3d_Texture0, clamp(uv, vec2(0.0), vec2(1.0))).a;
}

void main() {
    vec4 base = texture(p3d_Texture0, v_uv);
    if (u_master_enabled < 0.5 || u_target_enabled < 0.5) {
        fragColor = base;
        return;
    }

    float pulse = 0.5 + 0.5 * sin(u_time * max(u_pulse_speed, 0.001));
    float emissive = u_emissive_strength * pulse;
    float luminance = dot(base.rgb, vec3(0.2126, 0.7152, 0.0722));
    float reactive_mask = smoothstep(0.18, 0.85, luminance) * (0.35 + 0.65 * pulse);
    vec3 color = base.rgb + vec3(emissive * 0.15, emissive * 0.08, emissive * 0.18);
    color += vec3(0.06, 0.10, 0.22) * reactive_mask * (0.35 + u_emissive_strength);
    color = mix(color, vec3(1.0, 0.35, 0.25), clamp(u_hit_flash, 0.0, 1.0));

    float alpha = base.a;
    vec2 outline_texel = fwidth(v_uv) * 1.75 + vec2(0.0015);
    float outline_neighbor = 0.0;
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv + vec2(outline_texel.x, 0.0)));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv - vec2(outline_texel.x, 0.0)));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv + vec2(0.0, outline_texel.y)));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv - vec2(0.0, outline_texel.y)));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv + outline_texel));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv - outline_texel));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv + vec2(outline_texel.x, -outline_texel.y)));
    outline_neighbor = max(outline_neighbor, sample_alpha(v_uv + vec2(-outline_texel.x, outline_texel.y)));
    float outline_mask = clamp(outline_neighbor - base.a, 0.0, 1.0) * (0.40 + 0.60 * pulse);
    vec3 outline_color = mix(vec3(0.08, 0.20, 0.58), vec3(1.0, 0.52, 0.18), clamp(u_hit_flash, 0.0, 1.0));

    if (u_dissolve_amount > 0.001) {
        float noise = hash12(v_uv * 37.0);
        float keep = smoothstep(u_dissolve_amount - 0.03, u_dissolve_amount + 0.06, noise);
        float dissolve_edge = 1.0 - smoothstep(0.0, 0.08, abs(noise - u_dissolve_amount));
        alpha *= keep;
        color += vec3(1.0, 0.46, 0.14) * dissolve_edge * 0.22;
    }

    if (u_materialize_progress < 0.999) {
        float sweep_noise = hash12(v_uv * vec2(21.3, 47.9));
        float sweep = v_uv.y + (sweep_noise - 0.5) * 0.24;
        float reveal = smoothstep(sweep - 0.12, sweep + 0.06, u_materialize_progress);
        float frontier = 1.0 - smoothstep(0.0, 0.08, abs(u_materialize_progress - sweep));
        alpha *= reveal;
        color += vec3(0.28, 0.62, 1.0) * frontier * (1.0 - reveal * 0.35);
    }

    float final_alpha = max(alpha, outline_mask * 0.95);
    vec3 final_color = mix(color, outline_color, outline_mask * (1.0 - alpha));
    fragColor = vec4(final_color, final_alpha);
}
