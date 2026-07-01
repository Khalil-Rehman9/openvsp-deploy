"""UAV model definitions — inputs aligned with MATLAB TESTING38 app."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InputField:
    key: str
    label: str
    default: float


@dataclass(frozen=True)
class UavModel:
    id: str
    label: str
    geometry_file: str
    input_fields: tuple[InputField, ...] = field(default_factory=tuple)
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
        input_fields=(
            InputField("wingSpan", "Wing Span (m)", 2.400),
            InputField("wingChord", "Wing Chord (m)", 0.360),
            InputField("fuselageLength", "Fuselage Length (m)", 2.100),
            InputField("tailSpan", "Tail Span (m)", 0.6832),
            InputField("tailChord", "Tail Chord (m)", 0.205),
        ),
    ),
    "shahed-136": UavModel(
        id="shahed-136",
        label="Shahed 136",
        geometry_file="/data/geometry/shahed-136.vsp3",
        input_fields=(
            InputField("semiSpan", "Wing Semi-span (m)", 2.500),
            InputField("rootChord", "Root Chord (m)", 2.276),
            InputField("tipChord", "Tip Chord (m)", 0.440),
            InputField("fuselageLength", "Fuselage Length (m)", 3.500),
        ),
    ),
    "aai-shadow": UavModel(
        id="aai-shadow",
        label="AAI Shadow 200",
        geometry_file="/data/geometry/aai-shadow.vsp3",
        input_fields=(
            InputField("wingSpan", "Wing Span (m)", 4.68846),
            InputField("wingRootChord", "Wing Root Chord (m)", 0.6586),
            InputField("wingTipChord", "Wing Tip Chord (m)", 0.6586),
            InputField("fuselageLength", "Fuselage Length (m)", 1.6300),
            InputField("tailSpan", "Tail Span (m)", 1.4500),
            InputField("tailRootChord", "Tail Root Chord (m)", 0.4000),
            InputField("tailTipChord", "Tail Tip Chord (m)", 0.4000),
        ),
    ),
    "iai-heron": UavModel(
        id="iai-heron",
        label="IAI Heron",
        geometry_file="/data/geometry/iai-heron.vsp3",
        input_fields=(
            InputField("wingSpan", "Wing Span (m)", 16.677),
            InputField("fuselageLength", "Fuselage Length (m)", 8.50),
            InputField("sec1Span", "Section 1 Span (m)", 1.77872),
            InputField("sec1RootChord", "Section 1 Root Chord (m)", 1.29),
            InputField("sec1TipChord", "Section 1 Tip Chord (m)", 1.29),
            InputField("sec2Span", "Section 2 Span (m)", 6.56),
            InputField("sec2RootChord", "Section 2 Root Chord (m)", 1.29),
            InputField("sec2TipChord", "Section 2 Tip Chord (m)", 0.64),
            InputField("tailSpan", "Tail Span (m)", 3.3),
            InputField("tailRootChord", "Tail Root Chord (m)", 0.81),
            InputField("tailTipChord", "Tail Tip Chord (m)", 0.81),
        ),
    ),
}


def get_model(vehicle_id: str) -> UavModel:
    key = vehicle_id.strip().lower().replace(" ", "-")
    if key not in MODELS:
        known = ", ".join(sorted(MODELS))
        raise KeyError(f"Unknown vehicle '{vehicle_id}'. Known: {known}")
    return MODELS[key]


def default_geometry_params(model: UavModel) -> dict[str, float]:
    return {f.key: f.default for f in model.input_fields}


def input_keys(model: UavModel) -> set[str]:
    return {f.key for f in model.input_fields}
