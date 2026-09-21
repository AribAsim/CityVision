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
import queue
import sys
import time
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
from edge.behavior_analyzer import check_hit_and_run, should_run_anpr, vru_proximity_risk
from edge.bus_simulator import BusSimulator
from edge.density_accumulator import DensityAccumulator, compute_segment_key
from edge.detector import ANOMALY_CLASSES, RoadDetector
from edge.event_builder import EventBuilder
from edge.gps_simulator import GPSSimulator
from edge.track_stitcher import TrackStitcher
from edge.waterlogging_heuristic import detect_waterlogging


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
                   help="Override road anomaly model path (defaults to RoadDetectionModel/…/best.pt)")
    p.add_argument("--camera-id", default="FRONT",
                   choices=["FRONT", "REAR", "LEFT", "RIGHT"],
                   help="Identifier for the camera stream")
    # Multi-perception & diagnostic flags
    p.add_argument("--no-vehicles", action="store_true",
                   help="Disable secondary vehicle/pedestrian detection")
    p.add_argument("--no-anpr", action="store_true",
                   help="Disable secondary license plate and OCR detection")
    p.add_argument("--no-infra", action="store_true",
                   help="Disable secondary traffic sign and infra detection")
    p.add_argument("--no-waterlog", action="store_true",
                   help="Disable waterlogging heuristic detection")
    p.add_argument("--benchmark", action="store_true",
                   help="Benchmark real inference latencies and FPS across models")
    return p.parse_args()


