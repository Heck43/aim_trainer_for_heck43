"""Shared shader UI/runtime metadata and preset helpers."""
from __future__ import annotations

import copy


SHADER_CONTROL_PORT = 18991
PRESET_VERSION = 1


DEFAULT_SHADER_STATE = {
    "master_enabled": True,
    "target_enabled": True,
    "weapon_enabled": True,
    "post_enabled": False,
    "volumes_enabled": False,
    "debug_views_enabled": False,
    "post_debug_stage": 0.0,
    "target_hit_flash": 1.25,
    "target_emissive": 0.35,
    "target_pulse_speed": 1.25,
    "target_dissolve_test": 0.0,
    "weapon_fresnel": 0.9,
    "weapon_flash_strength": 1.2,
    "post_vignette": 0.28,
    "post_contrast": 1.08,
    "post_saturation": 1.05,
    "post_sharpen": 0.15,
    "post_hit_tint": 0.3,
    "post_speed_strength": 0.15,
}


PARAM_DEFINITIONS = {
    "post_debug_stage": {"label": "Post Stage", "min": 0.0, "max": 3.0, "format": "%.0f"},
    "target_hit_flash": {"label": "Hit Flash", "min": 0.0, "max": 4.0, "format": "%.2f"},
    "target_emissive": {"label": "Emissive", "min": 0.0, "max": 3.0, "format": "%.2f"},
    "target_pulse_speed": {"label": "Pulse Speed", "min": 0.0, "max": 8.0, "format": "%.2f"},
    "target_dissolve_test": {"label": "Dissolve", "min": 0.0, "max": 1.0, "format": "%.2f"},
    "weapon_fresnel": {"label": "Fresnel", "min": 0.0, "max": 4.0, "format": "%.2f"},
    "weapon_flash_strength": {"label": "Shot Flash", "min": 0.0, "max": 4.0, "format": "%.2f"},
    "post_vignette": {"label": "Vignette", "min": 0.0, "max": 1.0, "format": "%.2f"},
    "post_contrast": {"label": "Contrast", "min": 0.5, "max": 2.0, "format": "%.2f"},
    "post_saturation": {"label": "Saturation", "min": 0.0, "max": 2.0, "format": "%.2f"},
    "post_sharpen": {"label": "Sharpen", "min": 0.0, "max": 2.0, "format": "%.2f"},
    "post_hit_tint": {"label": "Hit Tint", "min": 0.0, "max": 1.0, "format": "%.2f"},
    "post_speed_strength": {"label": "Speed FX", "min": 0.0, "max": 1.0, "format": "%.2f"},
}


CLAMP_RULES = {
    key: (meta["min"], meta["max"])
    for key, meta in PARAM_DEFINITIONS.items()
}


BOOL_KEYS = {
    "master_enabled",
    "target_enabled",
    "weapon_enabled",
    "post_enabled",
    "volumes_enabled",
    "debug_views_enabled",
}


TAB_LAYOUT = [
    {"id": "home", "label": "Home"},
    {"id": "techniques", "label": "Techniques"},
    {"id": "targets", "label": "Targets"},
    {"id": "weapon", "label": "Weapon"},
    {"id": "post", "label": "Post"},
    {"id": "volumes", "label": "Volumes"},
    {"id": "stats", "label": "Stats"},
]


