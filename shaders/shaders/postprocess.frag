#version 150

uniform sampler2D scene_tex;
uniform vec2 u_texel_size;
uniform float u_master_enabled;
uniform float u_post_enabled;
uniform float u_vignette;
uniform float u_contrast;
uniform float u_saturation;
uniform float u_sharpen;
uniform float u_hit_tint_strength;
uniform float u_speed_strength;
uniform float u_time;
uniform float u_ads_amount;
uniform float u_combo_amount;

in vec2 v_uv;

out vec4 fragColor;

vec3 apply_saturation(vec3 color, float sat) {
    float luma = dot(color, vec3(0.299, 0.587, 0.114));
    return mix(vec3(luma), color, sat);
}

float luminance(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

vec3 aces_tonemap(vec3 color) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0, 1.0);
}

void main() {
    vec4 src = texture(scene_tex, v_uv);
    if (u_master_enabled < 0.5 || u_post_enabled < 0.5) {
        fragColor = src;
        return;
    }

    vec3 color = src.rgb;
    vec2 centered = v_uv * 2.0 - 1.0;
    float radial = clamp(dot(centered, centered), 0.0, 1.0);

    vec3 north = texture(scene_tex, v_uv + vec2(0.0, u_texel_size.y)).rgb;
    vec3 south = texture(scene_tex, v_uv - vec2(0.0, u_texel_size.y)).rgb;
    vec3 east = texture(scene_tex, v_uv + vec2(u_texel_size.x, 0.0)).rgb;
    vec3 west = texture(scene_tex, v_uv - vec2(u_texel_size.x, 0.0)).rgb;
    vec3 blur = (north + south + east + west) * 0.25;

    float chroma_shift = (0.0010 + (u_speed_strength * 0.0025) + (u_ads_amount * 0.0015)) * smoothstep(0.05, 1.0, radial);
    if (chroma_shift > 0.00001) {
        vec2 dir = centered * chroma_shift;
        vec3 fringe = vec3(
            texture(scene_tex, v_uv + dir * 1.20).r,
            texture(scene_tex, v_uv).g,
            texture(scene_tex, v_uv - dir).b
        );
        color = mix(color, fringe, 0.55);
    }

    vec3 bloom_taps =
        texture(scene_tex, v_uv + vec2(u_texel_size.x, u_texel_size.y) * 2.0).rgb +
        texture(scene_tex, v_uv + vec2(-u_texel_size.x, u_texel_size.y) * 2.0).rgb +
        texture(scene_tex, v_uv + vec2(u_texel_size.x, -u_texel_size.y) * 2.0).rgb +
        texture(scene_tex, v_uv + vec2(-u_texel_size.x, -u_texel_size.y) * 2.0).rgb;
    vec3 bloom = max((bloom_taps * 0.25) - 0.62, vec3(0.0));
    color += bloom * (0.18 + 0.16 * u_speed_strength + 0.12 * u_vignette);

    if (u_sharpen > 0.001) {
        color = mix(color, color + (color - blur), clamp(u_sharpen, 0.0, 1.0));
        float local_contrast = luminance(color) - luminance(blur);
        color += vec3(local_contrast) * 0.18 * clamp(u_sharpen, 0.0, 1.0);
    }

    vec3 toned = aces_tonemap(max(color, vec3(0.0)) * mix(0.95, 1.30, clamp((u_contrast - 1.0) * 0.85 + 0.35, 0.0, 1.0)));
    color = mix(color, toned, 0.55);
    color = (color - 0.5) * u_contrast + 0.5;
    color = apply_saturation(color, u_saturation);

    float grade_mix = smoothstep(0.22, 0.82, luminance(color));
    color *= mix(vec3(0.95, 0.98, 1.04), vec3(1.04, 1.01, 0.95), grade_mix);

    float vignette = 1.0 - radial * (u_vignette + u_ads_amount * 0.18);
    color *= clamp(vignette, 0.0, 1.0);

    color = mix(color, color + vec3(0.10, 0.01, 0.01), clamp(u_hit_tint_strength, 0.0, 1.0));
    color = mix(color, color + vec3(0.01, 0.03, 0.08), clamp(u_speed_strength, 0.0, 1.0));
    color = mix(color, color + vec3(0.03, 0.05, 0.08) * (1.0 - radial), clamp(u_ads_amount, 0.0, 1.0));
    color += vec3(0.12, 0.06, 0.02) * (0.5 + 0.5 * sin(u_time * 8.0)) * clamp(u_combo_amount, 0.0, 1.0) * (1.0 - radial * 0.75);

    fragColor = vec4(clamp(color, 0.0, 1.0), src.a);
}
