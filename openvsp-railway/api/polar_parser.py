"""Parse VSPAero polar / coefficient text output into JSON-friendly rows."""

from __future__ import annotations

import re
from pathlib import Path


def _parse_floats(line: str) -> list[float]:
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", line)]


_VSPAERO_RESULT_ROW = re.compile(
    r"^\s*(\d+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)\s+"
    r"([\d.eE+-]+)"
)


def parse_vspaero_stdout(text: str) -> list[dict[str, float]]:
    """
    Extract converged alpha / CL / CD rows from VSPAero console output.

    Uses wake-iteration result lines (Iter Mach AoA Beta CLo CLi CLtot CDo CDi CDtot L/D ...).
    """
    rows: list[dict[str, float]] = []
    seen_alphas: set[float] = set()

    for raw in text.splitlines():
        match = _VSPAERO_RESULT_ROW.match(raw)
        if not match:
            continue
        wake_iter = int(match.group(1))
        if wake_iter != 3:
            continue
        alpha = float(match.group(3))
        cl = float(match.group(7))
        cdi = float(match.group(9))
        cd = float(match.group(10))
        key = round(alpha, 6)
        if key in seen_alphas:
            continue
        seen_alphas.add(key)
        rows.append({"alpha": alpha, "cl": cl, "cd": cd, "cdi": cdi})

    rows.sort(key=lambda r: r["alpha"])
    return rows


def parse_polar_file(path: Path) -> list[dict[str, float]]:
    """
    Parse a VSPAero .polar file.

    Data rows use: Beta, Mach, AoA, Re/1e6, CLo, CLi, CLtot, CDo, CDi, CDtot, ...
    """
    if not path.exists():
        return []

    rows: list[dict[str, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not re.search(r"[-+]?(?:\d*\.\d+|\d+)", line):
            continue
        if re.search(r"[A-Za-z]", line.replace("e", "").replace("E", "")):
            # Skip banner/header lines that contain column labels.
            continue
        nums = _parse_floats(line)
        if len(nums) < 10:
            continue
        rows.append({"alpha": nums[2], "cl": nums[6], "cd": nums[9], "cdi": nums[8]})

    rows.sort(key=lambda r: r["alpha"])
    return rows


def find_polar_near(
    case_name: str,
    search_dirs: list[Path],
    *,
    geometry_stem: str | None = None,
) -> Path | None:
    named = [f"{case_name}.polar", f"{case_name}_DegenGeom.polar"]
    if geometry_stem:
        named.extend([f"{geometry_stem}.polar", f"{geometry_stem}_DegenGeom.polar"])

    for directory in search_dirs:
        if not directory.exists():
            continue
        for name in named:
            path = directory / name
            if path.exists():
                return path
        polars = sorted(directory.glob("*.polar"), key=lambda p: p.stat().st_mtime, reverse=True)
        if polars:
            return polars[0]
    return None


def compute_performance(polar: list[dict[str, float]], *, velocity_mps: float = 30.0) -> dict[str, float | None]:
    """Derive simple L/D max and approximate range/endurance scalars from polar."""
    if not polar:
        return {"ld_max": None, "cl_at_ld_max": None, "cd_at_ld_max": None}

    best = max(polar, key=lambda r: (r["cl"] / r["cd"]) if r["cd"] else 0.0)
    ld_max = best["cl"] / best["cd"] if best["cd"] else None

    return {
        "ld_max": ld_max,
        "cl_at_ld_max": best["cl"],
        "cd_at_ld_max": best["cd"],
        "reference_velocity_mps": velocity_mps,
    }