TECHNIQUE_DEFINITIONS = [
    {
        "panel": "techniques",
        "group": "Live",
        "technique_id": "target_core",
        "display_name": "Target Core",
        "enabled_key": "target_enabled",
        "stage": "object",
        "order": 10,
        "status": "active",
        "cost": "low",
        "description": "Current live target material controls.",
        "debug_notes": "Backed by the active target GLSL shader.",
        "param_keys": ["target_hit_flash", "target_emissive", "target_pulse_speed", "target_dissolve_test"],
        "panels": ["techniques", "targets"],
    },
    {
        "panel": "techniques",
        "group": "Live",
        "technique_id": "weapon_core",
        "display_name": "Weapon Core",
        "enabled_key": "weapon_enabled",
        "stage": "object",
        "order": 20,
        "status": "active",
        "cost": "low",
        "description": "Current live weapon highlight and shot-response shader.",
        "debug_notes": "Backed by the active weapon GLSL shader.",
        "param_keys": ["weapon_fresnel", "weapon_flash_strength"],
        "panels": ["techniques", "weapon"],
    },
    {
        "panel": "techniques",
        "group": "Live",
        "technique_id": "post_pipeline_debug",
        "display_name": "Post Pipeline",
        "enabled_key": "post_enabled",
        "stage": "fullscreen",
        "order": 30,
        "status": "experimental",
        "cost": "medium",
        "description": "Current fullscreen GLSL capture and postprocess chain.",
        "debug_notes": "Stage 1/2/3 are meant for pipeline validation before new passes are added.",
        "param_keys": [
            "post_debug_stage",
            "post_vignette",
            "post_contrast",
            "post_saturation",
            "post_sharpen",
            "post_hit_tint",
            "post_speed_strength",
        ],
        "panels": ["techniques", "post"],
    },
    {
        "panel": "targets",
        "group": "Reactive",
        "technique_id": "target_outline",
        "display_name": "Target Outline",
        "stage": "object",
        "order": 110,
        "status": "active",
        "cost": "low",
        "description": "Depth-aware rim/outline pass for target readability.",
        "debug_notes": "Integrated into the live target shader and driven by emissive / pulse controls.",
        "param_keys": ["target_emissive", "target_pulse_speed"],
        "panels": ["techniques", "targets"],
    },
    {
        "panel": "targets",
        "group": "Reactive",
        "technique_id": "target_texture_reactive",
        "display_name": "Texture Reactive",
        "stage": "object",
        "order": 120,
        "status": "active",
        "cost": "medium",
        "description": "Texture-driven target reactions and image-aware highlights.",
        "debug_notes": "Integrated into the live target shader and reacts to texture luminance and pulse animation.",
        "param_keys": ["target_emissive", "target_pulse_speed"],
        "panels": ["techniques", "targets"],
    },
    {
        "panel": "targets",
        "group": "Respawn",
        "technique_id": "target_materialize",
        "display_name": "Respawn Materialize",
        "stage": "object",
        "order": 130,
        "status": "active",
        "cost": "medium",
        "description": "Spawn/respawn rematerialization effect for targets.",
        "debug_notes": "Integrated into the live target shader with automatic runtime respawn timing.",
        "param_keys": [],
        "panels": ["techniques", "targets"],
    },
    {
        "panel": "weapon",
        "group": "Surface",
        "technique_id": "weapon_heat",
        "display_name": "Weapon Heat",
        "stage": "object",
        "order": 210,
        "status": "active",
        "cost": "medium",
        "description": "Heat shimmer and barrel heating response.",
        "debug_notes": "Integrated into the live weapon shader and driven by recoil / flash response.",
        "param_keys": ["weapon_fresnel", "weapon_flash_strength"],
        "panels": ["techniques", "weapon"],
    },
    {
        "panel": "weapon",
        "group": "Emission",
        "technique_id": "muzzle_glow",
        "display_name": "Muzzle Glow",
        "stage": "object",
        "order": 220,
        "status": "active",
        "cost": "low",
        "description": "Muzzle flash glow and tracer-driven emissive shaping.",
        "debug_notes": "Integrated into the live weapon shader and keyed off shot flash intensity.",
        "param_keys": ["weapon_flash_strength"],
        "panels": ["techniques", "weapon"],
    },
    {
        "panel": "post",
        "group": "Color",
        "technique_id": "tonemap",
        "display_name": "Tonemap",
        "stage": "fullscreen",
        "order": 310,
        "status": "active",
        "cost": "low",
        "description": "Tonemap and response-curve control before heavier lens FX.",
        "debug_notes": "Integrated into the live post shader and shaped by contrast tuning.",
        "param_keys": ["post_contrast"],
        "panels": ["techniques", "post"],
    },
    {
        "panel": "post",
        "group": "Color",
        "technique_id": "color_grading",
        "display_name": "Color Grading",
        "stage": "fullscreen",
        "order": 320,
        "status": "active",
        "cost": "low",
        "description": "LUT-based grading, vibrance, gamma and lift-gamma-gain controls.",
        "debug_notes": "Integrated into the live post shader with saturation-driven grading and split-tone shaping.",
        "param_keys": ["post_saturation"],
        "panels": ["techniques", "post"],
    },
    {
        "panel": "post",
        "group": "Clarity",
        "technique_id": "clarity_pack",
        "display_name": "Clarity Pack",
        "stage": "fullscreen",
        "order": 330,
        "status": "active",
        "cost": "low",
        "description": "Sharpen, deband and dither tools for crisp aim-trainer readability.",
        "debug_notes": "Integrated into the live post shader with sharpen and local-contrast recovery.",
        "param_keys": ["post_sharpen"],
        "panels": ["techniques", "post"],
    },
    {
        "panel": "post",
        "group": "Lens",
        "technique_id": "lens_pack",
        "display_name": "Lens Pack",
        "stage": "fullscreen",
        "order": 340,
        "status": "experimental",
        "cost": "medium",
        "description": "Bloom, lens dirt, glare streaks and controlled chromatic aberration.",
        "debug_notes": "Integrated into the live post shader with lightweight bloom and radial chromatic fringing.",
        "param_keys": ["post_vignette", "post_speed_strength"],
        "panels": ["techniques", "post"],
    },
    {
        "panel": "post",
        "group": "Gameplay",
        "technique_id": "reactive_overlays",
        "display_name": "Reactive Overlays",
        "stage": "fullscreen",
        "order": 350,
        "status": "active",
        "cost": "low",
        "description": "Damage, kill, combo and ADS-reactive overlays.",
        "debug_notes": "Integrated into the live post shader with hit, movement, ADS and combo response.",
        "param_keys": ["post_hit_tint", "post_speed_strength"],
        "panels": ["techniques", "post"],
    },
    {
        "panel": "post",
        "group": "Utility",
        "technique_id": "debug_views",
        "display_name": "Debug Views",
        "enabled_key": "debug_views_enabled",
        "stage": "debug",
        "order": 360,
        "status": "planned",
        "cost": "low",
        "description": "Depth, mask, UV, threshold and pass debug previews.",
        "debug_notes": "UI shell placeholder for future buffer inspectors.",
        "param_keys": [],
        "panels": ["techniques", "post", "stats"],
    },
    {
        "panel": "volumes",
        "group": "Local Volumes",
        "technique_id": "local_fog_volumes",
        "display_name": "Local Fog Volumes",
        "enabled_key": "volumes_enabled",
        "stage": "volumetric/local",
        "order": 410,
        "status": "planned",
        "cost": "medium",
        "description": "Local fog volumes and height-aware distance fog.",
        "debug_notes": "Placeholder for future GLSL/local-volume implementation.",
        "param_keys": [],
        "panels": ["techniques", "volumes"],
    },
    {
        "panel": "volumes",
        "group": "Local Volumes",
        "technique_id": "heat_haze",
        "display_name": "Heat Haze",
        "stage": "volumetric/local",
        "order": 420,
        "status": "planned",
        "cost": "medium",
        "description": "Heat haze and refractive distortion zones.",
        "debug_notes": "Placeholder for future GLSL/local-volume implementation.",
        "param_keys": [],
        "panels": ["techniques", "volumes"],
    },
    {
        "panel": "volumes",
        "group": "Local Volumes",
        "technique_id": "impact_dust",
        "display_name": "Impact Dust",
        "stage": "volumetric/local",
        "order": 430,
        "status": "planned",
        "cost": "low",
        "description": "Impact dust puffs and muzzle smoke support shell.",
        "debug_notes": "Placeholder for future GLSL/local-volume implementation.",
        "param_keys": [],
        "panels": ["techniques", "volumes"],
    },
    {
        "panel": "volumes",
        "group": "Lighting",
        "technique_id": "light_shafts",
        "display_name": "Light Shafts",
        "stage": "volumetric/local",
        "order": 440,
        "status": "planned",
        "cost": "medium",
        "description": "Optional localized light shafts around bright emitters.",
        "debug_notes": "Placeholder for future GLSL/local-volume implementation.",
        "param_keys": [],
        "panels": ["techniques", "volumes"],
    },
]


