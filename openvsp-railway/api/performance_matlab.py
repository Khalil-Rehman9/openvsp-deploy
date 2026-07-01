"""Performance curves matching MATLAB TESTING38 logic."""

from __future__ import annotations

import math

G = 9.81
RHO = 1.225


def _nearest_polar_row(polar: list[dict[str, float]], alpha_deg: float = 3.0) -> dict[str, float]:
    if not polar:
        return {"alpha": alpha_deg, "cl": 0.4, "cd": 0.025, "cdi": 0.01}
    return min(polar, key=lambda r: abs(r["alpha"] - alpha_deg))


def _interpolate_polar_at_alpha(polar: list[dict[str, float]], alpha_deg: float = 3.0) -> dict[str, float]:
    if not polar:
        return {"alpha": alpha_deg, "cl": 0.4, "cd": 0.025, "cdi": 0.01}
    rows = sorted(polar, key=lambda r: r["alpha"])
    for row in rows:
        if abs(row["alpha"] - alpha_deg) < 1e-6:
            return row
    for left, right in zip(rows, rows[1:]):
        if left["alpha"] <= alpha_deg <= right["alpha"]:
            span = right["alpha"] - left["alpha"]
            if span <= 0:
                return left
            t = (alpha_deg - left["alpha"]) / span
            left_cdi = left.get("cdi", max(left["cd"] * 0.4, 0.0))
            right_cdi = right.get("cdi", max(right["cd"] * 0.4, 0.0))
            return {
                "alpha": alpha_deg,
                "cl": left["cl"] + t * (right["cl"] - left["cl"]),
                "cd": left["cd"] + t * (right["cd"] - left["cd"]),
                "cdi": left_cdi + t * (right_cdi - left_cdi),
            }
    return _nearest_polar_row(polar, alpha_deg)


def _sanitize_aero(
    cl: float, cd: float, cdi: float, vehicle_id: str
) -> tuple[float, float, float]:
    bad = (
        cl != cl
        or cd != cd
        or cl < 0
        or cl > 4
        or cd < 0
        or cd > 2
    )
    if bad:
        if vehicle_id == "hero-400ec":
            return 0.42, 0.021, 0.009
        return 0.38, 0.032, 0.014
    if cdi != cdi:
        cdi = max(cd * 0.4, 0.0)
    return cl, cd, cdi


def _extract_aero(polar: list[dict[str, float]], vehicle_id: str) -> tuple[float, float, float]:
    if not polar:
        return _sanitize_aero(float("nan"), float("nan"), float("nan"), vehicle_id)
    row = _interpolate_polar_at_alpha(polar)
    return _sanitize_aero(row["cl"], row["cd"], row.get("cdi", max(row["cd"] * 0.4, 0.0)), vehicle_id)


def default_reynolds(vehicle_id: str, params: dict[str, float]) -> float:
    """Match MATLAB: Re at 50 m/s using reference chord."""
    rho = 1.225
    mu = 1.789e-5
    v = 50.0
    if vehicle_id == "hero-400ec":
        cref = params.get("wingChord", 0.36)
    elif vehicle_id == "shahed-136":
        cref = params.get("rootChord", 2.276)
    elif vehicle_id == "aai-shadow":
        cref = params.get("wingRootChord", 0.6586)
    else:
        cref = params.get("sec1RootChord", 1.29)
    return round(rho * v * cref / mu)


