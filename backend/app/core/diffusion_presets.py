# diffusion_presets.py
# diffusion mode 관리 파일

from backend.app.core.schemas import CompositionMode

PRESET_TABLE = {
    CompositionMode.rigid: {
        "control_weight": 0.9,
        "ip_adapter_scale": 0.55,
    },
    CompositionMode.balanced: {
        "control_weight": 0.6,
        "ip_adapter_scale": 0.35,
    },
    CompositionMode.creative: {
        "control_weight": 0.35,
        "ip_adapter_scale": 0.18,
    },
}

def resolve_preset(mode, override_control=None, override_ip=None):
    # 1) 문자열로 들어올 가능성 방어
    if isinstance(mode, str):
        try:
            mode = CompositionMode(mode)
        except ValueError:
            mode = CompositionMode.balanced

    base = PRESET_TABLE.get(mode, PRESET_TABLE[CompositionMode.balanced])

    # 2) 기본은 프리셋 값
    cw = base["control_weight"]
    ip = base["ip_adapter_scale"]

    # 3) override는 "실제 양수일 때만" 반영
    if override_control is not None and override_control > 0:
        cw = override_control
    if override_ip is not None and override_ip > 0:
        ip = override_ip

    # 4) 안전 범위 클램핑
    cw = max(0.3, min(1.0, cw))
    ip = max(0.1, min(0.6, ip))

    print(
        f"[Preset] mode={mode} ({type(mode)}), "
        f"override_control={override_control}, override_ip={override_ip}, "
        f"resolved_control={cw}, resolved_ip={ip}"
    )

    return cw, ip
