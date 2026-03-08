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

in vec2 v_uv;

out vec4 fragColor;

vec3 apply_saturation(vec3 color, float sat) {
    float luma = dot(color, vec3(0.299, 0.587, 0.114));
    return mix(vec3(luma), color, sat);
}

void main() {
    vec4 src = texture(scene_tex, v_uv);
    if (u_master_enabled < 0.5 || u_post_enabled < 0.5) {
        fragColor = src;
        return;
    }

    vec3 color = src.rgb;

    if (u_sharpen > 0.001) {
        vec3 north = texture(scene_tex, v_uv + vec2(0.0, u_texel_size.y)).rgb;
        vec3 south = texture(scene_tex, v_uv - vec2(0.0, u_texel_size.y)).rgb;
        vec3 east = texture(scene_tex, v_uv + vec2(u_texel_size.x, 0.0)).rgb;
        vec3 west = texture(scene_tex, v_uv - vec2(u_texel_size.x, 0.0)).rgb;
        vec3 blur = (north + south + east + west) * 0.25;
        color = mix(color, color + (color - blur), clamp(u_sharpen, 0.0, 1.0));
    }

    color = (color - 0.5) * u_contrast + 0.5;
    color = apply_saturation(color, u_saturation);

    vec2 centered = v_uv * 2.0 - 1.0;
    float vignette = 1.0 - dot(centered, centered) * u_vignette;
    color *= clamp(vignette, 0.0, 1.0);

    color = mix(color, color + vec3(0.10, 0.01, 0.01), clamp(u_hit_tint_strength, 0.0, 1.0));
    color = mix(color, color + vec3(0.01, 0.03, 0.08), clamp(u_speed_strength, 0.0, 1.0));

    fragColor = vec4(color, src.a);
}