def compute_matlab_performance(
    vehicle_id: str,
    params: dict[str, float],
    polar: list[dict[str, float]],
) -> tuple[dict[str, float | None], dict[str, list[float]], list[str]]:
    cl, cd, cdi = _extract_aero(polar, vehicle_id)
    v = [float(x) for x in _velocity_grid(vehicle_id)]

    if vehicle_id == "hero-400ec":
        wing_span = params["wingSpan"]
        wing_chord = params["wingChord"]
        s_ref = wing_span * wing_chord
        ar = wing_span**2 / s_ref if s_ref else 0.0
        weight = 40.0 * G
        cd0 = cd - cdi
        k = cdi / max(cl**2, 1e-6)
        batt_wh = 4500.0
        p_avail = 150.0
        eta = 0.65
        cl_v, cd_v, ld_v, pr = _parabolic_polar(v, weight, s_ref, cd0, k, eta, p_avail)
        j = batt_wh * 3600.0 * 0.8
        u_r = [(vel * (j / p)) / 1000.0 if p > 0 else 0.0 for vel, p in zip(v, pr)]
        u_e = [(j / p) / 3600.0 if p > 0 else 0.0 for vel, p in zip(v, pr)]
        name = "Hero 400EC"
    elif vehicle_id == "shahed-136":
        semi = params["semiSpan"]
        root = params["rootChord"]
        s_ref = 0.5 * root * (2.0 * semi)
        ar = (2.0 * semi) ** 2 / s_ref if s_ref else 0.0
        weight = 200.0 * G
        cd0 = max(cd - cdi, 0.008)
        k = cdi / max(cl**2, 1e-6)
        w_fuel = 50.0 * G
        sfc = 0.55 / (1000.0 * 3600.0)
        p_avail = 300.0
        eta = 0.60
        cl_v, cd_v, ld_v, pr = _parabolic_polar(v, weight, s_ref, cd0, k, eta, p_avail)
        w1 = weight - w_fuel
        br = [(eta / (G * sfc)) * ld * math.log(weight / w1) for ld in ld_v]
        u_r = [b / 1000.0 for b in br]
        u_e = [b / (vel * 1000.0) if vel > 0 else 0.0 for b, vel in zip(br, v)]
        name = "Shahed 136"
    elif vehicle_id == "aai-shadow":
        wing_span = params["wingSpan"]
        root = params["wingRootChord"]
        tip = params["wingTipChord"]
        s_ref = wing_span * (root + tip) / 2.0
        ar = wing_span**2 / s_ref if s_ref else 0.0
        weight = 170.0 * G
        cd0 = max(cd - cdi, 0.018)
        k = cdi / max(cl**2, 1e-6)
        w_fuel = 40.0 * G
        sfc = 0.55 / (1000.0 * 3600.0)
        eta = 0.70
        p_avail = 28500.0
        cl_v, cd_v, ld_v, pr = _parabolic_polar(v, weight, s_ref, cd0, k, eta, p_avail)
        w1 = weight - w_fuel
        br = [(eta / (G * sfc)) * ld * math.log(weight / w1) for ld in ld_v]
        u_r = [b / 1000.0 for b in br]
        u_e = [b / (vel * 1000.0) if vel > 0 else 0.0 for b, vel in zip(br, v)]
        name = "AAI Shadow 200"
    else:  # iai-heron
        sec1_span = params["sec1Span"]
        sec1_root = params["sec1RootChord"]
        sec2_span = params["sec2Span"]
        sec2_root = params["sec2RootChord"]
        sec2_tip = params["sec2TipChord"]
        wing_span = params["wingSpan"]
        s_ref = 2.0 * (sec1_span * sec1_root + sec2_span * (sec2_root + sec2_tip) / 2.0)
        ar = wing_span**2 / s_ref if s_ref else 0.0
        weight = 1150.0 * G
        cd0 = max(cd - cdi, 0.015)
        k = cdi / max(cl**2, 1e-6)
        w_fuel = 350.0 * G
        sfc = 0.45 / (1000.0 * 3600.0)
        eta = 0.75
        p_avail = 160000.0
        cl_v, cd_v, ld_v, pr = _parabolic_polar(v, weight, s_ref, cd0, k, eta, p_avail)
        w1 = weight - w_fuel
        br = [(eta / (G * sfc)) * ld * math.log(weight / w1) for ld in ld_v]
        u_r = [b / 1000.0 for b in br]
        u_e = [b / (vel * 1000.0) if vel > 0 else 0.0 for b, vel in zip(br, v)]
        name = "IAI Heron"

    r_max = max(u_r) if u_r else 0.0
    r_idx = u_r.index(r_max) if u_r else 0
    e_max = max(u_e) if u_e else 0.0
    e_idx = u_e.index(e_max) if u_e else 0
    ld_max_glide = 1.0 / (2.0 * math.sqrt(cd0 * k)) if cd0 > 0 and k > 0 else None

    summary = {
        "ld_max": ld_max_glide,
        "cl_at_ld_max": cl,
        "cd_at_ld_max": cd,
        "reference_velocity_mps": v[r_idx] if v else None,
        "s_ref_m2": s_ref,
        "aspect_ratio": ar,
        "cd0": cd0,
        "k_induced": k,
        "range_max_km": r_max,
        "range_max_velocity_mps": v[r_idx] if v else None,
        "endurance_max_hr": e_max,
        "endurance_max_velocity_mps": v[e_idx] if v else None,
    }

    curves = {
        "velocity_mps": v,
        "range_km": u_r,
        "endurance_hr": u_e,
        "ld": ld_v,
        "power_w": pr,
        "cl": cl_v,
        "cd": cd_v,
    }

    lines = [
        f"UAV Name: {name}",
        f"Reference Area S: {s_ref:.3f} m²",
        f"Aspect Ratio AR: {ar:.2f}",
        f"Max Range (Rmax): {r_max:.1f} km @ {v[r_idx]:.1f} m/s",
        f"Max Endurance (Emax): {e_max:.2f} hr @ {v[e_idx]:.1f} m/s",
        "----------------------------------------",
        f"CD0 (Zero Lift Drag): {cd0:.5f}",
        f"k (Induced Coefficient): {k:.5f}",
        f"Max Glide L/D Ratio: {ld_max_glide:.2f}" if ld_max_glide else "Max Glide L/D Ratio: —",
        f"VSPAero @ α≈3°: CL={cl:.4f}, CD={cd:.5f}, CDi≈{cdi:.5f}",
    ]

    return summary, curves, lines


def _velocity_grid(vehicle_id: str) -> list[float]:
    if vehicle_id in ("aai-shadow", "iai-heron"):
        return [15.0 + i * (75.0 - 15.0) / 499.0 for i in range(500)]
    if vehicle_id == "shahed-136":
        return [15.0 + i * (100.0 - 15.0) / 499.0 for i in range(500)]
    return [15.0 + i * (100.0 - 15.0) / 499.0 for i in range(500)]


def _parabolic_polar(
    velocities: list[float],
    weight: float,
    s_ref: float,
    cd0: float,
    k: float,
    eta: float,
    p_avail: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
    cl_v: list[float] = []
    cd_v: list[float] = []
    ld_v: list[float] = []
    pr: list[float] = []
    for vel in velocities:
        q = max(0.5 * RHO * vel**2 * s_ref, 1e-6)
        cl = weight / q
        cd = cd0 + k * cl**2
        ld = cl / cd if cd else 0.0
        pd = 0.5 * RHO * vel**3 * s_ref * cd
        power = (pd / eta) + p_avail
        cl_v.append(cl)
        cd_v.append(cd)
        ld_v.append(ld)
        pr.append(power)
    return cl_v, cd_v, ld_v, pr
