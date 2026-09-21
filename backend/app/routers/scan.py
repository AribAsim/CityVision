"""
backend/app/routers/scan.py
----------------------------
Router for initiating and monitoring bus video scans.
Triggers the existing edge pipeline (edge/runner.py) directly in-process
with real-time MJPEG frame streaming to the browser.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import queue
import sys
import threading
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .. import schemas

router = APIRouter(prefix="/api/scan", tags=["Scan"])

# Allowed buses
ALLOWED_BUSES = {"BUS-01", "BUS-02", "BUS-03"}

# Uploads directory inside data/uploads
REPO_ROOT = Path(__file__).resolve().parents[3]
VENV_SITE_PACKAGES = REPO_ROOT / "venv" / "Lib" / "site-packages"
if VENV_SITE_PACKAGES.exists() and str(VENV_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(VENV_SITE_PACKAGES))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

UPLOADS_DIR = REPO_ROOT / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store for active/completed scan jobs
scan_jobs: Dict[str, dict] = {}

# Frame queues for real-time MJPEG stream (job_id -> queue.Queue[bytes | None])
frame_queues: Dict[str, queue.Queue] = {}


def _run_scan_thread(job_id: str, bus_id: str, video_path: Path) -> None:
    job = scan_jobs.get(job_id)
    fq = frame_queues.get(job_id)
    if not job:
        return

    def on_dispatch(count: int) -> None:
        job["events_dispatched"] = count

    try:
        from edge.runner import run as edge_run

        port = os.environ.get("PORT", "8000")
        args = argparse.Namespace(
            bus=bus_id,
            video=str(video_path),
            api=f"http://127.0.0.1:{port}/api/ingest",
            no_preview=True,
            dry_run=False,
            model=None,
            camera_id="FRONT",
            no_vehicles=False,    # Keep vehicle detection active (cars/peds tracked + boxes drawn)
            no_anpr=True,         # Disable ANPR OCR during quick scan
            no_infra=True,        # Disable infra signs during quick scan
            no_waterlog=False,
            benchmark=False,
        )

        print(f"[SCAN] Starting in-process edge runner for job {job_id}, bus {bus_id}", flush=True)
        edge_run(args, frame_queue=fq, on_dispatch=on_dispatch)
        job["status"] = "COMPLETED"
        print(f"[SCAN] Job {job_id} COMPLETED. Events dispatched: {job.get('events_dispatched', 0)}", flush=True)
    except ImportError as exc:
        job["status"] = "FAILED"
        job["error"] = f"Computer vision edge dependencies not installed in this environment ({exc}). Run edge runner locally or install ultralytics & opencv."
        print(f"[SCAN] Job {job_id} MISSING DEPENDENCY: {job['error']}", flush=True)
    except Exception as exc:
        job["status"] = "FAILED"
        err_msg = str(exc) or repr(exc)
        job["error"] = f"Edge runner failed: {err_msg}"
        print(f"[SCAN] Job {job_id} EXCEPTION: {job['error']}", flush=True)
    finally:
        if fq is not None:
            fq.put(None)  # Sentinel value signaling end of stream
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
    and initiates the edge pipeline with real-time frame streaming.
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

    # 6. Initialize frame queue (buffer up to 5 frames for smooth streaming)
    fq: queue.Queue = queue.Queue(maxsize=5)
    frame_queues[job_id] = fq

    # 7. Launch background runner task via threading.Thread
    thread = threading.Thread(
        target=_run_scan_thread,
        args=(job_id, bus_id, temp_video_path),
        daemon=True,
    )
    thread.start()

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


@router.get("/stream/{job_id}")
async def stream_scan_frames(job_id: str):
    """
    MJPEG stream endpoint for real-time annotated frame streaming directly into browser <img> tag.
    """
    fq = frame_queues.get(job_id)
    if not fq:
        raise HTTPException(status_code=404, detail="No active stream for this job")

    async def frame_generator():
        loop = asyncio.get_running_loop()
        try:
            while True:
                # Read next JPEG frame without blocking the asyncio loop
                frame_bytes = await loop.run_in_executor(None, fq.get)
                if frame_bytes is None:
                    # Stream ended (sentinel received)
                    break
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame_bytes
                    + b"\r\n"
                )
        except asyncio.CancelledError:
            pass
        finally:
            frame_queues.pop(job_id, None)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive",
        },
    )
