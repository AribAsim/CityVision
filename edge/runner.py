"""
edge/runner.py
--------------
CLI entrypoint for the edge pipeline.

Usage (from repo root, with venv active):

  # Use webcam (device 0):
  python -m edge.runner --bus BUS-01

  # Use a video file:
  python -m edge.runner --bus BUS-01 --video path/to/demo.mp4

  # Headless (no preview window):
  python -m edge.runner --bus BUS-01 --video demo.mp4 --no-preview

  # Dry-run (no HTTP POST):
  python -m edge.runner --bus BUS-01 --video demo.mp4 --dry-run

Pipeline per frame:
  Read frame → YOLO inference → for each anomaly detection → EventBuilder.process()
  EventBuilder handles dedup, severity, evidence, and HTTP POST internally.

Visual overlay:
  All detected boxes (including non-anomaly) are drawn on the preview window
  with green=anomaly, yellow=other class, text label + confidence.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

# ---------------------------------------------------------------------------
# Make sure repo root is in sys.path so relative imports work
# regardless of how the module is invoked
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from edge.anomaly_tracker import AnomalyTracker
from edge.bus_simulator import BusSimulator
from edge.detector import ANOMALY_CLASSES, RoadDetector
from edge.event_builder import EventBuilder
from edge.gps_simulator import GPSSimulator
from edge.track_stitcher import TrackStitcher


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SIH26124 Edge Pipeline")
    p.add_argument("--bus", default="BUS-01",
                   choices=["BUS-01", "BUS-02", "BUS-03"],
                   help="Simulated bus identifier")
    p.add_argument("--video", default=None,
                   help="Path to video file. Omit for live webcam (device 0).")
    p.add_argument("--api", default="http://localhost:8000/api/ingest",
                   help="FastAPI ingestion endpoint URL")
    p.add_argument("--no-preview", action="store_true",
                   help="Disable the OpenCV preview window (useful for headless servers)")
    p.add_argument("--dry-run", action="store_true",
                   help="Skip HTTP POST (useful for offline testing)")
    p.add_argument("--model", default=None,
                   help="Override model path (defaults to RoadDetectionModel/…/best.pt)")
    return p.parse_args()


def run(args: argparse.Namespace) -> None:
    # ------------------------------------------------------------------
    # Initialise components
    # ------------------------------------------------------------------
    bus = BusSimulator(bus_id=args.bus, video_source=args.video)
    detector = RoadDetector(model_path=args.model) if args.model else RoadDetector()
    gps = GPSSimulator(route_id=bus.route_id)   # total_frames filled later
    event_builder = EventBuilder(
        bus_id=bus.bus_id,
        route_id=bus.route_id,
        api_url=args.api,
        dry_run=args.dry_run,
    )

    # ------------------------------------------------------------------
    # Open video source
    # ------------------------------------------------------------------
    source = args.video if args.video else 0
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[RUNNER] ERROR: Cannot open source '{source}'", file=sys.stderr)
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if total_frames > 0:
        gps = GPSSimulator(route_id=bus.route_id, total_frames=total_frames)

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tracker = AnomalyTracker(frame_rate=max(int(fps), 1))
    stitcher = TrackStitcher()

    print(f"[RUNNER] Bus={bus.bus_id}  Route={bus.route_id}  Source={source}")
    print(f"[RUNNER] Resolution={frame_w}x{frame_h}  FPS={fps:.1f}  Frames={total_frames or 'live'}")
    print(f"[RUNNER] API={args.api}  DryRun={args.dry_run}  Preview={not args.no_preview}")
    print("[RUNNER] Press 'q' in the preview window to quit.\n")

    frame_idx = 0
    raw_yolo_detections = 0
    anomaly_detections = 0
    total_completed_tracks = 0
    dispatched = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"[RUNNER] End of stream at frame {frame_idx}.")
                break

            # --- GPS location for this frame ---
            location = gps.get_location(frame_idx)

            # --- YOLO inference (all classes) ---
            all_detections = detector.detect(frame)
            raw_yolo_detections += len(all_detections)
            anomaly_detections += sum(1 for d in all_detections if d.class_name in ANOMALY_CLASSES)

            # --- Physical Anomaly Tracking (ByteTrack) ---
            completed_tracks = tracker.update(
                detections=all_detections,
                frame=frame,
                location=location,
                frame_idx=frame_idx,
            )

            # --- Motion-Compensated Track Stitching (Gap-Based) ---
            ready_to_dispatch = []
            for c_track in completed_tracks:
                ready_to_dispatch.extend(stitcher.process_completed_track(c_track, frame_idx))

            # --- Dispatch events for any tracks ready this frame ---
            for c_track in ready_to_dispatch:
                total_completed_tracks += 1
                event = event_builder.process_track(
                    completed_track=c_track,
                    frame_w=frame_w,
                    frame_h=frame_h,
                )
                if event is not None:
                    dispatched += 1

            # --- Draw ALL boxes on preview frame ---
            display_frame = frame.copy()
            for det in all_detections:
                x1, y1, x2, y2 = det.bbox
                color = (0, 200, 0) if det.class_name in ANOMALY_CLASSES else (0, 200, 255)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                label = f"{det.class_name} {det.confidence:.0%}"
                cv2.putText(display_frame, label, (x1, max(y1 - 6, 14)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # --- GPS overlay ---
            gps_text = f"GPS: {location.latitude:.5f},{location.longitude:.5f}  Hdg:{location.heading_deg:.0f}\u00b0"
            cv2.putText(display_frame, gps_text, (10, frame_h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
            bus_text = f"{bus.bus_id} | {bus.route_id} | Frame {frame_idx} | Tracks: {tracker.active_track_count}"
            cv2.putText(display_frame, bus_text, (10, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # --- Show preview ---
            if not args.no_preview:
                cv2.imshow("SIH26124 Edge Pipeline", display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("[RUNNER] User quit.")
                    break

            frame_idx += 1

        # --- Flush remaining active tracks at end of stream ---
        eos_tracks = tracker.flush()
        for c_track in eos_tracks:
            stitcher.process_completed_track(c_track, frame_idx + 100)
        final_stitched_tracks = stitcher.flush()

        for c_track in final_stitched_tracks:
            total_completed_tracks += 1
            event = event_builder.process_track(
                completed_track=c_track,
                frame_w=frame_w,
                frame_h=frame_h,
            )
            if event is not None:
                dispatched += 1

    finally:
        cap.release()
        if not args.no_preview:
            cv2.destroyAllWindows()

        unique_tracks = tracker._next_track_id - 1
        events_created = event_builder.metrics["events_created"]

        print(f"\n[RUNNER] ================= DIAGNOSTICS =================")
        print(f"[RUNNER] Frames processed: {frame_idx}")
        print(f"[RUNNER] Raw YOLO detections: {raw_yolo_detections}")
        print(f"[RUNNER] Anomaly detections: {anomaly_detections}")
        print(f"[RUNNER] Active tracks: {tracker.active_track_count}")
        print(f"[RUNNER] Completed tracks: {total_completed_tracks}")
        print(f"[RUNNER] Unique physical tracks: {unique_tracks}")
        print(f"[RUNNER] Events created: {events_created}")
        print(f"[RUNNER] Events dispatched: {dispatched}")
        print(f"[RUNNER] ================================================\n")


def main() -> None:
    run(build_args())


if __name__ == "__main__":
    main()
