"""UAV model → OpenVSP geom/container/parameter mapping."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParmTarget:
    geom_name: str
    container: str
    parm_name: str
    json_key: str


@dataclass(frozen=True)
class UavModel:
    id: str
    label: str
    geometry_file: str
    parm_targets: tuple[ParmTarget, ...] = field(default_factory=tuple)
    default_mach: float = 0.15
    default_alpha_start: float = 0.0
    default_alpha_end: float = 12.0
    default_alpha_step: float = 2.0
    default_re: float = 1_000_000.0


MODELS: dict[str, UavModel] = {
    "hero-400ec": UavModel(
        id="hero-400ec",
        label="Hero 400EC",
        geometry_file="/data/geometry/hero-400ec.vsp3",
        parm_targets=(
            ParmTarget("wing", "WingGeom", "TotalSpan", "span"),
        ),
    ),
    "shahed-136": UavModel(
        id="shahed-136",
        label="Shahed 136",
        geometry_file="/data/geometry/shahed-136.vsp3",
        parm_targets=(
            ParmTarget("wing", "WingGeom", "TotalSpan", "span"),
        ),
    ),
    "aai-shadow": UavModel(
        id="aai-shadow",
        label="AAI Shadow",
        geometry_file="/data/geometry/aai-shadow.vsp3",
        parm_targets=(
            ParmTarget("WingGeom", "XSec_1", "Root_Chord", "rootChord"),
            ParmTarget("WingGeom", "XSec_1", "Tip_Chord", "tipChord"),
        ),
    ),
    "iai-heron": UavModel(
        id="iai-heron",
        label="IAI Heron",
        geometry_file="/data/geometry/iai-heron.vsp3",
        parm_targets=(
            ParmTarget("WingGeom", "XSec_1", "Root_Chord", "rootChord"),
            ParmTarget("WingGeom", "XSec_1", "Tip_Chord", "tipChord"),
            ParmTarget("WingGeom", "XSec_2", "Root_Chord", "outerRootChord"),
            ParmTarget("WingGeom", "XSec_2", "Tip_Chord", "outerTipChord"),
        ),
    ),
}


def get_model(vehicle_id: str) -> UavModel:
    key = vehicle_id.strip().lower().replace(" ", "-")
    if key not in MODELS:
        known = ", ".join(sorted(MODELS))
        raise KeyError(f"Unknown vehicle '{vehicle_id}'. Known: {known}")
    return MODELS[key]
