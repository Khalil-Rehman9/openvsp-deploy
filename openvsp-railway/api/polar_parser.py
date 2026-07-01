"""Parse VSPAero polar / coefficient text output into JSON-friendly rows."""

from __future__ import annotations

import re
from pathlib import Path


def _parse_floats(line: str) -> list[float]:
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", line)]


def parse_polar_file(path: Path) -> list[dict[str, float]]:
    """
    Parse a .polar or similar whitespace-delimited aero results file.
    Returns rows with alpha, cl, cd when detectable.
    """
    if not path.exists():
        return []

    rows: list[dict[str, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        nums = _parse_floats(line)
        if len(nums) < 3:
            continue
        # Common VSPAero column order: Alpha, CL, CD, ...
        rows.append({"alpha": nums[0], "cl": nums[1], "cd": nums[2]})
    return rows


def find_polar_near(case_name: str, search_dirs: list[Path]) -> Path | None:
    named = [f"{case_name}.polar", f"{case_name}_DegenGeom.polar"]
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
