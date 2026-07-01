"""Build OpenVSP AngelScript lines from UAV parameters (MATLAB-aligned)."""

from __future__ import annotations

import math

from .model_registry import UavModel, default_geometry_params


def _set_parm(geom: str, container: str, parm: str, value: float) -> str:
    return (
        f'string _g = FindGeom("{geom}", 0); '
        f'string _p = FindParm(_g, "{parm}", "{container}"); '
        f'if (_p != "") {{ SetParmVal(_p, {value}); }}'
    )


def _set_parm_by_name(geom_name: str, container: str, parm: str, value: float) -> str:
    return (
        f'array<string> _gl = FindGeomsWithName("{geom_name}"); '
        f'if (_gl.size() > 0) {{ '
        f'string _p = FindParm(_gl[0], "{parm}", "{container}"); '
        f'if (_p != "") {{ SetParmVal(_p, {value}); }} }}'
    )


def build_geometry_commands(model: UavModel, params: dict[str, float]) -> list[str]:
    merged = default_geometry_params(model)
    merged.update(params)
    builders = {
        "hero-400ec": _hero_commands,
        "shahed-136": _shahed_commands,
        "aai-shadow": _shadow_commands,
        "iai-heron": _heron_commands,
    }
    lines = builders[model.id](merged)
    if not lines:
        raise ValueError(f"No geometry parameters for {model.id}")
    lines.append("Update();")
    return lines


def _hero_commands(p: dict[str, float]) -> list[str]:
    wing_span = p["wingSpan"]
    wing_chord = p["wingChord"]
    fuse_len = p["fuselageLength"]
    tail_span = p["tailSpan"]
    tail_chord = p["tailChord"]
    return [
        _set_parm("wing", "WingGeom", "TotalSpan", wing_span),
        _set_parm("wing", "XSec_1", "Root_Chord", wing_chord),
        _set_parm("wing", "XSec_1", "Tip_Chord", wing_chord),
        _set_parm("wing", "XSec_1", "Sweep", 5.0),
        _set_parm("wing", "XSec_1", "Sweep_Location", 0.0),
        _set_parm("wing", "XSec_1", "Dihedral", 0.0),
        _set_parm("wing", "XForm", "X_Rel_Rotation", 30.0),
        _set_parm("wing", "XForm", "Y_Rel_Rotation", 0.0),
        _set_parm("wing", "XForm", "Z_Rel_Rotation", 0.0),
        _set_parm("fuselage", "Design", "Length", fuse_len),
        _set_parm("tail", "WingGeom", "TotalSpan", tail_span),
        _set_parm("tail", "XSec_1", "Root_Chord", tail_chord),
        _set_parm("tail", "XForm", "X_Rel_Rotation", 45.0),
        _set_parm("tail", "XForm", "Y_Rel_Rotation", 0.0),
    ]


def _shahed_commands(p: dict[str, float]) -> list[str]:
    semi = p["semiSpan"]
    root = p["rootChord"]
    tip = p["tipChord"]
    fuse = p["fuselageLength"]
    sweep = math.degrees(math.atan2((root - tip) / 2.0, semi)) if semi else 0.0
    total_span = 2.0 * semi
    return [
        _set_parm("wing", "WingGeom", "TotalSpan", total_span),
        _set_parm("wing", "XSec_1", "Root_Chord", root),
        _set_parm("wing", "XSec_1", "Tip_Chord", tip),
        _set_parm("wing", "XSec_1", "Sweep", sweep),
        _set_parm("wing", "XSec_1", "Sweep_Location", 0.0),
        _set_parm("wing", "XSec_1", "Dihedral", 0.0),
        _set_parm("wing", "XForm", "X_Rel_Rotation", 0.0),
        _set_parm("wing", "XForm", "Y_Rel_Rotation", 0.0),
        _set_parm("wing", "XForm", "Z_Rel_Location", 0.0),
        _set_parm("fuselage", "Design", "Length", fuse),
        (
            'array<string> _tl = FindGeomsWithName("tail"); '
            'if (_tl.size() > 0) { string _tz = FindParm(_tl[0], "Z_Rel_Location", "XForm"); '
            'if (_tz != "") { SetParmVal(_tz, 9999.0); } }'
        ),
    ]


