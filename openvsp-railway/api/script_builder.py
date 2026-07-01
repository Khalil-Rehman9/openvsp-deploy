"""Build OpenVSP AngelScript lines from UAV parameters (MATLAB-aligned)."""

from __future__ import annotations

import math

from .model_registry import UavModel, default_geometry_params


class _ParmWriter:
  """Emit SetParmVal lines with unique AngelScript variable names."""

  def __init__(self) -> None:
    self._n = 0
    self.lines: list[str] = []

  def set_parm(self, geom: str, container: str, parm: str, value: float) -> None:
    idx = self._n
    self._n += 1
    g = f"_g{idx}"
    p = f"_p{idx}"
    self.lines.append(
      f'string {g} = FindGeom("{geom}", 0); '
      f'string {p} = FindParm({g}, "{parm}", "{container}"); '
      f'if ({p} != "") {{ SetParmVal({p}, {value}); }}'
    )

  def set_parm_by_name(self, geom_name: str, container: str, parm: str, value: float) -> None:
    idx = self._n
    self._n += 1
    gl = f"_gl{idx}"
    p = f"_p{idx}"
    self.lines.append(
      f'array<string> {gl} = FindGeomsWithName("{geom_name}"); '
      f"if ({gl}.size() > 0) {{ "
      f'string {p} = FindParm({gl}[0], "{parm}", "{container}"); '
      f'if ({p} != "") {{ SetParmVal({p}, {value}); }} }}'
    )

  def add_raw(self, line: str) -> None:
    self.lines.append(line)


def build_geometry_commands(model: UavModel, params: dict[str, float]) -> list[str]:
  merged = default_geometry_params(model)
  merged.update(params)
  writers = {
    "hero-400ec": _hero_commands,
    "shahed-136": _shahed_commands,
    "aai-shadow": _shadow_commands,
    "iai-heron": _heron_commands,
  }
  writer = writers[model.id](merged)
  if not writer.lines:
    raise ValueError(f"No geometry parameters for {model.id}")
  writer.lines.append("Update();")
  return writer.lines


def _hero_commands(p: dict[str, float]) -> _ParmWriter:
  w = _ParmWriter()
  w.set_parm("wing", "WingGeom", "TotalSpan", p["wingSpan"])
  w.set_parm("wing", "XSec_1", "Root_Chord", p["wingChord"])
  w.set_parm("wing", "XSec_1", "Tip_Chord", p["wingChord"])
  w.set_parm("wing", "XSec_1", "Sweep", 5.0)
  w.set_parm("wing", "XSec_1", "Sweep_Location", 0.0)
  w.set_parm("wing", "XSec_1", "Dihedral", 0.0)
  w.set_parm("wing", "XForm", "X_Rel_Rotation", 30.0)
  w.set_parm("wing", "XForm", "Y_Rel_Rotation", 0.0)
  w.set_parm("wing", "XForm", "Z_Rel_Rotation", 0.0)
  w.set_parm("fuselage", "Design", "Length", p["fuselageLength"])
  w.set_parm("tail", "WingGeom", "TotalSpan", p["tailSpan"])
  w.set_parm("tail", "XSec_1", "Root_Chord", p["tailChord"])
  w.set_parm("tail", "XForm", "X_Rel_Rotation", 45.0)
  w.set_parm("tail", "XForm", "Y_Rel_Rotation", 0.0)
  return w


def _shahed_commands(p: dict[str, float]) -> _ParmWriter:
  semi = p["semiSpan"]
  root = p["rootChord"]
  tip = p["tipChord"]
  fuse = p["fuselageLength"]
  sweep = math.degrees(math.atan2((root - tip) / 2.0, semi)) if semi else 0.0
  total_span = 2.0 * semi
  w = _ParmWriter()
  w.set_parm("wing", "WingGeom", "TotalSpan", total_span)
  w.set_parm("wing", "XSec_1", "Root_Chord", root)
  w.set_parm("wing", "XSec_1", "Tip_Chord", tip)
  w.set_parm("wing", "XSec_1", "Sweep", sweep)
  w.set_parm("wing", "XSec_1", "Sweep_Location", 0.0)
  w.set_parm("wing", "XSec_1", "Dihedral", 0.0)
  w.set_parm("wing", "XForm", "X_Rel_Rotation", 0.0)
  w.set_parm("wing", "XForm", "Y_Rel_Rotation", 0.0)
  w.set_parm("wing", "XForm", "Z_Rel_Location", 0.0)
  w.set_parm("fuselage", "Design", "Length", fuse)
  w.add_raw(
    'array<string> _tl0 = FindGeomsWithName("tail"); '
    'if (_tl0.size() > 0) { string _tz0 = FindParm(_tl0[0], "Z_Rel_Location", "XForm"); '
    'if (_tz0 != "") { SetParmVal(_tz0, 9999.0); } }'
  )
  return w


