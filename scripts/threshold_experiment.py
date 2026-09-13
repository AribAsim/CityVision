"""
scripts/threshold_experiment.py
Phase 1 Controlled Threshold Experiment using cached detections.
Tests ByteTrack matching thresholds without running YOLO from scratch.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pickle
import numpy as np
from edge.detector import RawDetection
from edge.anomaly_tracker import AnomalyTracker
from edge.gps_simulator import GPSSimulator

CACHE_PATH = "scratch/yolo_detections_cache.pkl"

def run_experiment_on_cache():
    if not Path(CACHE_PATH).exists():
        print(f"Error: {CACHE_PATH} not found!")
        return

    with open(CACHE_PATH, "rb") as f:
        frames_dets = pickle.load(f)

    print(f"Loaded {len(frames_dets)} frames of cached detections.")

    thresholds = [0.8, 0.7, 0.6, 0.5, 0.4]
    results = {}

    for th in thresholds:
        tracker = AnomalyTracker(
            track_activation_threshold=0.30,
            lost_track_buffer=30,
            minimum_matching_threshold=th,
            frame_rate=30,
            min_hits=2,
        )
        gps = GPSSimulator(total_frames=len(frames_dets))
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        completed_tracks = []
        for f_idx, frame_dets in enumerate(frames_dets):
            loc = gps.get_location(f_idx)
            raw_dets = [
                RawDetection(class_name=c, confidence=conf, bbox=bx)
                for c, conf, bx in frame_dets
            ]
            comp = tracker.update(raw_dets, dummy_frame, loc, f_idx)
            completed_tracks.extend(comp)
        
        flush_comp = tracker.flush()
        completed_tracks.extend(flush_comp)

        potholes = [t for t in completed_tracks if t.class_name == "Pothole"]
        cracks = [t for t in completed_tracks if "Crack" in t.class_name]
        results[th] = {
            "total": len(completed_tracks),
            "potholes": len(potholes),
            "cracks": len(cracks),
            "tracks": completed_tracks
        }

    print("\n" + "="*80)
    print("PHASE 1 THRESHOLD EXPERIMENT SUMMARY")
    print("="*80)
    print(f"{'Threshold':<12} | {'Total Tracks':<14} | {'Potholes':<10} | {'Cracks':<10}")
    print("-" * 55)
    for th in thresholds:
        r = results[th]
        print(f"{th:<12.2f} | {r['total']:<14} | {r['potholes']:<10} | {r['cracks']:<10}")
    print("="*80)

    # Detailed Analysis for Key Fragmentation and Separation Cases
    for th in [0.8, 0.6, 0.5, 0.4]:
        print(f"\n--- TRACK LIST FOR THRESHOLD {th} ---")
        p_tracks = sorted([t for t in results[th]["tracks"] if t.class_name == "Pothole"], key=lambda x: x.first_frame_idx)
        for t in p_tracks:
            print(f"  Trk {t.track_id:2d} | F{t.first_frame_idx:3d} -> F{t.last_frame_idx:3d} (hits={t.hit_count:2d}, conf={t.best_confidence:.2f}) | bbox={t.best_bbox}")

if __name__ == "__main__":
    run_experiment_on_cache()
