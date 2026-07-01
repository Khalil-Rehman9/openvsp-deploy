"""Build OpenVSP AngelScript lines from UAV parameters."""

from __future__ import annotations

from .model_registry import ParmTarget, UavModel


def _set_parm_line(geom_name: str, container: str, parm_name: str, value: float) -> str:
    return (
        f'string _g = FindGeom("{geom_name}", 0); '
        f'string _p = GetParm(_g, "{parm_name}", "{container}"); '
        f"SetParmVal(_p, {value});"
    )


def build_geometry_commands(model: UavModel, params: dict[str, float]) -> list[str]:
    lines: list[str] = []
    for target in model.parm_targets:
        if target.json_key not in params:
            continue
        lines.append(
            _set_parm_line(target.geom_name, target.container, target.parm_name, params[target.json_key])
        )
    if not lines:
        raise ValueError(f"No geometry parameters provided for {model.id}")
    lines.append("Update();")
    return lines


def build_vspaero_commands(
    *,
    mach: float,
    alpha_start: float,
    alpha_end: float,
    alpha_step: float,
    reynolds: float,
) -> list[str]:
    """Configure VSPAERO analysis settings via OpenVSP API."""
    return [
        'string _a = FindGeom("VSPAEROSettings", 0);',
        'if (_a != "") {',
        f'  SetParmVal(GetParm(_a, "Mach", "VSPAERO"), {mach});',
        f'  SetParmVal(GetParm(_a, "ReCref", "VSPAERO"), {reynolds});',
        f'  SetParmVal(GetParm(_a, "AlphaStart", "VSPAERO"), {alpha_start});',
        f'  SetParmVal(GetParm(_a, "AlphaEnd", "VSPAERO"), {alpha_end});',
        f'  SetParmVal(GetParm(_a, "AlphaNpts", "VSPAERO"), '
        f"{max(2, int((alpha_end - alpha_start) / alpha_step) + 1)});",
        "}",
        "Update();",
    ]


def build_export_commands(results_dir: str, case_name: str) -> list[str]:
    return [
        f'SetVSP3FileName("{results_dir}/{case_name}.vsp3");',
        f'WriteVSPFile("{results_dir}/{case_name}.vsp3", SET_ALL);',
    ]
