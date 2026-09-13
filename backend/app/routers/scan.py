"""
backend/app/routers/scan.py
----------------------------
Router for initiating and monitoring bus video scans.
Triggers the existing edge pipeline (edge/runner.py) as an asynchronous subprocess.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .. import schemas

router = APIRouter(prefix="/api/scan", tags=["Scan"])

# Allowed buses
ALLOWED_BUSES = {"BUS-01", "BUS-02", "BUS-03"}

# Uploads directory inside data/uploads
REPO_ROOT = Path(__file__).resolve().parents[3]
UPLOADS_DIR = REPO_ROOT / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store for active/completed scan jobs
# In production/MVP, this keeps state without requiring Redis or Celery
scan_jobs: Dict[str, dict] = {}


def _run_scan_process(job_id: str, bus_id: str, video_path: Path) -> None:
    job = scan_jobs.get(job_id)
    if not job:
        return

    try:
        venv_python = REPO_ROOT / "venv" / "Scripts" / "python.exe"
        python_bin = str(venv_python) if venv_python.exists() else sys.executable

        cmd = [
            python_bin,
            "-u",
            "-m",
            "edge.runner",
            "--bus",
            bus_id,
            "--video",
            str(video_path),
            "--no-preview",
        ]

        print(f"[SCAN] Launching edge runner: {' '.join(cmd)}", flush=True)

        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        job["pid"] = proc.pid
        output_lines = []

        if proc.stdout:
            while True:
                raw_line = proc.stdout.readline()
                if not raw_line:
                    break
                line = raw_line.strip()
                if line:
                    output_lines.append(line)
                    print(f"[EDGE-RUNNER] {line}", flush=True)

                    # Track events dispatched in real-time
                    if "Events dispatched:" in line:
                        m = re.search(r"Events dispatched:\s*(\d+)", line)
                        if m:
                            job["events_dispatched"] = int(m.group(1))
                    elif "[DISPATCHER]" in line and any(k in line for k in ("201", "200", "✓")):
                        job["events_dispatched"] = job.get("events_dispatched", 0) + 1

        proc.wait()

        if proc.returncode == 0:
            job["status"] = "COMPLETED"
            print(f"[SCAN] Job {job_id} COMPLETED. Events dispatched: {job.get('events_dispatched', 0)}", flush=True)
        else:
            job["status"] = "FAILED"
            err_summary = "\n".join(output_lines[-5:]) if output_lines else "Unknown error"
            job["error"] = f"Edge runner failed (exit {proc.returncode}): {err_summary}"
            print(f"[SCAN] Job {job_id} FAILED: {job['error']}", flush=True)

    except Exception as exc:
        job["status"] = "FAILED"
        err_msg = str(exc) or repr(exc)
        job["error"] = f"Edge runner failed: {err_msg}"
        print(f"[SCAN] Job {job_id} EXCEPTION: {job['error']}", flush=True)
    finally:
        # Clean up temporary uploaded video file
        try:
            if video_path.exists():
                video_path.unlink()
        except Exception:
            pass


@router.post("/start", response_model=schemas.ScanStartResponse)
async def start_scan(
    bus_id: str = Form(...),
    route_id: Optional[str] = Form(None),
    video_file: UploadFile = File(...),
):
    """
    Accepts video upload and bus/route parameters, saves video to temporary storage,
    and initiates the existing edge pipeline (edge/runner.py) in a background task.
    """
    # 1. Validate bus_id
    if bus_id not in ALLOWED_BUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bus_id '{bus_id}'. Must be one of: {', '.join(sorted(ALLOWED_BUSES))}",
        )

    # 2. Validate video file format
    if not video_file.filename:
        raise HTTPException(status_code=400, detail="Missing video file filename")

    ext = os.path.splitext(video_file.filename)[1].lower()
    if ext != ".mp4":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Only .mp4 video files are supported.",
        )

    # 3. Create job record
    job_id = str(uuid.uuid4())
    temp_video_path = UPLOADS_DIR / f"scan_{job_id}{ext}"

    # 4. Save uploaded file to disk
    try:
        with open(temp_video_path, "wb") as f:
            while chunk := await video_file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)
    except Exception as e:
        if temp_video_path.exists():
            temp_video_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    # 5. Register job state
    scan_jobs[job_id] = {
        "job_id": job_id,
        "bus_id": bus_id,
        "route_id": route_id,
        "filename": video_file.filename,
        "status": "PROCESSING",
        "events_dispatched": 0,
        "error": None,
    }

    # 6. Launch background runner task via threading.Thread (cross-platform)
    thread = threading.Thread(
        target=_run_scan_process,
        args=(job_id, bus_id, temp_video_path),
        daemon=True,
    )
    thread.start()

    return schemas.ScanStartResponse(
        job_id=job_id,
        status="PROCESSING",
        message=f"{bus_id} scan initiated for {video_file.filename}",
    )

    return schemas.ScanStartResponse(
        job_id=job_id,
        status="PROCESSING",
        message=f"{bus_id} scan initiated for {video_file.filename}",
    )


@router.get("/status/{job_id}", response_model=schemas.ScanStatusResponse)
def get_scan_status(job_id: str):
    """
    Returns current status and event count of a video scan job.
    """
    job = scan_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")

    return schemas.ScanStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        events_dispatched=job.get("events_dispatched", 0),
        error=job.get("error"),
    )