def _shadow_commands(p: dict[str, float]) -> list[str]:
    return [
        _set_parm_by_name("WingGeom", "WingGeom", "TotalSpan", p["wingSpan"]),
        _set_parm_by_name("WingGeom", "XSec_1", "Root_Chord", p["wingRootChord"]),
        _set_parm_by_name("WingGeom", "XSec_1", "Tip_Chord", p["wingTipChord"]),
        _set_parm_by_name("WingGeom", "XSec_1", "Dihedral", 0.0),
        _set_parm_by_name("WingGeom", "XForm", "X_Rel_Rotation", 0.0),
        _set_parm_by_name("FuselageGeom", "Design", "Length", p["fuselageLength"]),
        _set_parm_by_name("tail", "WingGeom", "TotalSpan", p["tailSpan"]),
        _set_parm_by_name("tail", "XSec_1", "Root_Chord", p["tailRootChord"]),
        _set_parm_by_name("tail", "XSec_1", "Tip_Chord", p["tailTipChord"]),
        _set_parm_by_name("tail", "XForm", "X_Rel_Rotation", -35.0),
    ]


def _heron_commands(p: dict[str, float]) -> list[str]:
    return [
        _set_parm_by_name("WingGeom", "WingGeom", "TotalSpan", p["wingSpan"]),
        _set_parm_by_name("WingGeom", "XSec_1", "Root_Chord", p["sec1RootChord"]),
        _set_parm_by_name("WingGeom", "XSec_1", "Tip_Chord", p["sec1TipChord"]),
        _set_parm_by_name("WingGeom", "XSec_1", "Span", p["sec1Span"]),
        _set_parm_by_name("WingGeom", "XSec_2", "Root_Chord", p["sec2RootChord"]),
        _set_parm_by_name("WingGeom", "XSec_2", "Tip_Chord", p["sec2TipChord"]),
        _set_parm_by_name("WingGeom", "XSec_2", "Span", p["sec2Span"]),
        _set_parm_by_name("FuselageGeom", "Design", "Length", p["fuselageLength"]),
        _set_parm_by_name("tail", "WingGeom", "TotalSpan", p["tailSpan"]),
        _set_parm_by_name("tail", "XSec_1", "Root_Chord", p["tailRootChord"]),
        _set_parm_by_name("tail", "XSec_1", "Tip_Chord", p["tailTipChord"]),
    ]


def build_vspaero_commands(
    *,
    mach: float,
    alpha_start: float,
    alpha_end: float,
    alpha_step: float,
    reynolds: float,
    wing_geom_names: tuple[str, ...] = ("WingGeom", "wing"),
) -> list[str]:
    alpha_npts = max(2, int((alpha_end - alpha_start) / alpha_step) + 1)
    wing_lookup = " ".join(
        f'if (_wid.size() == 0) {{ _wid = FindGeomsWithName("{name}"); }}' for name in wing_geom_names[1:]
    )
    wing_init = f'array<string> _wid = FindGeomsWithName("{wing_geom_names[0]}"); {wing_lookup}'
    return [
        'SetAnalysisInputDefaults("VSPAEROComputeGeometry");',
        'ExecAnalysis("VSPAEROComputeGeometry");',
        'SetAnalysisInputDefaults("VSPAEROSweep");',
        'array<int> _gs; _gs.push_back(0); SetIntAnalysisInput("VSPAEROSweep", "GeomSet", _gs, 0);',
        'array<int> _rf; _rf.push_back(1); SetIntAnalysisInput("VSPAEROSweep", "RefFlag", _rf, 0);',
        f"{wing_init} SetStringAnalysisInput(\"VSPAEROSweep\", \"WingID\", _wid, 0);",
        f'array<double> _a0; _a0.push_back({alpha_start}); SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", _a0, 0);',
        f'array<double> _a1; _a1.push_back({alpha_end}); SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd", _a1, 0);',
        f'array<int> _an; _an.push_back({alpha_npts}); SetIntAnalysisInput("VSPAEROSweep", "AlphaNpts", _an, 0);',
        f'array<double> _m; _m.push_back({mach}); SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", _m, 0);',
        'array<int> _mn; _mn.push_back(1); SetIntAnalysisInput("VSPAEROSweep", "MachNpts", _mn, 0);',
        f'array<double> _re; _re.push_back({reynolds}); SetDoubleAnalysisInput("VSPAEROSweep", "ReCref", _re, 0);',
        "Update();",
        'ExecAnalysis("VSPAEROSweep");',
    ]
