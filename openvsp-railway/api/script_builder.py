"""Build OpenVSP AngelScript lines from UAV parameters."""

from __future__ import annotations

from .model_registry import UavModel


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
    """
    Run VSPAero through OpenVSP's Analysis Manager (not FindGeom).

    VSPAERO settings are not a geometry component — use VSPAEROComputeGeometry
    then VSPAEROSweep with SetDoubleAnalysisInput / ExecAnalysis.
    """
    alpha_npts = max(2, int((alpha_end - alpha_start) / alpha_step) + 1)
    return [
        'SetAnalysisInputDefaults("VSPAEROComputeGeometry");',
        'ExecAnalysis("VSPAEROComputeGeometry");',
        'SetAnalysisInputDefaults("VSPAEROSweep");',
        'array<int> _gs; _gs.push_back(0); SetIntAnalysisInput("VSPAEROSweep", "GeomSet", _gs, 0);',
        'array<int> _rf; _rf.push_back(1); SetIntAnalysisInput("VSPAEROSweep", "RefFlag", _rf, 0);',
        (
            'array<string> _wid = FindGeomsWithName("WingGeom"); '
            'if (_wid.size() == 0) { _wid = FindGeomsWithName("wing"); } '
            'SetStringAnalysisInput("VSPAEROSweep", "WingID", _wid, 0);'
        ),
        f'array<double> _a0; _a0.push_back({alpha_start}); SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", _a0, 0);',
        f'array<double> _a1; _a1.push_back({alpha_end}); SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd", _a1, 0);',
        f'array<int> _an; _an.push_back({alpha_npts}); SetIntAnalysisInput("VSPAEROSweep", "AlphaNpts", _an, 0);',
        f'array<double> _m; _m.push_back({mach}); SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", _m, 0);',
        'array<int> _mn; _mn.push_back(1); SetIntAnalysisInput("VSPAEROSweep", "MachNpts", _mn, 0);',
        f'array<double> _re; _re.push_back({reynolds}); SetDoubleAnalysisInput("VSPAEROSweep", "ReCref", _re, 0);',
        "Update();",
        'ExecAnalysis("VSPAEROSweep");',
    ]


def build_export_commands(results_dir: str, case_name: str) -> list[str]:
    return [
        f'SetVSP3FileName("{results_dir}/{case_name}.vsp3");',
        f'WriteVSPFile("{results_dir}/{case_name}.vsp3", SET_ALL);',
    ]