def make_default_shader_state() -> dict:
    return copy.deepcopy(DEFAULT_SHADER_STATE)


def sanitize_shader_state(payload: dict | None, base: dict | None = None) -> dict:
    """Merge payload into base/default and clamp values to safe ranges."""
    state = make_default_shader_state() if base is None else copy.deepcopy(base)
    if not payload:
        return state

    for key, value in payload.items():
        if key not in DEFAULT_SHADER_STATE:
            continue
        if key in BOOL_KEYS:
            state[key] = bool(value)
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        min_value, max_value = CLAMP_RULES.get(key, (-1.0e9, 1.0e9))
        state[key] = max(min_value, min(max_value, numeric))

    return state


def build_technique_registry(state: dict | None = None) -> list[dict]:
    """Build a runtime-friendly registry view from the flat shader state."""
    safe_state = sanitize_shader_state({}, base=state)
    registry = []

    for definition in TECHNIQUE_DEFINITIONS:
        technique = copy.deepcopy(definition)
        technique.setdefault("display_name", technique.get("technique_id", "Unnamed Technique"))
        technique.setdefault("status", "planned")
        technique.setdefault("panels", ["techniques"])
        enabled_key = technique.get("enabled_key")
        technique["enabled"] = bool(safe_state.get(enabled_key, False)) if enabled_key else False
        technique["params"] = []
        for key in technique.get("param_keys", []):
            meta = copy.deepcopy(PARAM_DEFINITIONS[key])
            meta["key"] = key
            meta["value"] = safe_state[key]
            technique["params"].append(meta)
        registry.append(technique)

    registry.sort(key=lambda item: (item["panels"][0], item.get("order", 0), item.get("display_name", item.get("technique_id", ""))))
    return registry


def build_panel_registry(state: dict | None = None) -> dict[str, list[dict]]:
    panels = {tab["id"]: [] for tab in TAB_LAYOUT}
    for technique in build_technique_registry(state):
        for panel_id in technique.get("panels", []):
            panels.setdefault(panel_id, []).append(copy.deepcopy(technique))
    return panels


def count_enabled_techniques(registry: list[dict]) -> int:
    return sum(1 for item in registry if item.get("enabled"))


def make_preset_payload(name: str, state: dict | None) -> dict:
    preset_name = (name or "default").strip() or "default"
    return {
        "version": PRESET_VERSION,
        "name": preset_name,
        "state": sanitize_shader_state(state, None),
    }


def sanitize_preset_payload(payload: dict | None) -> dict:
    safe_payload = payload if isinstance(payload, dict) else {}
    return make_preset_payload(str(safe_payload.get("name", "default")), safe_payload.get("state"))