def _shadow_commands(p: dict[str, float]) -> _ParmWriter:
  w = _ParmWriter()
  w.set_parm_by_name("WingGeom", "WingGeom", "TotalSpan", p["wingSpan"])
  w.set_parm_by_name("WingGeom", "XSec_1", "Root_Chord", p["wingRootChord"])
  w.set_parm_by_name("WingGeom", "XSec_1", "Tip_Chord", p["wingTipChord"])
  w.set_parm_by_name("WingGeom", "XSec_1", "Dihedral", 0.0)
  w.set_parm_by_name("WingGeom", "XForm", "X_Rel_Rotation", 0.0)
  w.set_parm_by_name("FuselageGeom", "Design", "Length", p["fuselageLength"])
  w.set_parm_by_name("tail", "WingGeom", "TotalSpan", p["tailSpan"])
  w.set_parm_by_name("tail", "XSec_1", "Root_Chord", p["tailRootChord"])
  w.set_parm_by_name("tail", "XSec_1", "Tip_Chord", p["tailTipChord"])
  w.set_parm_by_name("tail", "XForm", "X_Rel_Rotation", -35.0)
  return w


def _heron_commands(p: dict[str, float]) -> _ParmWriter:
  w = _ParmWriter()
  w.set_parm_by_name("WingGeom", "WingGeom", "TotalSpan", p["wingSpan"])
  w.set_parm_by_name("WingGeom", "XSec_1", "Root_Chord", p["sec1RootChord"])
  w.set_parm_by_name("WingGeom", "XSec_1", "Tip_Chord", p["sec1TipChord"])
  w.set_parm_by_name("WingGeom", "XSec_1", "Span", p["sec1Span"])
  w.set_parm_by_name("WingGeom", "XSec_2", "Root_Chord", p["sec2RootChord"])
  w.set_parm_by_name("WingGeom", "XSec_2", "Tip_Chord", p["sec2TipChord"])
  w.set_parm_by_name("WingGeom", "XSec_2", "Span", p["sec2Span"])
  w.set_parm_by_name("FuselageGeom", "Design", "Length", p["fuselageLength"])
  w.set_parm_by_name("tail", "WingGeom", "TotalSpan", p["tailSpan"])
  w.set_parm_by_name("tail", "XSec_1", "Root_Chord", p["tailRootChord"])
  w.set_parm_by_name("tail", "XSec_1", "Tip_Chord", p["tailTipChord"])
  return w


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
    f'{wing_init} SetStringAnalysisInput("VSPAEROSweep", "WingID", _wid, 0);',
    f'array<double> _a0; _a0.push_back({alpha_start}); SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", _a0, 0);',
    f'array<double> _a1; _a1.push_back({alpha_end}); SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd", _a1, 0);',
    f'array<int> _an; _an.push_back({alpha_npts}); SetIntAnalysisInput("VSPAEROSweep", "AlphaNpts", _an, 0);',
    f'array<double> _m; _m.push_back({mach}); SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", _m, 0);',
    'array<int> _mn; _mn.push_back(1); SetIntAnalysisInput("VSPAEROSweep", "MachNpts", _mn, 0);',
    f'array<double> _re; _re.push_back({reynolds}); SetDoubleAnalysisInput("VSPAEROSweep", "ReCref", _re, 0);',
    "Update();",
    'ExecAnalysis("VSPAEROSweep");',
  ]
