"""
scripts/audit_lineage.py
------------------------
Diagnostic audit script for road anomaly tracking lineage.

Performs a full trace:
  YOLO detection -> tracker_id -> completed track -> event_id

Generates:
  1. data/audit/lineage.csv
  2. data/audit/frame_observations.csv
  3. data/audit/track_{track_id}_{class_name}_best.jpg (best-confidence crop)
  4. data/audit/track_{track_id}_{class_name}_sheet.jpg (multi-frame contact sheet)

DOES NOT modify production code or post HTTP events (runs in dry-run mode).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

# Ensure repo root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from edge.anomaly_tracker import AnomalyTracker, CompletedTrack
from edge.bus_simulator import BusSimulator
from edge.detector import ANOMALY_CLASSES, RoadDetector
from edge.event_builder import EventBuilder
from edge.gps_simulator import GPSSimulator
from edge.track_stitcher import TrackStitcher


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit road anomaly event lineage")
    p.add_argument("--video", default="WhatsApp Video 2026-09-11 at 10.40.32 PM.mp4",
                   help="Path to video file")
    p.add_argument("--bus", default="BUS-01", help="Simulated bus ID")
    p.add_argument("--no-preview", action="store_true", help="Disable preview window")
    p.add_argument("--model", default=None, help="YOLO model override")
    return p.parse_args()


def create_contact_sheet(
    cap: cv2.VideoCapture,
    observations: List[Tuple[int, List[int], float]],  # list of (frame_idx, bbox, conf)
    track_id: int,
    class_name: str,
    output_path: Path,
    max_tiles: int = 8,
) -> None:
    """
    Creates a tiled contact sheet showing up to max_tiles evenly-spaced observations.
    """
    if not observations:
        return

    n_obs = len(observations)
    if n_obs <= max_tiles:
        selected = observations
    else:
        indices = np.linspace(0, n_obs - 1, max_tiles, dtype=int)
        selected = [observations[i] for i in indices]

    tiles = []
    tile_size = (240, 240)  # Standardize each tile size (w, h)

    for frame_idx, bbox, conf in selected:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = bbox
        pad = 20
        x1c = max(x1 - pad, 0)
        y1c = max(y1 - pad, 0)
        x2c = min(x2 + pad, w)
        y2c = min(y2 + pad, h)

        crop = frame[y1c:y2c, x1c:x2c].copy()
        if crop.size == 0:
            continue

        # Draw bbox relative to crop
        rx1, ry1 = x1 - x1c, y1 - y1c
        rx2, ry2 = x2 - x1c, y2 - y1c
        cv2.rectangle(crop, (rx1, ry1), (rx2, ry2), (0, 255, 0), 2)

        # Annotate tile with frame number and conf
        header_text = f"F{frame_idx} | {conf:.0%}"
        cv2.putText(crop, header_text, (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        resized = cv2.resize(crop, tile_size, interpolation=cv2.INTER_AREA)
        tiles.append(resized)

    if not tiles:
        return

    # Tile in a single row or 2-row grid
    cols = min(len(tiles), 4)
    rows = (len(tiles) + cols - 1) // cols

    sheet = np.zeros((rows * tile_size[1], cols * tile_size[0], 3), dtype=np.uint8)
    for idx, t in enumerate(tiles):
        r = idx // cols
        c = idx % cols
        y = r * tile_size[1]
        x = c * tile_size[0]
        sheet[y:y + tile_size[1], x:x + tile_size[0]] = t

    cv2.imwrite(str(output_path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])


def main():
    args = build_args()

    audit_dir = _REPO_ROOT / "data" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    lineage_csv_path = audit_dir / "lineage.csv"
    frame_obs_csv_path = audit_dir / "frame_observations.csv"

    bus = BusSimulator(bus_id=args.bus, video_source=args.video)
    detector = RoadDetector(model_path=args.model) if args.model else RoadDetector()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {args.video}", file=sys.stderr)
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    gps = GPSSimulator(route_id=bus.route_id, total_frames=total_frames)
    event_builder = EventBuilder(
        bus_id=bus.bus_id,
        route_id=bus.route_id,
        dry_run=True,  # Audit only, no HTTP POST
    )

    tracker = AnomalyTracker(frame_rate=max(int(fps), 1))
    stitcher = TrackStitcher()

    print(f"[AUDIT] Starting audit on: {args.video}")
    print(f"[AUDIT] Resolution: {frame_w}x{frame_h}, FPS: {fps:.2f}, Frames: {total_frames}")

    # Track observation history: track_id -> list of (frame_idx, bbox, conf)
    track_history: Dict[int, List[Tuple[int, List[int], float]]] = {}
    raw_completed_all: List[CompletedTrack] = []
    completed_all: List[Tuple[CompletedTrack, dict]] = []

    frame_obs_file = open(frame_obs_csv_path, "w", newline="", encoding="utf-8")
    frame_obs_writer = csv.writer(frame_obs_file)
    frame_obs_writer.writerow(["frame_idx", "class_name", "tracker_id", "x1", "y1", "x2", "y2", "confidence"])

    frame_idx = 0
    raw_dets_count = 0
    anomaly_dets_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            location = gps.get_location(frame_idx)
            all_dets = detector.detect(frame)
            raw_dets_count += len(all_dets)
            anomaly_dets = [d for d in all_dets if d.class_name in ANOMALY_CLASSES]
            anomaly_dets_count += len(anomaly_dets)

            # Update tracker
            completed = tracker.update(
                detections=all_dets,
                frame=frame,
                location=location,
                frame_idx=frame_idx,
            )

            # Log active track observations in this frame
            for (cls_name, tid), rec in tracker._active_records.items():
                # If rec was updated on this frame
                if rec.last_frame_idx == frame_idx:
                    bx = rec.best_bbox
                    # Record history for contact sheet
                    if rec.track_id not in track_history:
                        track_history[rec.track_id] = []
                    track_history[rec.track_id].append((frame_idx, rec.best_bbox, rec.best_confidence))

                    frame_obs_writer.writerow([
                        frame_idx, cls_name, rec.track_id, bx[0], bx[1], bx[2], bx[3], f"{rec.best_confidence:.4f}"
                    ])

            raw_completed_all.extend(completed)

            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"[AUDIT] Processed {frame_idx}/{total_frames} frames...")

        # End of stream flush
        eos = tracker.flush()
        raw_completed_all.extend(eos)

        print(f"[AUDIT] ByteTrack produced {len(raw_completed_all)} completed tracks. Running TrackStitcher...")
        stitched_tracks = stitcher.stitch_tracks(raw_completed_all)
        print(f"[AUDIT] TrackStitcher result: {len(stitched_tracks)} final physical tracks.")

        for c in stitched_tracks:
            evt = event_builder.process_track(c, frame_w, frame_h)
            if evt:
                completed_all.append((c, evt))


    finally:
        frame_obs_file.close()

    print(f"\n[AUDIT] Frame processing complete. Generating audit images and contact sheets...")

    # Open video fresh for seeking to generate contact sheets
    cap_seek = cv2.VideoCapture(args.video)

    lineage_rows = []
    for c, evt in completed_all:
        tid = c.track_id
        cls = c.class_name

        # 1. Best crop image
        best_crop_path = audit_dir / f"track_{tid}_{cls}_best.jpg"
        x1, y1, x2, y2 = c.best_bbox
        pad = 20
        h, w = c.best_frame.shape[:2]
        x1c = max(x1 - pad, 0)
        y1c = max(y1 - pad, 0)
        x2c = min(x2 + pad, w)
        y2c = min(y2 + pad, h)
        crop = c.best_frame[y1c:y2c, x1c:x2c].copy()
        label = f"{cls} #{tid} {c.best_confidence:.0%}"
        cv2.putText(crop, label, (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imwrite(str(best_crop_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 90])

        # 2. Contact sheet
        sheet_path = audit_dir / f"track_{tid}_{cls}_sheet.jpg"
        obs = track_history.get(tid, [])
        create_contact_sheet(cap_seek, obs, tid, cls, sheet_path)

        lineage_rows.append({
            "track_id": tid,
            "class_name": cls,
            "first_frame": c.first_frame_idx,
            "last_frame": c.last_frame_idx,
            "hit_count": c.hit_count,
            "best_confidence": round(c.best_confidence, 4),
            "x1": c.best_bbox[0],
            "y1": c.best_bbox[1],
            "x2": c.best_bbox[2],
            "y2": c.best_bbox[3],
            "latitude": round(c.best_location.latitude, 6),
            "longitude": round(c.best_location.longitude, 6),
            "event_id": evt["event_id"],
        })

    cap_seek.release()
    cap.release()

    # Write lineage.csv
    with open(lineage_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "track_id", "class_name", "first_frame", "last_frame", "hit_count",
            "best_confidence", "x1", "y1", "x2", "y2", "latitude", "longitude", "event_id"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(lineage_rows)

    # Print structured diagnostics table
    print("\n" + "=" * 85)
    print("===== AUDIT LINEAGE =====")
    print("=" * 85)
    print(f"{'track_id':<9} | {'class':<12} | {'frames':<13} | {'hits':<5} | {'conf':<6} | {'lat':<10} | {'lon':<10} | {'event_id'}")
    print("-" * 85)
    for r in lineage_rows:
        frames_str = f"{r['first_frame']} -> {r['last_frame']}"
        print(f"{r['track_id']:<9} | {r['class_name']:<12} | {frames_str:<13} | {r['hit_count']:<5} | {r['best_confidence']:<6.3f} | {r['latitude']:<10.5f} | {r['longitude']:<10.5f} | {r['event_id']}")
    print("=" * 85)
    print(f"Total Frames Processed: {frame_idx}")
    print(f"Raw YOLO Detections: {raw_dets_count}")
    print(f"Anomaly Detections: {anomaly_dets_count}")
    print(f"Total Completed Tracks: {len(completed_all)}")
    print(f"Lineage CSV: {lineage_csv_path}")
    print(f"Observations CSV: {frame_obs_csv_path}")
    print(f"Audit Images Dir: {audit_dir}")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
