"""
UAV analysis API — bridges user-facing JSON to OpenVSP + VSPAERO on Railway.

Mounts openvsp-mcp routes plus POST /api/analyze for model-specific workflows.
"""

from __future__ import annotations

import os
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openvsp_mcp.fastapi_app import create_app as create_openvsp_app
from pydantic import BaseModel, ConfigDict, Field

from .model_registry import MODELS, default_geometry_params, get_model, input_keys
from .performance_matlab import compute_matlab_performance, default_reynolds
from .polar_parser import (
    compute_performance,
    find_polar_near,
    parse_polar_file,
    parse_vspaero_stdout,
)
from .script_builder import build_geometry_commands, build_vspaero_commands
from .vsp_runner import run_openvsp_script

GEOMETRY_DIR = Path(os.environ.get("GEOMETRY_DIR", "/data/geometry"))
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "/data/results"))
UPLOAD_TOKEN = os.environ.get("UPLOAD_TOKEN", "")
STATIC_DIR = Path(os.environ.get("STATIC_DIR", "/app/static"))


def _workbench_index() -> Path:
    for candidate in (STATIC_DIR / "index.html", Path("/app/static/index.html")):
        if candidate.is_file():
            return candidate
    raise HTTPException(status_code=404, detail="Workbench HTML not found on server")


class AnalyzeRequest(BaseModel):
    vehicle: str = Field(..., description="hero-400ec | shahed-136 | aai-shadow | iai-heron")
    mach: float | None = None
    alphaStart: float | None = None
    alphaEnd: float | None = None
    alphaStep: float | None = None
    reynolds: float | None = Field(None, alias="re")
    velocityMps: float = 30.0
    runVspaero: bool = True

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class AnalyzeResponse(BaseModel):
    vehicle: str
    geometry_file: str
    case_name: str
    script_path: str
    polar_file: str | None
    polar: list[dict[str, float]]
    performance: dict[str, float | None]
    curves: dict[str, list[float]] | None = None
    output_text: list[str] | None = None
    geometry_params: dict[str, float] | None = None
    vspaero_result: str | None


def _extract_geometry_params(body: AnalyzeRequest, model) -> dict[str, float]:
    merged = default_geometry_params(model)
    raw = body.model_dump(exclude_none=True, by_alias=True)
    allowed = input_keys(model)
    for key, value in raw.items():
        if key in allowed:
            merged[key] = float(value)
    return merged


def create_app() -> FastAPI:
    app = create_openvsp_app()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if STATIC_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/workbench", include_in_schema=False)
    def workbench():
        return FileResponse(_workbench_index())

    @app.post("/api/upload-zip")
    async def upload_geometry_zip(
        file: UploadFile = File(...),
        token: str | None = None,
    ):
        """Upload a .zip of .vsp3 files — extracted to /data/geometry/."""
        if UPLOAD_TOKEN and token != UPLOAD_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid upload token")

        filename = Path(file.filename or "").name
        if not filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only .zip files allowed")

        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")

        GEOMETRY_DIR.mkdir(parents=True, exist_ok=True)
        extracted: list[str] = []

        try:
            with zipfile.ZipFile(BytesIO(data)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = Path(info.filename).name
                    if not name.lower().endswith(".vsp3"):
                        continue
                    dest = GEOMETRY_DIR / name
                    dest.write_bytes(zf.read(info))
                    extracted.append(str(dest))
        except zipfile.BadZipFile as exc:
            raise HTTPException(status_code=400, detail="Invalid zip file") from exc

        if not extracted:
            raise HTTPException(status_code=400, detail="Zip contains no .vsp3 files")

        return {"ok": True, "extracted": extracted, "count": len(extracted)}

    @app.post("/api/upload")
    async def upload_geometry(
        file: UploadFile = File(...),
        token: str | None = None,
    ):
        """Fast multipart upload for .vsp3 files → /data/geometry/."""
        if UPLOAD_TOKEN and token != UPLOAD_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid upload token")

        filename = Path(file.filename or "").name
        if not filename.lower().endswith(".vsp3"):
            raise HTTPException(status_code=400, detail="Only .vsp3 files allowed")

        GEOMETRY_DIR.mkdir(parents=True, exist_ok=True)
        dest = GEOMETRY_DIR / filename
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")

        dest.write_bytes(data)
        return {
            "ok": True,
            "path": str(dest),
            "bytes": len(data),
            "filename": filename,
        }

    @app.get("/api/models")
    def list_models():
        return [
            {
                "id": m.id,
                "label": m.label,
                "geometry_file": m.geometry_file,
                "parameters": [
                    {"key": f.key, "label": f.label, "default": f.default}
                    for f in m.input_fields
                ],
                "defaults": {
                    "mach": m.default_mach,
                    "alphaStart": m.default_alpha_start,
                    "alphaEnd": m.default_alpha_end,
                    "alphaStep": m.default_alpha_step,
                    "re": default_reynolds(m.id, default_geometry_params(m)),
                },
            }
            for m in MODELS.values()
        ]

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    def analyze(body: AnalyzeRequest):
        try:
            model = get_model(body.vehicle)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        geom_path = Path(model.geometry_file)
        if not geom_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Geometry not on volume: {geom_path}. Upload .vsp3 to /data/geometry/.",
            )

        geom_params = _extract_geometry_params(body, model)

        try:
            commands = build_geometry_commands(model, geom_params)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        mach = body.mach if body.mach is not None else model.default_mach
        alpha_start = body.alphaStart if body.alphaStart is not None else model.default_alpha_start
        alpha_end = body.alphaEnd if body.alphaEnd is not None else model.default_alpha_end
        alpha_step = body.alphaStep if body.alphaStep is not None else model.default_alpha_step
        reynolds = body.reynolds if body.reynolds is not None else default_reynolds(
            model.id, geom_params
        )

        if body.runVspaero:
            commands.extend(
                build_vspaero_commands(
                    model=model,
                    geometry_path=str(geom_path),
                    mach=mach,
                    alpha_start=alpha_start,
                    alpha_end=alpha_end,
                    alpha_step=alpha_step,
                    reynolds=reynolds,
                )
            )

        case_name = f"{model.id}-{int(alpha_start)}-{int(alpha_end)}"
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        try:
            result = run_openvsp_script(
                str(geom_path),
                commands,
                vspaero_expected=body.runVspaero,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        search_dirs = [geom_path.parent, RESULTS_DIR, Path.cwd()]
        polar_path = find_polar_near(
            case_name,
            search_dirs,
            geometry_stem=geom_path.stem,
        )
        polar_rows: list[dict[str, float]] = []
        if result.vspaero_ran:
            polar_rows = parse_vspaero_stdout(result.stdout)
        if not polar_rows and polar_path:
            polar_rows = parse_polar_file(polar_path)

        polar_perf = compute_performance(polar_rows, velocity_mps=body.velocityMps)
        matlab_perf, curves, output_text = compute_matlab_performance(
            model.id,
            geom_params,
            polar_rows,
        )
        performance = {**polar_perf, **matlab_perf}

        return AnalyzeResponse(
            vehicle=model.id,
            geometry_file=str(geom_path),
            case_name=case_name,
            script_path=result.script_path,
            polar_file=str(polar_path) if polar_path else None,
            polar=polar_rows,
            performance=performance,
            curves=curves,
            output_text=output_text,
            geometry_params=geom_params,
            vspaero_result="vspaero" if result.vspaero_ran else None,
        )

    return app


app = create_app()