def run(
    args: argparse.Namespace,
    frame_queue: queue.Queue | None = None,
    on_dispatch: Any | None = None,
) -> None:
    # ------------------------------------------------------------------
    # Initialise components
    # ------------------------------------------------------------------
    bus = BusSimulator(bus_id=args.bus, video_source=args.video)
    detector = RoadDetector(model_path=args.model) if args.model else RoadDetector()

    # Optional multi-perception detectors
    vehicle_detector = None
    if not args.no_vehicles:
        try:
            from edge.vehicle_detector import VehicleDetector
            vehicle_detector = VehicleDetector()
        except Exception as e:
            print(f"[RUNNER] VehicleDetector unavailable ({e}). Continuing without vehicle perception.")

    infra_detector = None
    if not args.no_infra:
        try:
            from edge.infra_detector import InfraDetector
            infra_detector = InfraDetector()
        except Exception as e:
            print(f"[RUNNER] InfraDetector unavailable ({e}). Continuing without infra perception.")

    anpr_pipeline = None
    if not args.no_anpr:
        try:
            from edge.anpr.anpr_pipeline import ANPRPipeline
            anpr_pipeline = ANPRPipeline()
        except Exception as e:
            print(f"[RUNNER] ANPRPipeline unavailable ({e}). Continuing without license plate perception.")

    gps = GPSSimulator(route_id=bus.route_id)   # total_frames filled later
    event_builder = EventBuilder(
        bus_id=bus.bus_id,
        route_id=bus.route_id,
        camera_id=args.camera_id,
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
    print(f"[RUNNER] MultiPerception: Vehicles={vehicle_detector is not None}, Infra={infra_detector is not None}, ANPR={anpr_pipeline is not None}")
    print(f"[RUNNER] API={args.api}  DryRun={args.dry_run}  Preview={not args.no_preview}")
    print("[RUNNER] Press 'q' in the preview window to quit.\n")

    frame_idx = 0
    raw_yolo_detections = 0
    anomaly_detections = 0
    total_completed_tracks = 0
    dispatched = 0

    def _inc_dispatched():
        nonlocal dispatched
        dispatched += 1
        if on_dispatch is not None:
            try:
                on_dispatch(dispatched)
            except Exception:
                pass

    # Timing metrics (ms)
    time_road_ms = []
    time_vehicle_ms = []
    time_infra_ms = []
    time_anpr_ms = []

    # Multi-perception buffers for v2 multi-perception event attachment
    buffered_plates: list[dict] = []
    buffered_signs: list[dict] = []

    # PS-Compliance: Density Accumulator, Behavior Analysis, ANPR trigger tracking
    density_acc = DensityAccumulator()
    current_segment: Optional[str] = None
    anpr_trigger_frame: Optional[int] = None
    from collections import deque
    track_history: deque = deque(maxlen=60)

    def _flush_density(seg: str, loc: Any) -> None:
        if not seg:
            return
        payload = density_acc.flush(
            segment_key=seg,
            lat=loc.latitude,
            lon=loc.longitude,
            route_id=bus.route_id,
            bus_id=bus.bus_id,
        )
        if not args.dry_run:
            try:
                import requests
                telemetry_url = args.api.replace("/api/ingest", "/api/telemetry/density")
                r = requests.post(telemetry_url, json=payload, timeout=3)
                if r.status_code in (200, 201):
                    print(f"[RUNNER] Flushed density for segment {seg}: {payload['total_count']} vehicles")
            except Exception as e:
                print(f"[RUNNER] Telemetry POST failed ({e}). Continuing.")
        else:
            print(f"[RUNNER] [DRY-RUN] Flushed density for segment {seg}: {payload['total_count']} vehicles")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"[RUNNER] End of stream at frame {frame_idx}.")
                break

            # --- GPS location for this frame ---
            location = gps.get_location(frame_idx)
            seg_key = compute_segment_key(bus.route_id, location.latitude, location.longitude)

            # Check if entering a new segment cell
            if current_segment is None:
                current_segment = seg_key
            elif seg_key != current_segment:
                _flush_density(current_segment, location)
                current_segment = seg_key

            # --- YOLO inference: Road Anomalies (Primary) ---
            t0 = time.perf_counter()
            all_detections = detector.detect(frame)
            t1 = time.perf_counter()
            time_road_ms.append((t1 - t0) * 1000.0)

            raw_yolo_detections += len(all_detections)
            anomaly_detections += sum(1 for d in all_detections if d.class_name in ANOMALY_CLASSES)

            # --- Optional Secondary Perception: Vehicles & Pedestrians ---
            vehicle_detections = []
            if vehicle_detector is not None:
                tv0 = time.perf_counter()
                vehicle_detections = vehicle_detector.detect(frame)
                tv1 = time.perf_counter()
                time_vehicle_ms.append((tv1 - tv0) * 1000.0)
                # Accumulate into density buffer
                density_acc.add_frame(seg_key, vehicle_detections)

            # --- Optional Secondary Perception: Traffic Signs / Infra ---
            infra_detections = []
            if infra_detector is not None:
                ti0 = time.perf_counter()
                infra_detections = infra_detector.detect(frame)
                ti1 = time.perf_counter()
                time_infra_ms.append((ti1 - ti0) * 1000.0)
                for idet in infra_detections:
                    buffered_signs.append({
                        "sign_type": idet.class_name,
                        "confidence": round(float(idet.confidence), 4),
                        "bbox": [int(b) for b in idet.bbox],
                    })

            # --- Optional Secondary Perception: ANPR (Incident-Triggered) ---
            plate_reads = []
            if anpr_pipeline is not None and should_run_anpr(anpr_trigger_frame, frame_idx):
                tp0 = time.perf_counter()
                plate_reads = anpr_pipeline.process_frame(frame)
                tp1 = time.perf_counter()
                time_anpr_ms.append((tp1 - tp0) * 1000.0)
                for pr in plate_reads:
                    buffered_plates.append({
                        "plate_text": pr.plate_text,
                        "plate_confidence": round(float(pr.plate_confidence), 4),
                        "ocr_confidence": round(float(pr.ocr_confidence), 4),
                        "bbox": [int(b) for b in pr.bbox],
                    })

            # --- Physical Anomaly Tracking (ByteTrack) ---
            completed_tracks = tracker.update(
                detections=all_detections,
                frame=frame,
                location=location,
                frame_idx=frame_idx,
            )

            # Record track snapshot for behavior analysis (Hit & Run candidate detection)
            current_frame_tracks = []
            for det in vehicle_detections:
                current_frame_tracks.append({
                    "track_id": hash(tuple(det.bbox)) % 10000,
                    "class_name": det.class_name,
                    "bbox": det.bbox,
                    "confidence": det.confidence,
                })
            track_history.append({"frame_idx": frame_idx, "tracks": current_frame_tracks})

            # --- Motion-Compensated Track Stitching (Gap-Based) ---
            ready_to_dispatch = []
            for c_track in completed_tracks:
                ready_to_dispatch.extend(stitcher.process_completed_track(c_track, frame_idx))

            # --- Dispatch events for any tracks ready this frame ---
            for c_track in ready_to_dispatch:
                total_completed_tracks += 1
                plates_to_send = list(buffered_plates)
                signs_to_send = list(buffered_signs)
                event = event_builder.process_track(
                    completed_track=c_track,
                    frame_w=frame_w,
                    frame_h=frame_h,
                    nearby_plates=plates_to_send,
                    nearby_signs=signs_to_send,
                )
                if event is not None:
                    _inc_dispatched()
                    buffered_plates.clear()
                    buffered_signs.clear()

            # --- Telemetry tick & Driver Safety (Rash Driving Heuristic) ---
            bus.tick(dt=1.0 / max(fps, 1.0))
            if bus.check_rash_driving():
                cur_spd = bus.current_speed()
                rash_evt = event_builder.dispatch_safety_event(
                    event_type="Rash-Driving",
                    location=location,
                    frame=frame,
                    confidence=0.88,
                    details={"speed_kmh": cur_spd},
                )
                if rash_evt:
                    _inc_dispatched()
                    anpr_trigger_frame = frame_idx

            # --- Behavior Analysis: VRU Proximity Risk ---
            vru_risk = vru_proximity_risk(vehicle_detections, infra_detections, location)
            if vru_risk:
                vru_evt = event_builder.dispatch_safety_event(
                    event_type=vru_risk["event_type"],
                    location=location,
                    frame=frame,
                    confidence=vru_risk["confidence"],
                    details=vru_risk["details"],
                )
                if vru_evt:
                    _inc_dispatched()

            # --- Behavior Analysis: Hit-and-Run Candidate Detection ---
            hnr_candidate = check_hit_and_run(track_history)
            if hnr_candidate:
                hnr_evt = event_builder.dispatch_safety_event(
                    event_type=hnr_candidate["event_type"],
                    location=location,
                    frame=frame,
                    confidence=hnr_candidate["confidence"],
                    details=hnr_candidate["details"],
                )
                if hnr_evt:
                    _inc_dispatched()
                    anpr_trigger_frame = frame_idx

            # --- Waterlogging Heuristic (every 5th frame) ---
            if not args.no_waterlog and frame_idx % 5 == 0:
                wl_risk = detect_waterlogging(frame, location)
                if wl_risk:
                    wl_evt = event_builder.dispatch_safety_event(
                        event_type=wl_risk["event_type"],
                        location=location,
                        frame=frame,
                        confidence=wl_risk["confidence"],
                        details=wl_risk["details"],
                    )
                    if wl_evt:
                        _inc_dispatched()

            # --- Draw ALL boxes on preview frame ---
            display_frame = frame.copy()
            for det in all_detections:
                x1, y1, x2, y2 = [int(v) for v in det.bbox]
                color = (0, 200, 0) if det.class_name in ANOMALY_CLASSES else (0, 200, 255)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                label = f"{det.class_name} {det.confidence:.0%}"
                cv2.putText(display_frame, label, (x1, max(y1 - 6, 14)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            for vdet in vehicle_detections:
                vx1, vy1, vx2, vy2 = [int(v) for v in vdet.bbox]
                cv2.rectangle(display_frame, (vx1, vy1), (vx2, vy2), (255, 165, 0), 1)
                vlabel = f"{vdet.class_name} {vdet.confidence:.0%}"
                cv2.putText(display_frame, vlabel, (vx1, max(vy1 - 4, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 165, 0), 1)

            # --- GPS overlay ---
            gps_text = f"GPS: {location.latitude:.5f},{location.longitude:.5f}  Hdg:{location.heading_deg:.0f}\u00b0"
            cv2.putText(display_frame, gps_text, (10, frame_h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
            bus_text = f"{bus.bus_id} | {bus.route_id} | Frame {frame_idx} | Tracks: {tracker.active_track_count}"
            cv2.putText(display_frame, bus_text, (10, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # --- Push to frame_queue for MJPEG streaming ---
            if frame_queue is not None:
                ok, jpeg_buf = cv2.imencode(".jpg", display_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    try:
                        frame_queue.put_nowait(bytes(jpeg_buf))
                    except queue.Full:
                        pass  # drop frame rather than stall pipeline

            # --- Show preview window for CLI usage ---
            if not args.no_preview and frame_queue is None:
                cv2.imshow("SIH26124 Edge Pipeline", display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("[RUNNER] User quit.")
                    break

            frame_idx += 1

        # Flush density for final segment
        if current_segment is not None:
            _flush_density(current_segment, location)

        # --- Flush remaining active tracks at end of stream ---
        eos_tracks = tracker.flush()
        for c_track in eos_tracks:
            stitcher.process_completed_track(c_track, frame_idx + 100)
        final_stitched_tracks = stitcher.flush()

        for c_track in final_stitched_tracks:
            total_completed_tracks += 1
            plates_to_send = list(buffered_plates)
            signs_to_send = list(buffered_signs)
            event = event_builder.process_track(
                completed_track=c_track,
                frame_w=frame_w,
                frame_h=frame_h,
                nearby_plates=plates_to_send,
                nearby_signs=signs_to_send,
            )
            if event is not None:
                _inc_dispatched()
                buffered_plates.clear()
                buffered_signs.clear()

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

        # Benchmark Latencies
        if time_road_ms:
            avg_road = sum(time_road_ms) / len(time_road_ms)
            print(f"[BENCHMARK] Road Anomaly (YOLOv8m): avg {avg_road:.1f} ms/frame ({1000.0/max(avg_road, 0.1):.1f} FPS)")
        if time_vehicle_ms:
            avg_veh = sum(time_vehicle_ms) / len(time_vehicle_ms)
            print(f"[BENCHMARK] Vehicles/VRU (YOLOv8n):  avg {avg_veh:.1f} ms/frame ({1000.0/max(avg_veh, 0.1):.1f} FPS)")
        if time_infra_ms:
            avg_inf = sum(time_infra_ms) / len(time_infra_ms)
            print(f"[BENCHMARK] Traffic Signs (YOLOv8):  avg {avg_inf:.1f} ms/frame ({1000.0/max(avg_inf, 0.1):.1f} FPS)")
        if time_anpr_ms:
            avg_anpr = sum(time_anpr_ms) / len(time_anpr_ms)
            print(f"[BENCHMARK] ANPR Plate+OCR:          avg {avg_anpr:.1f} ms/read ({1000.0/max(avg_anpr, 0.1):.1f} reads/s)")
        print(f"[RUNNER] ================================================\n")


def main() -> None:
    run(build_args())


if __name__ == "__main__":
    main()
