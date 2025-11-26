# diffusion_presets.py
# diffusion mode 관리 파일

from backend.app.core.schemas import CompositionMode

PRESET_TABLE = {
    CompositionMode.rigid: {
        "control_weight": 0.9,
        "ip_adapter_scale": 0.55
    },
    CompositionMode.balanced: {
        "control_weight": 0.6,
        "ip_adapter_scale": 0.35
    },
    CompositionMode.creative: {
        "control_weight": 0.35,
        "ip_adapter_scale": 0.18,
    },
}

def resolve_preset(mode, override_control=None, override_ip=None):
    base = PRESET_TABLE.get(mode, PRESET_TABLE[CompositionMode.balanced])

    cw = override_control if override_control is not None else base["control_weight"]
    ip = override_ip if override_ip is not None else base["ip_adapter_scale"]

    # 안전 범위 클램핑
    cw = max(0.3, min(1.0, cw))
    ip = max(0.1, min(0.6, ip))

    return cw, ip    
